# users/tests/test_utils_rut.py
from django.test import TestCase

from users.utils import (calculate_dv, generate_random_rut, normalize_rut,
                         split_rut, validate_rut)


class RUTUtilsTestCase(TestCase):
    def test_normalize_and_split(self):
        assert normalize_rut("12.345.678-k") == "12345678K"
        num, dv = split_rut("12.345.678-k")
        self.assertEqual(num, "12345678")
        self.assertEqual(dv, "K")

    def test_calculate_dv_known(self):
        # Example from earlier: for 73305012 DV is 8
        self.assertEqual(calculate_dv(73305012), "8")

    def test_validate_rut_valid(self):
        r = generate_random_rut(8, with_hyphen=False)
        self.assertTrue(validate_rut(r))

    def test_generate_random_rut_with_hyphen(self):
        r = generate_random_rut(8, with_hyphen=True)
        # Should match pattern NNNNNNNN-D
        self.assertRegex(r, r"^\d{7,8}-[\dK]$")
        self.assertTrue(validate_rut(r))
