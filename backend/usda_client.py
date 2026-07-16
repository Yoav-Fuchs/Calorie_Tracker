import httpx
import os
from dotenv import load_dotenv

load_dotenv()

USDA_API_KEY = os.getenv("USDA_API_KEY", "DEMO_KEY")
USDA_BASE_URL = "https://api.nal.usda.gov/fdc/v1"

class USDAClient:
    def __init__(self, api_key: str = USDA_API_KEY):
        self.api_key = api_key
        
    async def search_food(self, query: str):
        """
        Searches food in the USDA FoodData Central database.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{USDA_BASE_URL}/foods/search", 
                    params={"query": query, "api_key": self.api_key, "pageSize": 1}
                )
                response.raise_for_status()
                data = response.json()
                
                if not data.get("foods"):
                    return None
                    
                first_food = data["foods"][0]
                return first_food
            except Exception as e:
                print(f"USDA API Error: {e}")
                return None
