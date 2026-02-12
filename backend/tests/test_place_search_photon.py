import httpx
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000/calc/api/v1/places/search"

async def test_search():
    params = {
        "q": "Bangalore",
        "limit": 5,
        "lang": "en"
    }
    logger.info(f"Testing search with params: {params}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(BASE_URL, params=params, timeout=10.0)
            logger.info(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info("Response JSON:")
                logger.info(data)
                
                if data.get("status") == "success" and len(data.get("results", [])) > 0:
                    logger.info("✅ Place search verification PASSED")
                else:
                    logger.error("❌ Place search verification FAILED: Unexpected response structure")
            else:
                logger.error(f"❌ Place search verification FAILED: Status {response.status_code}")
                logger.error(f"Response text: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Place search verification FAILED: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_search())
