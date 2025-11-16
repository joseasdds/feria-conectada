# users/views_auth.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from users.serializers import UserSerializer


class RegisterView(APIView):
    """
    POST /api/v1/auth/register/
    Crea un nuevo usuario y retorna tokens JWT.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                "status": "success",
                "message": "Usuario registrado correctamente.",
                "data": {
                    "user": UserSerializer(user).data,
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": "error",
            "message": "Error en el registro.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    POST /api/v1/auth/login/
    Autentica usuario y retorna tokens JWT.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        
        if not email or not password:
            return Response({
                "status": "error",
                "message": "Email y password son requeridos."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(request, email=email, password=password)
        
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                "status": "success",
                "message": "Login exitoso.",
                "data": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }
            }, status=status.HTTP_200_OK)
        
        return Response({
            "status": "error",
            "message": "Credenciales inválidas."
        }, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/
    Invalida el refresh token (blacklist).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({
                    "status": "error",
                    "message": "Refresh token es requerido."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response({
                "status": "success",
                "message": "Logout exitoso."
            }, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({
                "status": "error",
                "message": "Token inválido o ya expirado."
            }, status=status.HTTP_400_BAD_REQUEST)