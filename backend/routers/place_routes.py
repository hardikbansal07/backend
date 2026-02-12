from fastapi import APIRouter, HTTPException, Query
import httpx
import logging
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/places", tags=["Place Search"])
logger = logging.getLogger(__name__)

PHOTON_API_URL = "https://photon.komoot.io/api/"

@router.get("/search", response_model=Dict[str, Any])
async def search_places(
    q: str = Query(..., min_length=2, description="Place name to search for"),
    limit: int = Query(10, ge=1, le=50, description="Number of results to return"),
    lang: str = Query("en", description="Language code (e.g., en, de, fr)")
):
    """
    Search for places using the Photon API (OpenStreetMap data).
    """
    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "User-Agent": "AstrocareApp/1.0 (contact@astrocareai.com)"
            }
            response = await client.get(
                PHOTON_API_URL,
                params={
                    "q": q,
                    "limit": limit,
                    "lang": lang
                },
                headers=headers,
                timeout=5.0
            )
            response.raise_for_status()
            data = response.json()
            
            features = data.get("features", [])
            results = []
            
            for feature in features:
                props = feature.get("properties", {})
                geometry = feature.get("geometry", {})
                coords = geometry.get("coordinates", [None, None]) # lon, lat
                
                # Filter out results without coordinates
                if not coords or len(coords) < 2:
                    continue
                    
                # Standardize the output
                city = props.get("city") or props.get("name") or props.get("town") or props.get("village")
                country = props.get("country")
                state = props.get("state")
                
                label_parts = []
                if props.get("name"): label_parts.append(props["name"])
                if city and city != props.get("name"): label_parts.append(city)
                if state: label_parts.append(state)
                if country: label_parts.append(country)
                
                label = ", ".join(label_parts)
                
                results.append({
                    "name": props.get("name"),
                    "city": city,
                    "state": state,
                    "country": country,
                    "latitude": coords[1],
                    "longitude": coords[0],
                    "label": label,
                    "raw": props # Include raw properties for debugging/extra details
                })
                
            return {
                "status": "success",
                "results": results,
                "count": len(results)
            }
            
    except httpx.HTTPStatusError as e:
        logger.error(f"Photon API HTTP error: {e}")
        raise HTTPException(status_code=e.response.status_code, detail="External place search service unavailable")
    except httpx.RequestError as e:
        logger.error(f"Photon API request error: {e}")
        raise HTTPException(status_code=503, detail="Connection to place search service failed")
    except Exception as e:
        logger.error(f"Unexpected error in place search: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during place search")
