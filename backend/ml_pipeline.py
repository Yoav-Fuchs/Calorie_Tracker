import os
import google.generativeai as genai
import json

class MLPipeline:
    def __init__(self, api_key: str = None):
        print("Initializing Gemini Vision Pipeline...")
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-3.5-flash')
        else:
            self.model = None
            print("WARNING: GEMINI_API_KEY is not set.")

    async def analyze_image(self, image_bytes: bytes):
        """
        Runs the image through Gemini Vision and extracts structured nutritional JSON data.
        """
        if not self.model:
            return []

        prompt = """
        Analyze this image of food. Identify all the main food components.
        For each component, visually estimate the weight in grams and provide the macro nutritional values (calories, protein in grams, carbs in grams, fat in grams).
        Return ONLY a raw JSON array of objects. Do not include markdown formatting or backticks like ```json.
        Example Format of each object:
        {
          "name": "Grilled Chicken Breast",
          "confidence": 0.95,
          "estimated_weight_g": 200,
          "estimated_volume_cm3": 200,
          "calories": 330,
          "protein_g": 62,
          "carbs_g": 0,
          "fat_g": 7
        }
        """
        
        try:
            image_parts = [
                {
                    "mime_type": "image/jpeg",
                    "data": image_bytes
                }
            ]
            
            # This runs synchronously in the current thread, but works extremely fast for 1.5 Flash.
            response = self.model.generate_content([prompt, image_parts[0]])
            
            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:-3]
            elif raw_text.startswith("```"):
                raw_text = raw_text[3:-3]
                
            results = json.loads(raw_text)
            
            # Ensure proper structure
            for r in results:
                if 'nutrition' not in r:
                    r['nutrition'] = {
                        "calories": r.get("calories", 0),
                        "protein_g": r.get("protein_g", 0),
                        "carbs_g": r.get("carbs_g", 0),
                        "fat_g": r.get("fat_g", 0)
                    }
            return results
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return []
