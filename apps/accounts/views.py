
import logging

from rest_framework import generics, permissions, status
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken,
)
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction

from .models import User, OTPVerification
from .serializers import (
    UserRegistrationSerializer,
    UserDetailSerializer,
    CustomTokenObtainPairSerializer,
)


logger = logging.getLogger(__name__)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate an email verification OTP.
        otp = OTPVerification.create_for_user(
            user,
            OTPVerification.OTPType.EMAIL_VERIFY
        )

        # Send the verification email.
        try:
            send_mail(
                subject='Verify your BorrowCircle account',
                message=(
                    f'Hi {user.username},\n\n'
                    f'Your verification code is: {otp.code}\n\n'
                    'This code expires in 10 minutes.\n\n'
                    'Welcome to BorrowCircle!'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            email_sent = True
        except Exception:
            email_sent = False
            logger.exception(
                'Failed to send registration verification email.'
            )

        message = (
            'Registration successful! Please check your email '
            'for the verification code.'
            if email_sent
            else (
                'Your account was created, but the verification email '
                'could not be sent. Please request a new code.'
            )
        )

        return Response(
            {
                'user': UserDetailSerializer(user).data,
                'email_sent': email_sent,
                'message': message,
            },
            status=status.HTTP_201_CREATED
        )


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'email_verification'

    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')

        if not email or not code:
            return Response(
                {'error': 'Email and OTP code are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not isinstance(code, str) or len(code) != 6 or not code.isdigit():
            return Response(
                {'error': 'Please enter a valid 6-digit code.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                otp = OTPVerification.objects.select_for_update().get(
                    user__email=email,
                    code=code,
                    otp_type=OTPVerification.OTPType.EMAIL_VERIFY,
                    is_used=False,
                )

                if not otp.is_valid():
                    return Response(
                        {'error': 'Invalid or expired code.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                user = otp.user

                if user.is_verified:
                    return Response(
                        {'error': 'Account is already verified.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                otp.is_used = True
                otp.save(update_fields=['is_used'])

                user.is_verified = True
                user.save(update_fields=['is_verified'])

        except OTPVerification.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired code.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                'message': (
                    'Email verified successfully! You can now log in.'
                )
            },
            status=status.HTTP_200_OK
        )


class ResendOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'resend_otp'

    def post(self, request):
        email = request.data.get('email')

        if not email:
            return Response(
                {'error': 'Email is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        generic_response = {
            'message': (
                'If this email belongs to an unverified account, '
                'a new verification code has been sent.'
            )
        }

        user = User.objects.filter(email=email).first()

        if user and not user.is_verified:
            otp = OTPVerification.create_for_user(
                user,
                OTPVerification.OTPType.EMAIL_VERIFY
            )

            try:
                send_mail(
                    subject='Your new BorrowCircle verification code',
                    message=(
                        f'Hi {user.username},\n\n'
                        f'Your new verification code is: {otp.code}\n\n'
                        'This code expires in 10 minutes.'
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception:
                logger.exception(
                    'Failed to send email verification OTP.'
                )

        return Response(
            generic_response,
            status=status.HTTP_200_OK
        )


class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'forgot_password'

    def post(self, request):
        email = request.data.get('email')

        if not email:
            return Response(
                {'error': 'Email is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        generic_response = {
            'message': 'If that email exists, a reset code has been sent.'
        }

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                generic_response,
                status=status.HTTP_200_OK
            )

        otp = OTPVerification.create_for_user(
            user,
            OTPVerification.OTPType.PASSWORD_RESET
        )

        try:
            send_mail(
                subject='Reset your BorrowCircle password',
                message=(
                    f'Hi {user.username},\n\n'
                    f'Your password reset code is: {otp.code}\n\n'
                    'This code expires in 10 minutes.\n\n'
                    'If you did not request this, please ignore this email.'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception:
            # Invalidate the code if email delivery fails.
            otp.is_used = True
            otp.save(update_fields=['is_used'])

            logger.exception(
                'Failed to send password reset email.'
            )

        return Response(
            generic_response,
            status=status.HTTP_200_OK
        )


class VerifyResetCodeView(APIView):
    """
    Verify that a password-reset OTP code is valid without consuming it.
    Returns 200 if valid, 400 if invalid/expired.
    The frontend uses this to gate the 'enter new password' screen.
    """
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'verify_reset_code'

    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')

        if not all([email, code]):
            return Response(
                {'error': 'Email and code are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
            otp = OTPVerification.objects.get(
                user=user,
                code=code,
                otp_type=OTPVerification.OTPType.PASSWORD_RESET,
                is_used=False,
            )
        except (User.DoesNotExist, OTPVerification.DoesNotExist):
            return Response(
                {'error': 'Invalid or expired code.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not otp.is_valid():
            return Response(
                {
                    'error': (
                        'This code has expired. Please request a new one.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {'message': 'Code is valid.'},
            status=status.HTTP_200_OK
        )


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'reset_password'

    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')
        new_password = request.data.get('new_password')

        if not all([email, code, new_password]):
            return Response(
                {
                    'error': (
                        'Email, code, and new password are required.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                user = User.objects.get(email=email)

                otp = OTPVerification.objects.select_for_update().get(
                    user=user,
                    code=code,
                    otp_type=OTPVerification.OTPType.PASSWORD_RESET,
                    is_used=False,
                )

                if not otp.is_valid():
                    return Response(
                        {
                            'error': (
                                'This code has expired. '
                                'Please request a new one.'
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                try:
                    validate_password(new_password, user=user)
                except ValidationError as errors:
                    return Response(
                        {'error': errors.messages},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Update the user's password.
                user.set_password(new_password)
                user.save(update_fields=['password'])

                # Consume the password-reset OTP.
                otp.is_used = True
                otp.save(update_fields=['is_used'])

                # Revoke all outstanding refresh tokens for this user.
                outstanding_tokens = OutstandingToken.objects.filter(
                    user=user
                )

                for outstanding_token in outstanding_tokens:
                    BlacklistedToken.objects.get_or_create(
                        token=outstanding_token
                    )

        except (User.DoesNotExist, OTPVerification.DoesNotExist):
            return Response(
                {'error': 'Invalid or expired code.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                'message': (
                    'Password reset successfully! You can now log in.'
                )
            },
            status=status.HTTP_200_OK
        )


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    throttle_scope = 'login'


class UserDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class LogoutView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)

            # Ensure users can only revoke their own refresh tokens.
            if str(token.get('user_id')) != str(request.user.pk):
                return Response(
                    {'error': 'Invalid refresh token.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            token.blacklist()

        except TokenError:
            return Response(
                {'error': 'Invalid or expired refresh token.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {'detail': 'Successfully logged out.'},
            status=status.HTTP_205_RESET_CONTENT
        )
