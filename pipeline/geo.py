"""Geometry the lightship stations need (DESIGN.md 3.5): where a vessel moored "about 6 1/2 miles SE. 1/2 E. from
Cape Hatteras Light-House" lay, worked out from the light's own position.

- `destination` / `bearing_between` / `distance_nm`: great-circle sums on a sphere of mean radius (error well under
  0.5 % at the distances of a mooring, 1 to 30 nautical miles; a position is `approximate` anyway).
- `compass_degrees`: the thirty-two points of the old compass as the Light List and the Lighthouse Board wrote them
  ("SE. 1/2 E.", "N. by W. 3/4 W.", "ESE.") to degrees.
- `declination`: the magnetic declination of the IGRF-14 model (International Geomagnetic Reference Field; the
  coefficients are IAGA's, `data/reference/igrf14coeffs.txt`, valid 1900 onward), pure Python. The Light Lists of
  the Light-House Board say "Bearings and courses given are magnetic"; a compass bearing is turned to a true one by
  adding the declination (east positive) of the place and year. IGRF-1900 is good to a degree or two in the United
  States, which at 15 nautical miles is half a mile.

Python 3.12, standard library only.
"""
from __future__ import annotations

import functools
import math
import re
from pathlib import Path

EARTH_RADIUS_NM = 3440.065          # 6371.0088 km / 1.852
COEFFS = Path(__file__).resolve().parent.parent / "data" / "reference" / "igrf14coeffs.txt"


def destination(lat: float, lon: float, bearing_deg: float, dist_nm: float) -> tuple[float, float]:
    """The point `dist_nm` nautical miles from (lat, lon) on a true bearing (degrees clockwise from north)."""
    phi1, lam1, brg = math.radians(lat), math.radians(lon), math.radians(bearing_deg)
    d = dist_nm / EARTH_RADIUS_NM
    phi2 = math.asin(math.sin(phi1) * math.cos(d) + math.cos(phi1) * math.sin(d) * math.cos(brg))
    lam2 = lam1 + math.atan2(math.sin(brg) * math.sin(d) * math.cos(phi1), math.cos(d) - math.sin(phi1) * math.sin(phi2))
    return math.degrees(phi2), (math.degrees(lam2) + 540) % 360 - 180


def distance_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dlam = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlam / 2) ** 2
    return 2 * EARTH_RADIUS_NM * math.asin(min(1.0, math.sqrt(a)))


