# users/views_auth.py

from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

# Importar AMBOS serializers: UserSerializer (para lectura) y RegistrationSerializer (para creación)
from users.serializers import RegistrationSerializer, UserSerializer


class RegisterView(APIView):
    """
    POST /api/v1/auth/register/
    Crea un nuevo usuario (usando RegistrationSerializer para asignar el rol por defecto)
    y retorna tokens JWT.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        # CORRECCIÓN CLAVE: Usar RegistrationSerializer para la creación
        serializer = RegistrationSerializer(data=request.data)

        if serializer.is_valid():
            # El método save() del RegistrationSerializer ya incluye la asignación del rol 'cliente'
            # y dispara la signal para crear el ClienteProfile.
            user = serializer.save()

            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "status": "success",
                    "message": "Usuario registrado correctamente.",
                    "data": {
                        # Usar UserSerializer para serializar la respuesta (lectura, incluye perfil anidado)
                        "user": UserSerializer(user).data,
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {
                "status": "error",
                "message": "Error en el registro.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


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
            return Response(
                {"status": "error", "message": "Email y password son requeridos."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Django's authenticate usa el Manager del modelo (ej: authenticate(..., email=email))
        user = authenticate(request, email=email, password=password)

        if user:
            # Aquí podrías verificar si el usuario está activo, si tiene perfil, etc.
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "status": "success",
                    "message": "Login exitoso.",
                    "data": {
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                    },
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"status": "error", "message": "Credenciales inválidas."},
            status=status.HTTP_401_UNAUTHORIZED,
        )


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
                return Response(
                    {"status": "error", "message": "Refresh token es requerido."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {"status": "success", "message": "Logout exitoso."},
                status=status.HTTP_205_RESET_CONTENT,
            )
        except Exception as e:
            # Captura errores si el token es inválido, está mal formateado o ya está en blacklist
            return Response(
                {"status": "error", "message": "Token inválido o ya expirado."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class MeView(APIView):
    """
    GET /api/v1/me/
    Retorna los datos del usuario autenticado, incluyendo su perfil anidado.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Usamos el UserSerializer (el que incluye el SerializerMethodField 'profile')
        serializer = UserSerializer(request.user)

        return Response(
            {"status": "success", "data": serializer.data}, status=status.HTTP_200_OK
        )
