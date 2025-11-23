# users/tests/test_serializers_profiles.py
from django.test import TestCase

from users.serializers_profiles import FerianteProfileSerializer
from users.utils import generate_random_rut


class FerianteProfileSerializerTestCase(TestCase):
    def test_serializer_normalizes_rut_and_validates(self):
        rut = generate_random_rut(8, with_hyphen=True)  # ej. 73305012-8
        data = {"rut": rut, "direccion": "Calle de prueba 1234"}
        s = FerianteProfileSerializer(data=data)
        self.assertTrue(s.is_valid(), msg=f"errors: {s.errors}")
        validated = s.validated_data
        # Normalized rut should have no punctuation
        self.assertIn("rut", validated)
        self.assertNotIn(".", validated["rut"])
        self.assertNotIn("-", validated["rut"])

    def test_serializer_rejects_invalid_rut(self):
        data = {"rut": "12.345.678-0", "direccion": "Calle de prueba 1234"}
        s = FerianteProfileSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("rut", s.errors)
