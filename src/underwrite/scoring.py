import json
from typing import Optional, Dict, Any

from src.underwrite.comps import compute_comp_stats


def score_listing(conn, listing_id: int, criteria: dict) -> Optional[Dict[str, Any]]:
    median_psf, comp_count = compute_comp_stats(conn, listing_id, criteria)
    min_comp_count = int(criteria.get("min_comp_count", 5))

    if not median_psf or comp_count < min_comp_count:
        return None

    listing = conn.execute(
        """
        SELECT l.id AS listing_id, l.list_price, l.psf, p.sqft
        FROM listings l
        JOIN properties p ON p.id = l.property_id
        WHERE l.id = ?
        """,
        (listing_id,),
    ).fetchone()

    if not listing or not listing["sqft"]:
        return None

    listing_psf = listing["psf"]
    if not listing_psf and listing["list_price"]:
        listing_psf = listing["list_price"] / listing["sqft"]

    if not listing_psf:
        return None

    discount_pct = (median_psf - listing_psf) / median_psf
    arv = median_psf * listing["sqft"]

    condition_row = conn.execute(
        "SELECT AVG(condition_score) AS avg_score FROM media WHERE listing_id = ?",
        (listing_id,),
    ).fetchone()
    condition_score = condition_row["avg_score"] if condition_row else None

    score = discount_pct

    payload = {
        "listing_id": listing_id,
        "median_psf": median_psf,
        "listing_psf": listing_psf,
        "discount_pct": discount_pct,
        "arv": arv,
        "condition_score": condition_score,
        "comp_count": comp_count,
        "score": score,
    }

    conn.execute(
        """
        INSERT INTO comp_sets (listing_id, median_psf, comp_count, radius_miles, sqft_band_pct)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            listing_id,
            median_psf,
            comp_count,
            float(criteria.get("comp_radius_miles", 1.0)),
            float(criteria.get("sqft_band_pct", 0.15)),
        ),
    )

    conn.execute(
        """
        INSERT INTO underwrites (listing_id, arv, discount_pct, condition_score, rehab_cost, score, reasons_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            listing_id,
            arv,
            discount_pct,
            condition_score,
            None,
            score,
            json.dumps({
                "median_psf": median_psf,
                "listing_psf": listing_psf,
                "comp_count": comp_count,
            }),
        ),
    )
    conn.commit()

    return payload