def bearing_between(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """The initial true bearing from point 1 to point 2, degrees in [0, 360)."""
    p1, p2, dl = math.radians(lat1), math.radians(lat2), math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


# ---------------------------------------------------------------------------------------------
# The old compass
# ---------------------------------------------------------------------------------------------

POINTS = {"N": 0.0, "NNE": 22.5, "NE": 45.0, "ENE": 67.5, "E": 90.0, "ESE": 112.5, "SE": 135.0, "SSE": 157.5, "S": 180.0,
          "SSW": 202.5, "SW": 225.0, "WSW": 247.5, "W": 270.0, "WNW": 292.5, "NW": 315.0, "NNW": 337.5}
CARDINAL = {"N": 0.0, "E": 90.0, "S": 180.0, "W": 270.0}
POINT = 11.25                       # one point of the compass, in degrees
VULGAR = {"\u00bc": 0.25, "\u00bd": 0.5, "\u00be": 0.75, "\u215b": 0.125, "\u215c": 0.375, "\u215d": 0.625, "\u215e": 0.875}


def _toward(base: float, target: float, points: float) -> float:
    """`base` turned by `points` compass points the short way toward `target`."""
    diff = (target - base + 540) % 360 - 180
    return (base + math.copysign(points * POINT, diff)) % 360


def _fraction(tok: str) -> float:
    if tok in VULGAR:
        return VULGAR[tok]
    num, den = tok.split("/")
    return int(num) / int(den)


COMPASS_RE = re.compile(
    r"(N|NNE|NE|ENE|E|ESE|SE|SSE|S|SSW|SW|WSW|W|WNW|NW|NNW)"       # the point
    r"(?: BY (N|E|S|W))?"                                            # "by" a cardinal: one point toward it
    r"(?: ((?:[1-7]/[248])|[\u00bc\u00bd\u00be\u215b\u215c\u215d\u215e]) (N|NE|E|SE|S|SW|W|NW))?")  # a fraction of a point toward a direction


def compass_degrees(text: str) -> float:
    """"SE. 1/2 E." -> 129.375; "N. by W." -> 348.75; "ESE." -> 112.5; "NW. 3/4 N." -> 323.4375;
    "SE. by E. 1/4 E." -> 120.9375 (one point and a quarter from SE toward E); "due east" -> 90.

    Accepted: a point (N, NE, ESE ...), then "by" and a cardinal letter (one point toward it) and/or a fraction of a point
    (1/8 ... 7/8, also the vulgar-fraction characters) with the direction it leans toward. Anything else raises
    ValueError, so a description that cannot be read is never turned into a number."""
    t = text.strip().strip(".,;").replace("\u00b0", "")
    if re.fullmatch(r"(?i)due\s+(north|east|south|west)", t):
        return CARDINAL[t.split()[-1][0].upper()]
    t = re.sub(r"\s+", " ", re.sub(r"\.", " ", t)).strip().upper()
    m = COMPASS_RE.fullmatch(t)
    if not m:
        raise ValueError(f"not a compass bearing: {text!r}")
    base = POINTS[m.group(1)]
    if m.group(2):
        base = _toward(base, CARDINAL[m.group(2)], 1.0)
    if m.group(3):
        # the fraction leans toward the named direction, from the bearing so far
        base = _toward(base, POINTS[m.group(4)], _fraction(m.group(3)))
    return base


# ---------------------------------------------------------------------------------------------
# Magnetic declination (IGRF-14)
# ---------------------------------------------------------------------------------------------

@functools.lru_cache(maxsize=1)
def _coefficients() -> tuple[list[float], dict[str, list[float]]]:
    epochs: list[float] = []
    rows: dict[str, list[float]] = {}
    for line in COEFFS.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if parts[:1] == ["g/h"]:
            epochs = [float(x) for x in parts[3:-1]]        # 1900.0 ... 2025.0; the last word names the secular variation
        elif parts[:1] in (["g"], ["h"]):
            rows[f"{parts[0]}{parts[1]},{parts[2]}"] = [float(x) for x in parts[3:]]
    return epochs, rows


def _gh(year: float) -> tuple[dict[tuple[int, int], float], dict[tuple[int, int], float], int]:
    epochs, rows = _coefficients()
    if not epochs[0] <= year <= epochs[-1] + 5:
        raise ValueError(f"IGRF-14 here covers {epochs[0]:.0f} to {epochs[-1] + 5:.0f}, not {year}")
    g: dict[tuple[int, int], float] = {}
    h: dict[tuple[int, int], float] = {}
    nmax = 10 if year < 2000 else 13
    for key, vals in rows.items():
        kind, nm = key[0], key[1:].split(",")
        n, m = int(nm[0]), int(nm[1])
        if n > nmax:
            continue
        if year >= epochs[-1]:
            v = vals[len(epochs) - 1] + (year - epochs[-1]) * vals[len(epochs)]      # last epoch + secular variation
        else:
            i = min(int((year - epochs[0]) // 5), len(epochs) - 2)
            w = (year - epochs[i]) / (epochs[i + 1] - epochs[i])
            v = vals[i] * (1 - w) + vals[i + 1] * w
        (g if kind == "g" else h)[(n, m)] = v
    return g, h, nmax


def declination(lat: float, lon: float, year: float) -> float:
    """Magnetic declination in degrees (east positive) at a place on the Earth's surface, IGRF-14, for 1900 on."""
    g, h, nmax = _gh(year)
    a_ref, a, b = 6371.2, 6378.137, 6356.7523142
    phi = math.radians(lat)
    lat_c = math.atan2(b * b * math.tan(phi), a * a)
    r = math.sqrt((a ** 4 * math.cos(phi) ** 2 + b ** 4 * math.sin(phi) ** 2) / (a * a * math.cos(phi) ** 2 + b * b * math.sin(phi) ** 2))
    theta = math.pi / 2 - lat_c
    st, ct = math.sin(theta), math.cos(theta)
    lam = math.radians(lon)
    # Schmidt semi-normalised associated Legendre functions and their theta-derivatives
    P = {(0, 0): 1.0}
    dP = {(0, 0): 0.0}
    for n in range(1, nmax + 1):
        for m in range(0, n + 1):
            if n == m:
                if n == 1:
                    P[(1, 1)], dP[(1, 1)] = st, ct
                else:
                    k = math.sqrt((2 * n - 1) / (2 * n))
                    P[(n, n)] = k * st * P[(n - 1, n - 1)]
                    dP[(n, n)] = k * (ct * P[(n - 1, n - 1)] + st * dP[(n - 1, n - 1)])
            else:
                k1 = (2 * n - 1) / math.sqrt(n * n - m * m)
                p2 = P.get((n - 2, m), 0.0)
                d2 = dP.get((n - 2, m), 0.0)
                k2 = math.sqrt(((n - 1) ** 2 - m * m) / (n * n - m * m)) if n - 1 >= m else 0.0
                P[(n, m)] = k1 * ct * P[(n - 1, m)] - k2 * p2
                dP[(n, m)] = k1 * (-st * P[(n - 1, m)] + ct * dP[(n - 1, m)]) - k2 * d2
    br = bt = bp = 0.0
    for n in range(1, nmax + 1):
        f = (a_ref / r) ** (n + 2)
        for m in range(0, n + 1):
            gn, hn = g.get((n, m), 0.0), h.get((n, m), 0.0)
            c_, s_ = math.cos(m * lam), math.sin(m * lam)
            br += (n + 1) * f * (gn * c_ + hn * s_) * P[(n, m)]
            bt -= f * (gn * c_ + hn * s_) * dP[(n, m)]
            bp -= f * m * (-gn * s_ + hn * c_) * P[(n, m)] / st if st > 1e-9 else 0.0
    x_c, y_c, z_c = -bt, bp, -br          # north, east, down in the geocentric frame
    psi = phi - lat_c
    x = x_c * math.cos(psi) + z_c * math.sin(psi)
    return math.degrees(math.atan2(y_c, x))


def true_bearing(magnetic_deg: float, lat: float, lon: float, year: float) -> float:
    """A magnetic bearing taken at (lat, lon) in `year`, as a true one."""
    return (magnetic_deg + declination(lat, lon, year)) % 360
