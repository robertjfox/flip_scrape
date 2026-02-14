from typing import Dict, Any


def analyze_listing_photos(listing_id: int, photo_urls: list[str]) -> Dict[str, Any]:
    raise NotImplementedError(
        "Photo analysis is not wired yet. Add a vision model integration in src/underwrite/vision.py."
    )
