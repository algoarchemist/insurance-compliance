"""Maps service — Hospital geo lookup using Google Maps API."""

import httpx
from config import settings


async def geocode_address(address: str) -> dict:
    """Get lat/lng from address string."""
    if not settings.GOOGLE_MAPS_API_KEY:
        return {"lat": 13.0827, "lng": 80.2707}  # Default Chennai

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": address, "key": settings.GOOGLE_MAPS_API_KEY},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

    if data.get("results"):
        location = data["results"][0]["geometry"]["location"]
        return {"lat": location["lat"], "lng": location["lng"]}
    return {"lat": 0, "lng": 0}


async def find_nearby_hospitals(lat: float, lng: float, radius_km: int = 10) -> list:
    """Find hospitals near a location using Google Places API."""
    if not settings.GOOGLE_MAPS_API_KEY:
        return []

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
            params={
                "location": f"{lat},{lng}",
                "radius": radius_km * 1000,
                "type": "hospital",
                "key": settings.GOOGLE_MAPS_API_KEY,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

    return [
        {
            "name": r.get("name"),
            "address": r.get("vicinity"),
            "lat": r["geometry"]["location"]["lat"],
            "lng": r["geometry"]["location"]["lng"],
            "rating": r.get("rating"),
        }
        for r in data.get("results", [])
    ]


def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two coordinates in km (Haversine formula)."""
    from math import radians, cos, sin, asin, sqrt
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
    c = 2 * asin(sqrt(a))
    return 6371 * c
