import io
from PIL import Image
import torch

try:
    from ultralytics import YOLO
    from transformers import pipeline
except ImportError:
    # During installation, these might fail
    YOLO = None
    pipeline = None

class MLPipeline:
    def __init__(self):
        print("Initializing ML Models... This may take a while on the first run.")
        # 1. Segmentation Model (YOLOv8-seg)
        if YOLO:
            self.seg_model = YOLO('yolov8n-seg.pt')  # Nano version for speed
        else:
            self.seg_model = None

        # 2. Classification Model (ViT fine-tuned on Food-101)
        if pipeline:
            # We use nateraw/food101 which is a standard choice for food-101 on Hugging Face
            self.classifier = pipeline("image-classification", model="nateraw/food101")
        else:
            self.classifier = None

        # 3. Depth Estimation (MiDaS)
        try:
            self.midas = torch.hub.load("intel-isl/MiDaS", "MiDaS_small")
            device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
            self.midas.to(device)
            self.midas.eval()
            self.midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms").small_transform
        except Exception as e:
            print(f"Error loading MiDaS: {e}")
            self.midas = None

    def analyze_image(self, image_bytes: bytes):
        """
        Runs the image through the 3-step pipeline.
        """
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        # In a complete implementation, we would:
        # 1. Run YOLO to crop out individual food items from the plate.
        # 2. Run ViT on each cropped item.
        # 3. Run MiDaS on the original image, cross-reference with YOLO bounding boxes,
        #    and integrate depth values to estimate relative volume.
        
        # Since this is a foundation, we run ViT on the whole image as an example
        results = []
        if self.classifier:
            preds = self.classifier(image)
            top_pred = preds[0]
            
            # Simulated Volume based on a fixed value for demonstration
            # Actual volume requires reference object logic and depth integration.
            simulated_volume = 150.0 
            
            results.append({
                "name": top_pred["label"].title(),
                "confidence": top_pred["score"],
                "estimated_volume_cm3": simulated_volume,
                "estimated_weight_g": simulated_volume * 1.05 # Assuming density slightly higher than water
            })
            
        return results
