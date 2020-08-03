from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from django.urls import reverse
from unittest import mock
from events_users.models import Event
from datetime import datetime


class ModelTest(TestCase):
    def test_event_creation(self):
        """Ensure the model is created the way we want"""
        user = User.objects.create(
            username='user',
            email='mail',
            password='password'
        )
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
        """Create a couple of users and log in as one of them"""
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
        """Create an event and return its response and model object"""
        self.event_data = {
            'title': 'title',
            'description': 'desc',
            'date': '07/30/2020 19:30'
        }
        response = self.client.post(reverse('create_event'), self.event_data)
        return response, Event.objects.all()[0]

    def _log_in_as_another_user(self):
        """Log in as the other created user"""
        self.client.logout()
        self.client.login(username='user2', password='p')


class EventCreateTest(LoggedInTest):
    def test_event_view_get(self):
        """Check the form is displayed properly"""
        response = self.client.get(reverse('create_event'))
        self.assertEqual(200, response.status_code)
        self.assertIn(b'Event data', response.content)

    def test_event_view_post(self):
        """Check the event gets created and the user is redirected"""
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
        """Check a non-existing event returns 404"""
        response = self.client.get(reverse('edit_event', args=[9001]))
        self.assertEquals(404, response.status_code)

    def test_get_permissions(self):
        """Check only the event creator can see the form to edit it"""
        _, event = self._create_event()
        response = self.client.get(reverse('edit_event', args=[event.id]))
        self.assertEquals(200, response.status_code)
        self._log_in_as_another_user()
        response = self.client.get(reverse('edit_event', args=[event.id]))
        self.assertEquals(403, response.status_code)

    def test_event_edit_view_get(self):
        """Check event edition works"""
        _, event = self._create_event()
        response = self.client.get(reverse('edit_event', args=[event.id]))
        self.assertEquals(200, response.status_code)
        self.assertIn(b'Event data', response.content)

    def test_post_permissions(self):
        """Check only the event creator can submit the form to edit it"""
        _, event = self._create_event()
        self.event_data['description'] = 'new description'
        response = self.client.post(
            reverse('edit_event', args=[event.id]),
            self.event_data
        )
        self.assertEquals(302, response.status_code)
        self._log_in_as_another_user()
        response = self.client.get(reverse('edit_event', args=[event.id]))
        self.assertEquals(403, response.status_code)

    def test_event_edit_view_post(self):
        """Check event edition POST request works"""
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
    @mock.patch('events_users.views._get_redis_client')
    def test_all_events(self, _):
        """Check the event list page is displayed correctly"""
        with mock.patch('events_users.views.Event') as e:
            response = self.client.get(reverse('home'))
            self.assertEquals(200, response.status_code)
            e.assert_not_called()

    @mock.patch('events_users.views._get_redis_client')
    def test_get_all_events_fallback(self, client):
        """Check Postgres is used if Redis is not available"""
        with mock.patch('events_users.views.Event') as e:
            client.side_effect = Exception('oh no')
            self.client.get(reverse('home'))
            e.objects.all().select_related.assert_called_once_with('creator')


class SignUpTest(TestCase):
    def setUp(self):
        """Create a new user"""
        self.client = Client()
        self.user = User.objects.create(
            username='user', email='mail'
        )
        self.user.set_password('p')
        self.user.save()

    def test_sign_up_get(self):
        """Check that the form to sign up is returned correctly"""
        response = self.client.get(reverse('sign_up'))
        self.assertEqual(200, response.status_code)
        self.assertIn(b'Create a new Account', response.content)

    def test_sign_up_post(self):
        """Check that a user can be registered correctly"""
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
        """Check that joining a non-existing event won't work"""
        response = self.client.get(reverse('join_event', args=[9001]))
        self.assertEquals(404, response.status_code)

    def test_get_404_withdraw(self):
        """Check that withdrawing from a non-existing event won't work"""
        response = self.client.get(reverse('withdraw_event', args=[9001]))
        self.assertEquals(404, response.status_code)

    def test_join_event(self):
        """Check that joining an event works well"""
        _, event = self._create_event()
        self.assertEqual(0, len(event.users.values()))
        self.client.post(reverse('join_event', args=[event.id]))
        event = Event.objects.all()[0]
        self.assertEqual(1, len(event.users.values()))

    def test_withdraw_event(self):
        """Check that withdrawing from an event works well"""
        _, event = self._create_event()
        self.assertEqual(0, len(event.users.values()))
        self.client.post(reverse('join_event', args=[event.id]))
        event = Event.objects.all()[0]
        self.assertEqual(1, len(event.users.values()))
        self.client.post(reverse('withdraw_event', args=[event.id]))
        event = Event.objects.all()[0]
        self.assertEqual(0, len(event.users.values()))