from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Profile

User = get_user_model()


class AuthTests(TestCase):
    def test_register_creates_user_and_profile(self):
        response = self.client.post(
            reverse('register'),
            {
                'email': 'Test@Example.com',
                'password': 'secret1',
                'confirm_password': 'secret1',
            },
        )

        self.assertRedirects(response, reverse('login') + '?registered=true')
        user = User.objects.get()
        self.assertEqual(user.username, 'test@example.com')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_register_rejects_duplicate_email(self):
        User.objects.create_user(
            username='taken@example.com',
            email='taken@example.com',
            password='secret1',
        )

        response = self.client.post(
            reverse('register'),
            {
                'email': 'taken@example.com',
                'password': 'secret1',
                'confirm_password': 'secret1',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'existe déjà')
        self.assertEqual(User.objects.count(), 1)

    def test_register_rejects_mismatched_passwords(self):
        response = self.client.post(
            reverse('register'),
            {
                'email': 'new@example.com',
                'password': 'secret1',
                'confirm_password': 'different',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Les mots de passe ne correspondent pas')
        self.assertEqual(User.objects.count(), 0)

    def test_login_redirects_to_setup(self):
        User.objects.create_user(
            username='login@example.com',
            email='login@example.com',
            password='secret1',
        )

        response = self.client.post(
            reverse('login'),
            {'email': 'LOGIN@example.com', 'password': 'secret1'},
        )

        self.assertRedirects(response, reverse('setup'))
        self.assertEqual(int(self.client.session['_auth_user_id']), User.objects.get().id)

    def test_login_rejects_bad_password(self):
        User.objects.create_user(
            username='login@example.com',
            email='login@example.com',
            password='secret1',
        )

        response = self.client.post(
            reverse('login'),
            {'email': 'login@example.com', 'password': 'wrong'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'E-mail ou mot de passe incorrect')

    def test_protected_page_redirects_anonymous_user(self):
        response = self.client.get(reverse('setup'))
        self.assertRedirects(response, reverse('login') + '?next=/setup/')

    def test_logout_requires_post_and_redirects(self):
        user = User.objects.create_user(
            username='logout@example.com',
            email='logout@example.com',
            password='secret1',
        )
        self.client.force_login(user)

        response = self.client.post(reverse('logout'))

        self.assertRedirects(response, reverse('login'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_account_page_shows_details_without_plan(self):
        user = User.objects.create_user(
            username='account@example.com',
            email='account@example.com',
            password='secret1',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('account'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'account@example.com')
        self.assertNotContains(response, 'Current plan')
        self.assertNotContains(response, 'Sessions used')
        self.assertNotContains(response, 'Upgrades and billing')
