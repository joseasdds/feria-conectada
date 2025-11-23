# users/utils.py
import random
import re
from typing import Optional, Tuple


def calculate_dv(rut_number: int) -> str:
    """
    Calcula el dígito verificador (DV) del RUT chileno (módulo 11).
    """
    total = 0
    factor = 2
    for d in reversed(str(rut_number)):
        total += int(d) * factor
        factor += 1
        if factor > 7:
            factor = 2
    remainder = 11 - (total % 11)
    if remainder == 11:
        return "0"
    if remainder == 10:
        return "K"
    return str(remainder)


def normalize_rut(rut: str) -> str:
    """
    Normaliza el RUT: quita puntos y guion, y pone DV en mayúscula.
    Ej: '12.345.678-k' -> '12345678K'
    """
    if rut is None:
        return ""
    cleaned = re.sub(r"[^0-9Kk]", "", rut)
    return cleaned.upper()


def split_rut(rut: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Separa un RUT en (numero_sin_formato, dv).
    """
    if not rut:
        return None, None
    r = normalize_rut(rut)
    if len(r) < 2:
        return None, None
    number = r[:-1]
    dv = r[-1]
    if not number.isdigit():
        return None, None
    return number, dv.upper()


def validate_rut(rut: str) -> bool:
    """
    Valida si el RUT tiene DV correcto.
    """
    number, dv = split_rut(rut)
    if not number or not dv:
        return False
    try:
        computed = calculate_dv(int(number))
    except Exception:
        return False
    return computed == dv.upper()


def generate_random_rut(base_digits: int = 8, with_hyphen: bool = False) -> str:
    """
    Genera un RUT aleatorio válido (ej. '123456785' o '12345678-5').
    """
    if base_digits not in (7, 8):
        raise ValueError("base_digits debe ser 7 u 8")
    start = 10 ** (base_digits - 1)
    end = 10**base_digits - 1
    num = random.randint(start, end)
    dv = calculate_dv(num)
    if with_hyphen:
        return f"{num}-{dv}"
    return f"{num}{dv}"
