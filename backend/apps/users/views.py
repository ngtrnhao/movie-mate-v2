from django.shortcuts import render
from rest_framework import status, generics, serializers
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User, EmailVerificationToken
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer
)
from .services import send_verification_email

# Create your views here.

class RegisterView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Send verification email
        try:
            send_verification_email(user)
        except Exception as e:
            # Log the error but don't fail the registration
            print(f"Failed to send verification email: {e}")

        return Response({
            'message': 'Registration successful. Please check your email to verify your account.',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            }
        }, status=status.HTTP_201_CREATED)

class VerifyEmailView(generics.GenericAPIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        token = request.query_params.get('token')
        try:
            verification = EmailVerificationToken.objects.get(token=token)
            if not verification.is_valid():
                return Response(
                    {"error": "Verification link has expired."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = verification.user
            user.is_email_verified = True
            user.save()

            # Delete the used token
            verification.delete()

            return Response({
                "message": "Email verified successfully. You can now login."
            })
        except EmailVerificationToken.DoesNotExist:
            return Response(
                {"error": "Invalid verification link."},
                status=status.HTTP_400_BAD_REQUEST
            )

class LoginView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            user = User.objects.get(email=serializer.validated_data['email'])

            if not user.is_email_verified:
                return Response(
                    {
                        "error": "Email not verified",
                        "message": "Please verify your email before logging in.",
                        "code": "email_not_verified"
                    },
                    status=status.HTTP_401_UNAUTHORIZED
                )

            if not user.check_password(serializer.validated_data['password']):
                return Response(
                    {
                        "error": "Invalid password",
                        "message": "The password you entered is incorrect.",
                        "code": "invalid_password"
                    },
                    status=status.HTTP_401_UNAUTHORIZED
                )

            refresh = RefreshToken.for_user(user)
            return Response({
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'isEmailVerified': user.is_email_verified,
                },
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })

        except serializers.ValidationError as e:
            return Response(
                {
                    "error": "Validation error",
                    "message": e.detail,
                    "code": "validation_error"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {
                    "error": "Login failed",
                    "message": "An unexpected error occurred. Please try again.",
                    "code": "server_error"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ForgotPasswordView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = ForgotPasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            # TODO: Implement email sending
            return Response(
                {"message": "Password reset email has been sent."},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {"error": "User with this email does not exist."},
                status=status.HTTP_404_NOT_FOUND
            )

class ResetPasswordView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = ResetPasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # TODO: Validate reset token
        # user = get_user_from_token(token)
        # user.set_password(serializer.validated_data['password'])
        # user.save()

        return Response(
            {"message": "Password has been reset successfully."},
            status=status.HTTP_200_OK
        )
