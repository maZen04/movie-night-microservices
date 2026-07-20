from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import *
from common.response import success_response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework.exceptions import ValidationError
from rest_framework.throttling import AnonRateThrottle
from common.throttles import RegisterThrottle, LoginThrottle


class RegisterView(generics.CreateAPIView):
    serializer_class = UserSerializer
    throttle_classes = [RegisterThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return success_response(
            data=serializer.data,
            message="User registered successfully.",
            status=201
        )


class LoginView(generics.GenericAPIView):
    serializer_class = TokenObtainPairSerializer
    throttle_classes = [LoginThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return success_response(
            data=serializer.validated_data,
            message="logged in successfully.",
            status=200
        )


class RefreshTokenView(generics.GenericAPIView):
    serializer_class = TokenRefreshSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError:
            raise InvalidToken("Refresh token is invalid or expired.")

        return success_response(
            data=serializer.validated_data,
            message="Token refreshed successfully.",
            status=200
        )


class LogoutView(APIView):
    
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({"error": "Refresh token required"}, status=status.HTTP_400_BAD_REQUEST)
            token = RefreshToken(refresh_token)
            token.blacklist()

            return success_response(
                data={},
                message="logged out Successfully.",
                status=204
            )
        
        except TokenError:
            raise ValidationError({
                "refresh": ["Refresh token is required."]
            })
        

class ProfileView(generics.RetrieveUpdateDestroyAPIView):
    
    def get_serializer_class(self):
        if self.request.method in ["PATCH", "PUT"]:
            return UpdateProfileSerializer
        return UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
    
    def perform_update(self, serializer):
        if self.request.data.get('display_name') and self.request.data.get('display_name').strip()!= self.request.user.display_name:
            serializer.save()
        
        elif not self.request.data.get('display_name'):
            raise ValidationError({
                "display_name": ["This field is required."]
            })
        else:
            return Response({"error": "Display name is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    def perform_destroy(self, instance):
        instance.delete()
        return success_response(
            data={},
            message="User deleted successfully.",
            status=204
        )