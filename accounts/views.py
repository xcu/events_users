from django.shortcuts import render, redirect, get_object_or_404
from django.core import serializers
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.http import HttpResponseForbidden
from accounts.event_form import EventForm
from accounts.user_creation_form import UserCreationFormWithEmail
from accounts.models import Event
from json import loads, dumps
import redis


@method_decorator(login_required, name='dispatch')
class EventView(View):
    def get(self, request):
        """Render form to create an event"""
        context = {}
        form = EventForm(request.POST or None)
        context['form'] = form
        return render(request,'event/create_event.html', context)

    def post(self, request):
        """Send form to create an event"""
        context = {}
        form = EventForm(request.POST or None)
        if form.is_valid():
            _update_form_in_model(request, form, set_creator=True)
            return redirect('home')
        context['form'] = form
        return render(request, 'event/create_event.html', context)


@method_decorator(login_required, name='dispatch')
class EventEditView(View):
    def get(self, request, event_id):
        """Render form to edit an event"""
        obj = get_object_or_404(Event, pk=event_id)
        if request.user.id != obj.creator.id:
            return HttpResponseForbidden()
        form = EventForm(request.POST or None, instance=obj)
        context = {'form': form}
        return render(request,'event/create_event.html', context)

    def post(self, request, event_id):
        """Send form to edit an event"""
        obj = get_object_or_404(Event, pk=event_id)
        if request.user.id != obj.creator.id:
            return HttpResponseForbidden()
        form = EventForm(request.POST or None, instance=obj)
        if form.is_valid():
            _update_form_in_model(request, form)
            return redirect('home')
        context = {'form': form}
        return render(request,'event/create_event.html', context)


def _get_redis_client():
    return redis.Redis(host='cache', port=6379, db=1)


def _get_all_events():
    """Fetch all the events and sort them accordingly.

    Will try to get data from Redis first, and fallback to Postgres
    if anything fails.
    """
    try:
        client = _get_redis_client()
        events = client.hgetall('events')
        events = [loads(e.decode()) for e in events.values()]
        # will sort closer events first
        return sorted(events, key=lambda event: event['fields']['date'])
    except Exception:
        # fallback to Postgres
        events = Event.objects.all().select_related('creator')
        obj_list = loads(serializers.serialize('json', events))
        for obj_dict, obj in zip(obj_list, events):
            obj_dict['fields']['creator_name'] = \
                obj.creator.email.split('@')[0]
        return sorted(obj_list, key=lambda event: event['fields']['date'])


@login_required
def all_events(request):
    """Render page with all the events."""
    events_as_dict = _get_all_events()
    for event in events_as_dict:
        if request.user.id in event['fields']['users']:
            event['fields']['joined'] = True
        else:
            event['fields']['joined'] = False
    context = {"events": events_as_dict, "user": request.user}
    return render(request, 'event/show_events.html', context)


def _update_form_in_model(request, event_form, set_creator=False):
    """Save changes in form to database.

    :param request: request object
    :param event_form: form object with data to be stored
    :param set_creator: if the form is being created the creator FK
    needs to be set as well.
    """
    obj = event_form.save(commit=False)
    _update_model(request, obj, set_creator=set_creator)


def _update_model(request, obj, set_creator=False):
    """Save model in DB.

    Will save it both to Postgres and Redis.
    """
    if set_creator:
        obj.creator = request.user
    obj.save()
    pk = obj.pk
    # django serializer needs a list, so we need to do all this
    # serializer-related back and forth
    obj_dict = loads(serializers.serialize('json', [obj,]))[0]
    if set_creator:
        obj_dict['fields']['creator_name'] = request.user.email.split('@')[0]
    client = _get_redis_client()
    client.hset('events', pk, dumps(obj_dict))


def sign_up(request):
    """Form to create a new user in the system"""
    context = {}
    form = UserCreationFormWithEmail(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    context['form'] = form
    return render(request,'registration/sign_up.html', context)


@login_required
def join_event(request, event_id):
    """Add the logged user to a particular event"""
    obj = get_object_or_404(Event, pk=event_id)
    obj.users.add(request.user)
    _update_model(request, obj)
    return redirect('home')


@login_required
def withdraw_event(request, event_id):
    """Withdraw the logged user from a particular event"""
    obj = get_object_or_404(Event, pk=event_id)
    try:
        obj.users.remove(request.user)
        _update_model(request, obj)
    except TypeError:
        # if the user does not exist in the array, do nothing
        pass
    return redirect('home')
