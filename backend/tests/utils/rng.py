import random
import string

from pydantic import EmailStr


def generate_str(seed: int | None = None, k: int = 16) -> str:
    """## Generate random lowercase string of length `k`
    Using the same `seed` gives the same random string.
    """
    rng = random.Random(seed)
    return "".join(rng.choices(string.ascii_lowercase, k=k))


def generate_email(seed: int | None = None, domain="com") -> EmailStr:
    """## Generate a random email-formatted string.
    Using the same `seed` gives the same random email.
    """
    return f"{generate_str(seed)}@{generate_str(seed)}.{domain}"
