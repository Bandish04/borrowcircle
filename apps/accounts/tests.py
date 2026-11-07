
from unittest.mock import patch
from datetime import timedelta

from django.core import mail
from django.core.cache import cache
from django.test import override_settings
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

from .models import User, Profile, ReliabilitySummary, OTPVerification


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
)
class RegistrationTests(APITestCase):

    url = '/api/v1/auth/register/'

    def test_registration_creates_unverified_user_without_tokens(self):
        response = self.client.post(
            self.url,
            {
                'username': 'testuser',
                'email': 'testuser@example.com',
                'password': 'Violet!Comet#7391-Tree',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(email='testuser@example.com')

        self.assertFalse(user.is_verified)
        self.assertTrue(user.check_password('Violet!Comet#7391-Tree'))

        self.assertNotIn('access', response.data)
        self.assertNotIn('refresh', response.data)

        self.assertTrue(Profile.objects.filter(user=user).exists())
        self.assertTrue(ReliabilitySummary.objects.filter(user=user).exists())

        self.assertEqual(
            OTPVerification.objects.filter(
                user=user,
                otp_type=OTPVerification.OTPType.EMAIL_VERIFY,
                is_used=False,
            ).count(),
            1,
        )

        self.assertTrue(response.data['email_sent'])
        self.assertEqual(len(mail.outbox), 1)

    def test_registration_rejects_short_password(self):
        response = self.client.post(
            self.url,
            {
                'username': 'testuser',
                'email': 'testuser@example.com',
                'password': 'short',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
)
class EmailVerificationTests(APITestCase):

    url = '/api/v1/auth/verify-email/'

    def setUp(self):
        cache.clear()

        self.user = User.objects.create_user(
            email='verify@example.com',
            username='verifyuser',
            password='Violet!Comet#7391-Tree',
        )

        self.otp = OTPVerification.create_for_user(
            self.user,
            OTPVerification.OTPType.EMAIL_VERIFY,
        )

    def test_valid_otp_verifies_email(self):
        response = self.client.post(
            self.url,
            {
                'email': self.user.email,
                'code': self.otp.code,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.otp.refresh_from_db()

        self.assertTrue(self.user.is_verified)
        self.assertTrue(self.otp.is_used)

    def test_used_otp_cannot_be_reused(self):
        self.client.post(
            self.url,
            {
                'email': self.user.email,
                'code': self.otp.code,
            },
            format='json',
        )

        response = self.client.post(
            self.url,
            {
                'email': self.user.email,
                'code': self.otp.code,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_expired_otp_is_rejected(self):
        self.otp.expires_at = timezone.now() - timedelta(minutes=1)
        self.otp.save(update_fields=['expires_at'])

        response = self.client.post(
            self.url,
            {
                'email': self.user.email,
                'code': self.otp.code,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_verified)

    def test_invalid_otp_is_rejected(self):
        response = self.client.post(
            self.url,
            {
                'email': self.user.email,
                'code': '000000',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_verified)

    def test_email_verification_is_rate_limited(self):
        for attempt in range(5):
            response = self.client.post(
                self.url,
                {
                    'email': self.user.email,
                    'code': 'invalid',
                },
                format='json',
            )

            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST,
            )

        response = self.client.post(
            self.url,
            {
                'email': self.user.email,
                'code': 'invalid',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
        )


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
)

class ResendOTPTests(APITestCase):

    url = '/api/v1/auth/resend-otp/'

    def setUp(self):
        cache.clear()

        self.user = User.objects.create_user(
            email='resend@example.com',
            username='resenduser',
            password='Violet!Comet#7391-Tree',
        )

    def test_resend_creates_new_otp_and_invalidates_old_one(self):
        old_otp = OTPVerification.create_for_user(
            self.user,
            OTPVerification.OTPType.EMAIL_VERIFY,
        )

        response = self.client.post(
            self.url,
            {'email': self.user.email},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        old_otp.refresh_from_db()
        self.assertTrue(old_otp.is_used)

        new_otp = OTPVerification.objects.filter(
            user=self.user,
            otp_type=OTPVerification.OTPType.EMAIL_VERIFY,
            is_used=False,
        ).first()

        self.assertIsNotNone(new_otp)
        self.assertNotEqual(old_otp.code, new_otp.code)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(new_otp.code, mail.outbox[0].body)

    def test_resend_unknown_email_returns_generic_response(self):
        response = self.client.post(
            self.url,
            {'email': 'unknown@example.com'},
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data,
            {
                'message': (
                    'If this email belongs to an unverified account, '
                    'a new verification code has been sent.'
                )
            },
        )

        self.assertEqual(len(mail.outbox), 0)

    @patch(
        'apps.accounts.views.send_mail',
        side_effect=Exception('SMTP server unavailable'),
    )
    def test_resend_email_failure_returns_generic_response(
        self,
        mock_send_mail,
    ):
        response = self.client.post(
            self.url,
            {'email': self.user.email},
            format='json',
        )

        unknown_response = self.client.post(
            self.url,
            {'email': 'unknown@example.com'},
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.status_code,
            unknown_response.status_code,
        )
        self.assertEqual(
            response.data,
            unknown_response.data,
        )

        mock_send_mail.assert_called_once()

    def test_resend_otp_is_rate_limited(self):
        for attempt in range(3):
            response = self.client.post(
                self.url,
                {'email': 'unknown@example.com'},
                format='json',
            )

            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
            )

        response = self.client.post(
            self.url,
            {'email': 'unknown@example.com'},
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
        )

class LoginTests(APITestCase):

    url = '/api/v1/auth/login/'

    def setUp(self):
        cache.clear()

        self.password = 'Violet!Comet#7391-Tree'
        self.user = User.objects.create_user(
            email='login@example.com',
            username='loginuser',
            password=self.password,
        )

    def test_unverified_user_cannot_login(self):
        response = self.client.post(
            self.url,
            {
                'email': self.user.email,
                'password': self.password,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn('access', response.data)
        self.assertNotIn('refresh', response.data)

    def test_verified_user_can_login(self):
        self.user.is_verified = True
        self.user.save(update_fields=['is_verified'])

        response = self.client.post(
            self.url,
            {
                'email': self.user.email,
                'password': self.password,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_is_rate_limited(self):
        login_data = {
            'email': self.user.email,
            'password': self.password,
        }

        for attempt in range(10):
            response = self.client.post(
                self.url,
                login_data,
                format='json',
            )

            self.assertEqual(
                response.status_code,
                status.HTTP_401_UNAUTHORIZED,
            )

        response = self.client.post(
            self.url,
            login_data,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
        )

    def test_suspended_user_cannot_login(self):
        self.user.is_verified = True
        self.user.account_status = User.AccountStatus.SUSPENDED
        self.user.save()

        response = self.client.post(
            self.url,
            {
                'email': self.user.email,
                'password': self.password,
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_banned_user_cannot_login(self):
        self.user.is_verified = True
        self.user.account_status = User.AccountStatus.BANNED
        self.user.save()

        response = self.client.post(
            self.url,
            {
                'email': self.user.email,
                'password': self.password,
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
)
class PasswordResetTests(APITestCase):

    reset_url = '/api/v1/auth/reset-password/'

    def setUp(self):
        cache.clear()

        self.user = User.objects.create_user(
            email='reset@example.com',
            username='resetuser',
            password='Violet!Comet#7391-Tree',
        )

        self.otp = OTPVerification.create_for_user(
            self.user,
            OTPVerification.OTPType.PASSWORD_RESET,
        )

    def test_valid_password_reset(self):
        new_password = 'Forest!River#8254-Moon'

        response = self.client.post(
            self.reset_url,
            {
                'email': self.user.email,
                'code': self.otp.code,
                'new_password': new_password,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.otp.refresh_from_db()

        self.assertTrue(self.user.check_password(new_password))
        self.assertTrue(self.otp.is_used)


    def test_password_reset_blacklists_existing_refresh_tokens(self):
        # Create a refresh token before resetting the password.
        refresh_token = RefreshToken.for_user(self.user)

        response = self.client.post(
            self.reset_url,
            {
                'email': self.user.email,
                'code': self.otp.code,
                'new_password': 'Forest!River#8254-Moon',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        # Confirm that the existing refresh token was revoked.
        self.assertTrue(
            BlacklistedToken.objects.filter(
                token__user=self.user,
                token__token=str(refresh_token),
            ).exists()
        )


    def test_short_password_is_rejected(self):
        response = self.client.post(
            self.reset_url,
            {
                'email': self.user.email,
                'code': self.otp.code,
                'new_password': 'short',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.user.refresh_from_db()
        self.otp.refresh_from_db()

        self.assertTrue(self.user.check_password('Violet!Comet#7391-Tree'))
        self.assertFalse(self.otp.is_used)

    def test_common_password_is_rejected(self):
        response = self.client.post(
            self.reset_url,
            {
                'email': self.user.email,
                'code': self.otp.code,
                'new_password': 'password12345',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.user.refresh_from_db()
        self.otp.refresh_from_db()

        self.assertTrue(self.user.check_password('Violet!Comet#7391-Tree'))
        self.assertFalse(self.otp.is_used)

    def test_password_reset_is_rate_limited(self):
        for attempt in range(5):
            response = self.client.post(
                self.reset_url,
                {
                    'email': 'unknown@example.com',
                    'code': '000000',
                    'new_password': 'Forest!River#8254-Moon',
                },
                format='json',
            )

            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST,
            )

        response = self.client.post(
            self.reset_url,
            {
                'email': 'unknown@example.com',
                'code': '000000',
                'new_password': 'Forest!River#8254-Moon',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
        )


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
)
class ForgotPasswordTests(APITestCase):

    url = '/api/v1/auth/forgot-password/'

    def setUp(self):
        cache.clear()

        self.user = User.objects.create_user(
            email='forgot@example.com',
            username='forgotuser',
            password='Violet!Comet#7391-Tree',
        )

    def test_forgot_password_sends_reset_code(self):
        response = self.client.post(
            self.url,
            {'email': self.user.email},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        otp = OTPVerification.objects.get(
            user=self.user,
            otp_type=OTPVerification.OTPType.PASSWORD_RESET,
            is_used=False,
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(otp.code, mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].to, [self.user.email])

    def test_forgot_password_is_rate_limited(self):
        for attempt in range(3):
            response = self.client.post(
                self.url,
                {'email': f'unknown{attempt}@example.com'},
                format='json',
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(
            self.url,
            {'email': 'fourth@example.com'},
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
        )

    def test_unknown_email_returns_generic_response(self):
        response = self.client.post(
            self.url,
            {'email': 'unknown@example.com'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['message'],
            'If that email exists, a reset code has been sent.'
        )

        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(OTPVerification.objects.count(), 0)

    @patch(
        'apps.accounts.views.send_mail',
        side_effect=Exception('SMTP connection failed')
    )
    def test_email_failure_invalidates_reset_code(self, mock_send_mail):
        response = self.client.post(
            self.url,
            {'email': self.user.email},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        otp = OTPVerification.objects.get(
            user=self.user,
            otp_type=OTPVerification.OTPType.PASSWORD_RESET,
        )

        self.assertTrue(otp.is_used)
        mock_send_mail.assert_called_once()

    def test_missing_email_is_rejected(self):
        response = self.client.post(
            self.url,
            {},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class VerifyResetCodeTests(APITestCase):

    url = '/api/v1/auth/verify-reset-code/'

    def setUp(self):
        cache.clear()

        self.user = User.objects.create_user(
            email='verifyreset@example.com',
            username='verifyresetuser',
            password='Violet!Comet#7391-Tree',
        )

        self.otp = OTPVerification.create_for_user(
            self.user,
            OTPVerification.OTPType.PASSWORD_RESET,
        )

    def test_valid_reset_code_is_accepted(self):
        response = self.client.post(
            self.url,
            {
                'email': self.user.email,
                'code': self.otp.code,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Code is valid.')

        self.otp.refresh_from_db()
        self.assertFalse(self.otp.is_used)

    def test_invalid_reset_code_is_rejected(self):
        response = self.client.post(
            self.url,
            {
                'email': self.user.email,
                'code': '000000',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_reset_code_is_rate_limited(self):
        for attempt in range(5):
            response = self.client.post(
                self.url,
                {
                    'email': self.user.email,
                    'code': '000000',
                },
                format='json',
            )

            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST,
            )

        response = self.client.post(
            self.url,
            {
                'email': self.user.email,
                'code': '000000',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
        )


class LogoutTests(APITestCase):

    url = '/api/v1/auth/logout/'

    def setUp(self):
        self.user = User.objects.create_user(
            email='logout@example.com',
            username='logoutuser',
            password='Violet!Comet#7391-Tree',
        )

        self.other_user = User.objects.create_user(
            email='other@example.com',
            username='otheruser',
            password='Violet!Comet#7391-Tree',
        )

        self.client.force_authenticate(user=self.user)

    def test_valid_refresh_token_is_blacklisted(self):
        refresh = RefreshToken.for_user(self.user)

        response = self.client.post(
            self.url,
            {'refresh': str(refresh)},
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_205_RESET_CONTENT,
        )

        self.assertTrue(
            BlacklistedToken.objects.filter(
                token__jti=refresh['jti'],
            ).exists()
        )

    def test_missing_refresh_token_is_rejected(self):
        response = self.client.post(
            self.url,
            {},
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_invalid_refresh_token_is_rejected(self):
        response = self.client.post(
            self.url,
            {'refresh': 'not-a-valid-refresh-token'},
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_user_cannot_blacklist_another_users_token(self):
        refresh = RefreshToken.for_user(self.other_user)

        response = self.client.post(
            self.url,
            {'refresh': str(refresh)},
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertFalse(
            BlacklistedToken.objects.filter(
                token__jti=refresh['jti'],
            ).exists()
        )




class TokenRefreshTests(APITestCase):

    url = '/api/v1/auth/refresh/'

    def setUp(self):
        cache.clear()

        self.user = User.objects.create_user(
            email='refresh@example.com',
            username='refreshuser',
            password='Violet!Comet#7391-Tree',
            is_verified=True,
        )

    def test_refresh_token_rotation_returns_new_tokens(self):
        old_refresh = RefreshToken.for_user(self.user)
        old_jti = old_refresh['jti']

        response = self.client.post(
            self.url,
            {'refresh': str(old_refresh)},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

        self.assertNotEqual(
            response.data['refresh'],
            str(old_refresh),
        )

        self.assertTrue(
            BlacklistedToken.objects.filter(
                token__jti=old_jti,
            ).exists()
        )

    def test_old_refresh_token_cannot_be_reused(self):
        old_refresh = RefreshToken.for_user(self.user)

        first_response = self.client.post(
            self.url,
            {'refresh': str(old_refresh)},
            format='json',
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_200_OK,
        )

        second_response = self.client.post(
            self.url,
            {'refresh': str(old_refresh)},
            format='json',
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_suspended_user_cannot_refresh_token(self):
        self.user.account_status = User.AccountStatus.SUSPENDED
        self.user.save(update_fields=['account_status'])

        refresh = RefreshToken.for_user(self.user)

        response = self.client.post(
            self.url,
            {'refresh': str(refresh)},
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_unverified_user_cannot_refresh_token(self):
        self.user.is_verified = False
        self.user.save(update_fields=['is_verified'])

        refresh = RefreshToken.for_user(self.user)

        response = self.client.post(
            self.url,
            {'refresh': str(refresh)},
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )



class AccountStatusAccessTokenTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='accesscheck@example.com',
            username='accesscheckuser',
            password='Secure!Access#8254-Token',
            is_verified=True,
        )

        # Issue an access token while the account is active.
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_suspended_user_cannot_use_existing_access_token(self):
        # Suspend the account after its access token was issued.
        self.user.account_status = User.AccountStatus.SUSPENDED
        self.user.save(update_fields=['account_status'])

        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}'
        )

        response = self.client.get('/api/v1/auth/me/')

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )


    def test_banned_user_cannot_use_existing_access_token(self):
        self.user.account_status = User.AccountStatus.BANNED
        self.user.save(update_fields=['account_status'])

        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}'
        )

        response = self.client.get('/api/v1/auth/me/')

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_deactivated_user_cannot_use_existing_access_token(self):
        self.user.account_status = User.AccountStatus.DEACTIVATED
        self.user.save(update_fields=['account_status'])

        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}'
        )

        response = self.client.get('/api/v1/auth/me/')

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_unverified_user_cannot_use_existing_access_token(self):
        self.user.is_verified = False
        self.user.save(update_fields=['is_verified'])

        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}'
        )

        response = self.client.get('/api/v1/auth/me/')

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
