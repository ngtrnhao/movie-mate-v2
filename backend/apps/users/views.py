from django.shortcuts import render
from rest_framework import status, generics, serializers, viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User, EmailVerificationToken, Rating, Watchlist, UserFavoriteGenre
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    UserProfileSerializer,
    UserStatsSerializer,
    UserRatingSerializer,
    UserWatchlistSerializer,
    UserFavoriteGenreSerializer,
    GoogleAuthSerializer
)
from .services import send_verification_email
from rest_framework.views import APIView

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

class ProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user

    def get(self, request, *args, **kwargs):
        user_id = kwargs.get('userId')
        try:
            user = User.objects.get(id=user_id)
            serializer = self.get_serializer(user)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    def put(self, request, *args, **kwargs):
        user_id = kwargs.get('userId')
        try:
            user = User.objects.get(id=user_id)
            if user != request.user:
                return Response(
                    {"error": "You can only update your own profile"},
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = self.get_serializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class UploadAvatarView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def put(self, request, *args, **kwargs):
        user_id = kwargs.get('userId')
        try:
            user = User.objects.get(id=user_id)
            if user != request.user:
                return Response(
                    {"error": "You can only update your own avatar"},
                    status=status.HTTP_403_FORBIDDEN
                )

            if 'avatar' not in request.FILES:
                return Response(
                    {"error": "No avatar file provided"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Handle avatar upload logic here
            # You might want to use a storage service like AWS S3
            # For now, we'll just store the URL
            user.avatar_url = request.FILES['avatar'].name
            user.save()

            serializer = self.get_serializer(user)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class UserStatsView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserStatsSerializer

    def get(self, request, *args, **kwargs):
        user_id = kwargs.get('userId')
        try:
            user = User.objects.get(id=user_id)

            # Calculate stats
            stats = {
                'watched_movies_count': Watchlist.objects.filter(user=user, status='WATCHED').count(),
                'reviews_count': Rating.objects.filter(user=user).count(),
                'ratings_count': Rating.objects.filter(user=user).count(),
                'followers_count': 0,  # Implement if you have followers functionality
                'following_count': 0,  # Implement if you have following functionality
            }

            serializer = self.get_serializer(stats)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class UserReviewsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserRatingSerializer

    def get_queryset(self):
        user_id = self.kwargs.get('userId')
        return Rating.objects.filter(user_id=user_id).select_related('movie')

class UserRatingsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserRatingSerializer

    def get_queryset(self):
        user_id = self.kwargs.get('userId')
        return Rating.objects.filter(user_id=user_id).select_related('movie')

class UserFavoriteGenresView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserFavoriteGenreSerializer

    def get_queryset(self):
        user_id = self.kwargs.get('userId')
        return UserFavoriteGenre.objects.filter(user_id=user_id).select_related('genre')

class GoogleAuthView(APIView):
    permission_classes = []  # Allow unauthenticated access

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)

            return Response({
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'avatar_url': user.avatar_url
                }
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.all()

    def get_permissions(self):
        if self.action in ['create', 'list']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_object(self):
        return self.request.user

class UserRatingViewSet(viewsets.ModelViewSet):
    serializer_class = UserRatingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Rating.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class UserWatchlistViewSet(viewsets.ModelViewSet):
    serializer_class = UserWatchlistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Watchlist.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class UserFavoriteGenreViewSet(viewsets.ModelViewSet):
    serializer_class = UserFavoriteGenreSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserFavoriteGenre.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
