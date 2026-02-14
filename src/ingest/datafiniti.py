from typing import Dict, Any


def ingest_datafiniti(config, conn) -> Dict[str, Any]:
    if not config.datafiniti_api_key:
        return {"status": "skipped", "reason": "missing DATAFINITI_API_KEY"}

    raise NotImplementedError(
        "Datafiniti ingest is not wired yet. Add API integration in src/ingest/datafiniti.py."
    )
