import os
import httpx

class MLPipeline:
    def __init__(self, api_key: str = None):
        print("Initializing ML Pipeline using Hugging Face API...")
        self.api_key = api_key or os.getenv("HF_API_KEY")
        self.api_url = "https://router.huggingface.co/hf-inference/models/nateraw/food"

    async def analyze_image(self, image_bytes: bytes):
        """
        Runs the image through the Hugging Face Free Inference API.
        """
        headers = {"Content-Type": "application/octet-stream"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        results = []
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url, 
                    headers=headers, 
                    content=image_bytes,
                    timeout=30.0 # Cold starts can take 20-30 seconds
                )
                
            if response.status_code == 200:
                preds = response.json()
                if preds and isinstance(preds, list):
                    top_pred = preds[0]
                    
                    # Simulated Volume based on a fixed value for demonstration
                    simulated_volume = 150.0 
                    
                    results.append({
                        "name": top_pred["label"].title(),
                        "confidence": top_pred["score"],
                        "estimated_volume_cm3": simulated_volume,
                        "estimated_weight_g": simulated_volume * 1.05 
                    })
            else:
                print(f"Hugging Face API Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Error calling Hugging Face API: {e}")
            
        return results
