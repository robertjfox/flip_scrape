import json
from datetime import datetime, timezone

from src.ingest.datafiniti import ingest_datafiniti
from src.ingest.estated import enrich_with_estated


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_ingest(config, conn):
    started_at = _utc_now()
    errors = []
    new_listings = 0
    updated_listings = 0

    try:
        ingest_datafiniti(config, conn)
    except NotImplementedError as exc:
        errors.append(str(exc))

    try:
        enrich_with_estated(config, conn)
    except NotImplementedError as exc:
        errors.append(str(exc))

    ended_at = _utc_now()
    conn.execute(
        """
        INSERT INTO ingest_runs (source, started_at, ended_at, new_listings, updated_listings, errors_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "datafiniti+estated",
            started_at,
            ended_at,
            new_listings,
            updated_listings,
            json.dumps(errors) if errors else None,
        ),
    )
    conn.commit()

    return {
        "started_at": started_at,
        "ended_at": ended_at,
        "errors": errors,
        "new_listings": new_listings,
        "updated_listings": updated_listings,
    }
