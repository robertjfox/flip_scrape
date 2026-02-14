from datetime import datetime, timezone
from typing import Dict, Any, Optional

import requests

ESTATED_PROPERTY_URL = "https://apis.estated.com/v4/property"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_float(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_int(value):
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _combined_address(row) -> Optional[str]:
    if not row["address"] or not row["city"] or not row["state"]:
        return None
    parts = [row["address"], row["city"], row["state"]]
    if row["zip"]:
        parts[-1] = f"{row['state']} {row['zip']}"
    return ", ".join(parts)


def enrich_with_estated(config, conn) -> Dict[str, Any]:
    if not config.estated_api_key:
        return {"status": "skipped", "reason": "missing ESTATED_API_KEY"}

    criteria = config.criteria
    max_requests = int(criteria.get("estated_max_requests", 50))

    rows = conn.execute(
        """
        SELECT p.id, p.address, p.city, p.state, p.zip
        FROM properties p
        LEFT JOIN sales s ON s.property_id = p.id AND s.source = 'estated'
        WHERE s.id IS NULL
        LIMIT ?
        """,
        (max_requests,),
    ).fetchall()

    processed = 0
    errors = []

    for row in rows:
        combined = _combined_address(row)
        if not combined:
            continue

        params = {
            "token": config.estated_api_key,
            "combined_address": combined,
        }
        resp = requests.get(ESTATED_PROPERTY_URL, params=params, timeout=30)
        if resp.status_code != 200:
            errors.append(f"{combined}: {resp.status_code}")
            continue

        payload = resp.json()
        data = payload.get("data") or {}
        if not data:
            continue

        address = data.get("address") or {}
        structure = data.get("structure") or {}
        parcel = data.get("parcel") or {}
        deeds = data.get("deeds") or []

        conn.execute(
            """
            UPDATE properties SET
                address = COALESCE(?, address),
                city = COALESCE(?, city),
                state = COALESCE(?, state),
                zip = COALESCE(?, zip),
                lat = COALESCE(?, lat),
                lon = COALESCE(?, lon),
                beds = COALESCE(?, beds),
                baths = COALESCE(?, baths),
                sqft = COALESCE(?, sqft),
                year_built = COALESCE(?, year_built),
                lot_size = COALESCE(?, lot_size)
            WHERE id = ?
            """,
            (
                address.get("formatted_street_address"),
                address.get("city"),
                address.get("state"),
                address.get("zip_code"),
                _parse_float(address.get("latitude")),
                _parse_float(address.get("longitude")),
                _parse_float(structure.get("beds_count")),
                _parse_float(structure.get("baths")),
                _parse_int(structure.get("total_area_sq_ft")),
                _parse_int(structure.get("year_built")),
                _parse_int(parcel.get("area_sq_ft")),
                row["id"],
            ),
        )

        for deed in deeds:
            sale_price = _parse_float(deed.get("sale_price"))
            sale_date = deed.get("recording_date") or deed.get("original_contract_date")
            if not sale_price or not sale_date:
                continue

            exists = conn.execute(
                """
                SELECT 1 FROM sales WHERE property_id = ? AND sale_price = ? AND sale_date = ?
                """,
                (row["id"], sale_price, sale_date),
            ).fetchone()
            if exists:
                continue

            conn.execute(
                """
                INSERT INTO sales (property_id, source, sale_price, sale_date)
                VALUES (?, ?, ?, ?)
                """,
                (row["id"], "estated", sale_price, sale_date),
            )

        processed += 1

    conn.commit()

    return {
        "status": "ok",
        "processed": processed,
        "errors": errors,
        "timestamp": _utc_now(),
    }
