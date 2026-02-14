import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional

import requests

DATAFINITI_SEARCH_URL = "https://api.datafiniti.co/v4/properties/search"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _date_days_ago(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()


def _last_ingest_date(conn) -> Optional[str]:
    row = conn.execute(
        "SELECT ended_at FROM ingest_runs WHERE source LIKE ? ORDER BY ended_at DESC LIMIT 1",
        ("datafiniti%",),
    ).fetchone()
    if not row or not row["ended_at"]:
        return None
    return row["ended_at"][:10]


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


def _build_query(criteria: dict, since_date: str) -> str:
    counties = criteria.get("markets", ["Nassau County, NY", "Suffolk County, NY"])
    county_terms = []
    for county in counties:
        name = county.split(",")[0].replace(" County", "").strip()
        if name:
            county_terms.append(f'"{name}"')

    county_query = " OR ".join(county_terms) if county_terms else '"Nassau" OR "Suffolk"'

    return (
        "country:US AND province:NY "
        f"AND county:({county_query}) "
        "AND propertyType:\"Single Family Dwelling\" "
        "AND mostRecentStatus:\"For Sale\" "
        f"AND mostRecentStatusFirstDateSeen:[{since_date} TO *]"
    )


def _extract_listing_url(record: dict) -> Optional[str]:
    status_history = record.get("statusHistory") or []
    for status in status_history:
        if (status.get("type") or "").lower() == "for sale":
            urls = status.get("sourceURLs") or []
            if urls:
                return urls[0]
    return record.get("mostRecentEstimatedPriceSourceURL")


def ingest_datafiniti(config, conn) -> Dict[str, Any]:
    if not config.datafiniti_api_key:
        return {"status": "skipped", "reason": "missing DATAFINITI_API_KEY"}

    criteria = config.criteria
    lookback_days = int(criteria.get("datafiniti_lookback_days", 7))
    num_records = int(criteria.get("datafiniti_num_records", 50))

    since_date = _last_ingest_date(conn) or _date_days_ago(lookback_days)
    query = _build_query(criteria, since_date)

    headers = {
        "Authorization": f"Bearer {config.datafiniti_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "query": query,
        "format": "JSON",
        "num_records": num_records,
        "download": False,
    }

    response = requests.post(DATAFINITI_SEARCH_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()

    records: List[dict] = data.get("records", [])
    new_listings = 0
    updated_listings = 0

    for record in records:
        source_property_id = record.get("id")
        if not source_property_id:
            keys = record.get("keys") or []
            if keys:
                source_property_id = keys[0]

        if not source_property_id:
            continue

        address = record.get("address")
        city = record.get("city")
        state = record.get("province")
        zip_code = record.get("postalCode")
        lat = _parse_float(record.get("latitude"))
        lon = _parse_float(record.get("longitude"))
        sqft = _parse_int(record.get("floorSizeValue"))
        year_built = _parse_int(record.get("yearBuilt"))
        lot_size = _parse_int(record.get("lotSizeValue"))
        property_type = record.get("propertyType")

        conn.execute(
            """
            INSERT INTO properties (source, source_property_id, address, city, state, zip, lat, lon,
                                   beds, baths, sqft, year_built, lot_size, property_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source, source_property_id) DO UPDATE SET
                address=excluded.address,
                city=excluded.city,
                state=excluded.state,
                zip=excluded.zip,
                lat=excluded.lat,
                lon=excluded.lon,
                sqft=COALESCE(excluded.sqft, properties.sqft),
                year_built=COALESCE(excluded.year_built, properties.year_built),
                lot_size=COALESCE(excluded.lot_size, properties.lot_size),
                property_type=COALESCE(excluded.property_type, properties.property_type)
            """,
            (
                "datafiniti",
                str(source_property_id),
                address,
                city,
                state,
                zip_code,
                lat,
                lon,
                None,
                None,
                sqft,
                year_built,
                lot_size,
                property_type,
            ),
        )

        property_row = conn.execute(
            "SELECT id FROM properties WHERE source = ? AND source_property_id = ?",
            ("datafiniti", str(source_property_id)),
        ).fetchone()
        if not property_row:
            continue
        property_id = property_row["id"]

        list_price = _parse_float(record.get("mostRecentSaleListPriceAmount"))
        if list_price is None:
            list_price = _parse_float(record.get("mostRecentPriceAmount"))

        list_date = record.get("mostRecentSaleListPriceDate") or record.get("mostRecentPriceDate")
        status = record.get("mostRecentStatus")
        status_first_seen = record.get("mostRecentStatusFirstDateSeen")
        days_on_market = _parse_int(record.get("daysOnMarket"))
        url = _extract_listing_url(record)

        listing_psf = None
        if list_price is not None and sqft:
            listing_psf = list_price / sqft

        source_listing_id = f"{source_property_id}:{status_first_seen or list_date or _utc_now()}"

        existing = conn.execute(
            "SELECT id FROM listings WHERE source = ? AND source_listing_id = ?",
            ("datafiniti", source_listing_id),
        ).fetchone()

        conn.execute(
            """
            INSERT INTO listings (property_id, source, source_listing_id, status, list_price, list_date,
                                  last_seen, url, psf, days_on_market)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source, source_listing_id) DO UPDATE SET
                status=excluded.status,
                list_price=excluded.list_price,
                list_date=excluded.list_date,
                last_seen=excluded.last_seen,
                url=excluded.url,
                psf=excluded.psf,
                days_on_market=excluded.days_on_market
            """,
            (
                property_id,
                "datafiniti",
                source_listing_id,
                status,
                list_price,
                list_date,
                _utc_now(),
                url,
                listing_psf,
                days_on_market,
            ),
        )

        if existing:
            updated_listings += 1
        else:
            new_listings += 1

        listing_row = conn.execute(
            "SELECT id FROM listings WHERE source = ? AND source_listing_id = ?",
            ("datafiniti", source_listing_id),
        ).fetchone()
        if listing_row:
            listing_id = listing_row["id"]
            for image_url in record.get("imageURLs") or []:
                conn.execute(
                    """
                    INSERT INTO media (listing_id, url)
                    SELECT ?, ?
                    WHERE NOT EXISTS (
                        SELECT 1 FROM media WHERE listing_id = ? AND url = ?
                    )
                    """,
                    (listing_id, image_url, listing_id, image_url),
                )

    conn.commit()

    return {
        "status": "ok",
        "query": query,
        "num_records": len(records),
        "new_listings": new_listings,
        "updated_listings": updated_listings,
    }
