import logging
import os
from decimal import Decimal

import requests

logger = logging.getLogger(__name__)

# --- Clase de Servicio para la Geolocalización (Tarea 43) ---


class GeolocatorService:
    """
    Servicio encargado de interactuar con APIs de mapas (Google Maps, OSRM, etc.)
    para obtener distancias, tiempos de viaje y geocodificación.
    """

    # URL de la API de Distancia/Rutas (Simulación o Google Maps)
    # En producción, usarías os.getenv("GOOGLE_MAPS_API_KEY")
    API_KEY = os.getenv("MAPS_API_KEY", "YOUR_API_KEY_HERE")
    BASE_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"

    # Definimos las coordenadas del centro de Santiago para simulación
    # (El punto de recolección de pedidos)
    FERIA_ORIGEN_COORD = "-33.4489,-70.6693"  # Simulación: Santiago, Chile

    # -----------------------------------------------------------
    # Funciones de Soporte
    # -----------------------------------------------------------

    @staticmethod
    def _parse_location(location: str) -> str:
        """
        Garantiza que la ubicación esté en formato de coordenadas (lat,lng)
        o un string de dirección limpio para la API.
        Aquí se podría integrar un geocodificador, pero lo simulamos.
        """
        # Si la ubicación es una dirección (e.g., "Av. Providencia 1000")
        # Simplemente la devolvemos URL-safe.
        return location

    # -----------------------------------------------------------
    # Lógica Central
    # -----------------------------------------------------------

    def calculate_delivery_route(
        self, origin: str, destination: str, mode: str = "driving"
    ) -> dict:
        """
        Calcula el tiempo y la distancia estimada entre el origen y el destino.

        :param origin: Coordenadas o dirección del punto de recolección (Puesto).
        :param destination: Coordenadas o dirección del punto de entrega (Cliente).
        :param mode: Tipo de transporte (driving, walking, bicycling).
        :return: Diccionario con distancia_km y tiempo_seg.
        """
        if not self.API_KEY:
            logger.warning("MAPS_API_KEY no configurada. Usando datos simulados.")
            return self._simulate_route(origin, destination)

        # Simulación de llamada a API (en producción sería una solicitud real)
        try:
            # En una aplicación real, usarías requests.get(self.BASE_URL, params={...})
            # Aquí, solo devolvemos una simulación de respuesta exitosa.

            # Nota: Aquí deberías usar una dirección real del Puesto (Fase 2)
            # y la dirección del Cliente (Fase 1/3)

            return self._simulate_route(origin, destination)

        except requests.RequestException as e:
            logger.error(f"Error en la API de Mapas: {e}")
            return self._simulate_route(origin, destination, is_error=True)

    def _simulate_route(self, origin, destination, is_error=False):
        """
        Genera datos de ruta simulados para desarrollo sin API Key.
        """
        if is_error:
            # Si hubo error de red, devolvemos un valor seguro
            return {"distance_km": Decimal("5.0"), "time_min": 15, "error": "API Error"}

        # Generación de valores aleatorios realistas para simulación
        # Se asume una distancia base entre 2 km y 10 km
        import random

        distance_km = Decimal(random.uniform(2.0, 10.0)).quantize(Decimal("0.01"))

        # El tiempo de entrega se basa en la distancia (ej: 3 min por km + 5 min de preparación)
        time_min = int(distance_km * Decimal("3.5")) + 5

        return {"distance_km": distance_km, "time_min": time_min, "error": None}


# Inicializa el servicio para importarlo en vistas/tasks.py
geolocator_service = GeolocatorService()
