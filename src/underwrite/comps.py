from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from src.utils import haversine_miles, safe_median


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def compute_comp_stats(conn, listing_id: int, criteria: dict) -> Tuple[Optional[float], int]:
    listing = conn.execute(
        """
        SELECT l.id AS listing_id, l.list_price, l.psf, p.sqft, p.lat, p.lon
        FROM listings l
        JOIN properties p ON p.id = l.property_id
        WHERE l.id = ?
        """,
        (listing_id,),
    ).fetchone()

    if not listing:
        return None, 0

    sqft = listing["sqft"]
    lat = listing["lat"]
    lon = listing["lon"]

    if not sqft or lat is None or lon is None:
        return None, 0

    sqft_band_pct = float(criteria.get("sqft_band_pct", 0.15))
    min_sqft = sqft * (1 - sqft_band_pct)
    max_sqft = sqft * (1 + sqft_band_pct)

    lookback_days = int(criteria.get("comp_lookback_days", 365))
    cutoff = (_utc_now() - timedelta(days=lookback_days)).date().isoformat()

    rows = conn.execute(
        """
        SELECT s.sale_price, s.sale_date, p.sqft, p.lat, p.lon
        FROM sales s
        JOIN properties p ON p.id = s.property_id
        WHERE p.sqft BETWEEN ? AND ?
          AND p.lat IS NOT NULL
          AND p.lon IS NOT NULL
          AND s.sale_date >= ?
        """,
        (min_sqft, max_sqft, cutoff),
    ).fetchall()

    radius = float(criteria.get("comp_radius_miles", 1.0))
    psf_values = []
    for row in rows:
        dist = haversine_miles(lat, lon, row["lat"], row["lon"])
        if dist <= radius and row["sqft"]:
            psf_values.append(row["sale_price"] / row["sqft"])

    median_psf = safe_median(psf_values)
    return median_psf, len(psf_values)
