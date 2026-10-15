from django.contrib.auth import login, logout
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status, views, permissions
from rest_framework.response import Response
from .serializers import (
    UserSerializer,
    LoginSerializer,
    RegisterSerializer
)
from apps.audit.models import ActivityLog, AuditCategoryChoices

class LoginView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)

        # Log authentication event
        ActivityLog.objects.create(
            user=user,
            user_name=user.name,
            user_role=user.get_approved_roles()[0] if user.get_approved_roles() else 'USER',
            action='USER_LOGIN',
            details=f"Successful session sign-in for {user.email}.",
            category=AuditCategoryChoices.AUTH
        )

        return Response({
            'success': True,
            'message': f"Welcome back, {user.name}!",
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)

class LogoutView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        ActivityLog.objects.create(
            user=user,
            user_name=user.name,
            user_role=user.get_approved_roles()[0] if user.get_approved_roles() else 'USER',
            action='USER_LOGOUT',
            details=f"User {user.email} signed out.",
            category=AuditCategoryChoices.AUTH
        )
        logout(request)
        return Response({
            'success': True,
            'message': 'Successfully logged out.'
        }, status=status.HTTP_200_OK)

class CurrentUserView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response({
            'success': True,
            'user': serializer.data
        }, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'success': True,
            'message': 'Profile updated successfully.',
            'user': serializer.data
        }, status=status.HTTP_200_OK)

class RegisterView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Automatically establish authenticated session upon registration
        login(request, user)

        ActivityLog.objects.create(
            user=user,
            user_name=user.name,
            user_role=user.get_approved_roles()[0] if user.get_approved_roles() else 'USER',
            action='USER_REGISTERED',
            details=f"New account created for {user.email} with roles {user.get_approved_roles()}.",
            category=AuditCategoryChoices.AUTH
        )

        return Response({
            'success': True,
            'message': 'Account registered successfully.',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)

class CSRFTokenView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        token = get_token(request)
        return Response({
            'success': True,
            'csrfToken': token
        }, status=status.HTTP_200_OK)
