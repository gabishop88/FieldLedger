import math
import random
import string

from pydantic import EmailStr


def generate_str(seed: int | None = None, k: int = 16) -> str:
    """### Generate random lowercase string of length `k`
    Using the same `seed` gives the same random string.
    """
    rng = random.Random(seed)
    return "".join(rng.choices(string.ascii_lowercase, k=k))


def generate_email(seed: int | None = None, domain="com") -> EmailStr:
    """### Generate a random email-formatted string.
    Using the same `seed` gives the same random email.
    """
    return f"{generate_str(seed)}@{generate_str(seed)}.{domain}"


def generate_geom(
    seed: int | None = None, lat=40.045818, lon=-88.223950, r_min=0.01, r_max=0.02
) -> str:
    """### Generate a random convex polygon around the given center.
    It is deterministic based on seed, and contains the area defined by r_min.
    """
    rng = random.Random(seed)
    n = rng.choice(range(4,13))
    base_angles = [2 * math.pi * i / n for i in range(n)]
    jitter = (2 * math.pi / n) * 0.35

    points = []
    for angle in base_angles:
        a = angle + rng.uniform(-jitter, jitter)
        r = rng.uniform(r_min, r_max)
        points.append((lon + r * math.cos(a), lat + r * math.sin(a)))
    points.append(points[0])  # close polygon

    coords = ", ".join(f"{x:.6f} {y:.6f}" for x, y in points)
    return f"MULTIPOLYGON ((({coords})))"
