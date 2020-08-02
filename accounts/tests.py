from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from django.urls import reverse
from unittest import mock
from accounts.models import Event
from accounts import views
from datetime import datetime


class ModelTest(TestCase):
    def test_event_creation(self):
        user = User.objects.create(username='user', email='mail', password='password')
        dt = datetime.utcnow()
        model = Event.objects.create(
            title='event',
            description='desc',
            date=dt,
            creator=user
        )
        self.assertTrue(isinstance(model, Event))
        self.assertEqual('event', model.title)
        self.assertEqual('desc', model.description)
        self.assertEqual(dt, model.date)
        self.assertEqual(user, model.creator)


class LoggedInTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(
            username='user', email='mail'
        )
        self.user.set_password('p')
        self.user.save()

        self.user2 = User.objects.create(
            username='user2', email='mail2'
        )
        self.user2.set_password('p')
        self.user2.save()

        self.client.login(username='user', password='p')

    def _create_event(self):
        self.event_data = {
            'title': 'title',
            'description': 'desc',
            'date': '07/30/2020 19:30'
        }
        response = self.client.post(reverse('create_event'), self.event_data)
        return response, Event.objects.all()[0]


    def _log_in_as_another_user(self, username):
        self.client.logout()
        self.client.login(username=username, password='p')


class EventCreateTest(LoggedInTest):
    def test_event_view_get(self):
        response = self.client.get(reverse('create_event'))
        self.assertEqual(200, response.status_code)
        self.assertIn(b'Event data', response.content)

    def test_event_view_post(self):
        events = Event.objects.all()
        self.assertEqual(0, len(events))
        response, _ = self._create_event()
        self.assertEqual(302, response.status_code)
        self.assertEqual('/events/all', response.url)
        events = Event.objects.all()
        self.assertEqual(1, len(events))
        self.assertEqual(self.event_data['title'], events[0].title)
        self.assertEqual(self.event_data['description'], events[0].description)
        self.assertEqual(self.user.id, events[0].creator.id)


class EventEditTest(LoggedInTest):
    def test_get_404(self):
        response = self.client.get(reverse('edit_event', args=[9001]))
        self.assertEquals(404, response.status_code)

    def test_get_permissions(self):
        _, event = self._create_event()
        response = self.client.get(reverse('edit_event', args=[event.id]))
        self.assertEquals(200, response.status_code)
        self._log_in_as_another_user('user2')
        response = self.client.get(reverse('edit_event', args=[event.id]))
        self.assertEquals(403, response.status_code)

    def test_event_edit_view_get(self):
        _, event = self._create_event()
        response = self.client.get(reverse('edit_event', args=[event.id]))
        self.assertEquals(200, response.status_code)
        self.assertIn(b'Event data', response.content)

    def test_post_permissions(self):
        _, event = self._create_event()
        self.event_data['description'] = 'new description'
        response = self.client.post(
            reverse('edit_event', args=[event.id]),
            self.event_data
        )
        self.assertEquals(302, response.status_code)
        self._log_in_as_another_user('user2')
        response = self.client.get(reverse('edit_event', args=[event.id]))
        self.assertEquals(403, response.status_code)

    def test_event_edit_view_post(self):
        _, event = self._create_event()
        self.event_data['description'] = 'new description'
        response = self.client.post(
            reverse('edit_event', args=[event.id]),
            self.event_data
        )
        self.assertEquals(302, response.status_code)
        events = Event.objects.all()
        self.assertEqual(1, len(events))
        self.assertEqual('new description', events[0].description)


class AllEventsTest(LoggedInTest):
    @mock.patch('accounts.views._get_redis_client')
    def test_all_events(self, _):
        with mock.patch('accounts.views.Event') as e:
            response = self.client.get(reverse('home'))
            self.assertEquals(200, response.status_code)
            e.assert_not_called()

    @mock.patch('accounts.views._get_redis_client')
    def test_get_all_events_fallback(self, client):
        with mock.patch('accounts.views.Event') as e:
            client.side_effect = Exception('oh no')
            self.client.get(reverse('home'))
            e.objects.all().select_related.assert_called_once_with('creator')


class SignUpTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(
            username='user', email='mail'
        )
        self.user.set_password('p')
        self.user.save()

    def test_sign_up_get(self):
        response = self.client.get(reverse('sign_up'))
        self.assertEqual(200, response.status_code)
        self.assertIn(b'Create a new Account', response.content)

    def test_sign_up_post(self):
        login_data = {
            'username': 'user3',
            'email': 'me@myself.com',
            'password1': 'sherpany',
            'password2': 'sherpany',
        }
        response = self.client.post(reverse('sign_up'), login_data)
        self.assertEqual(302, response.status_code)
        self.assertEqual('/events/all', response.url)


class EventJoinWithdraw(LoggedInTest):
    def test_get_404_join(self):
        response = self.client.get(reverse('join_event', args=[9001]))
        self.assertEquals(404, response.status_code)

    def test_get_404_withdraw(self):
        response = self.client.get(reverse('withdraw_event', args=[9001]))
        self.assertEquals(404, response.status_code)

    def test_join_event(self):
        _, event = self._create_event()
        self.assertEqual(0, len(event.users.values()))
        self.client.post(reverse('join_event', args=[event.id]))
        event = Event.objects.all()[0]
        self.assertEqual(1, len(event.users.values()))

    def test_withdraw_event(self):
        _, event = self._create_event()
        self.assertEqual(0, len(event.users.values()))
        self.client.post(reverse('join_event', args=[event.id]))
        event = Event.objects.all()[0]
        self.assertEqual(1, len(event.users.values()))
        self.client.post(reverse('withdraw_event', args=[event.id]))
        event = Event.objects.all()[0]
        self.assertEqual(0, len(event.users.values()))