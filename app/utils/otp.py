import random
import string


def generate_otp(length: int = 6) -> str:
    """
    Generates a numeric OTP/invoice id of the given length.
    Used as a short, unique invoice identifier for generated POs.
    """
    return "".join(random.choices(string.digits, k=length))
