import urllib.request
import urllib.error
import json

models_to_test = [
    "google/vit-base-patch16-224",
    "dima806/food-101-image-classification",
    "Kaludi/food-category-classification-v2.0",
    "Pimaa/food101",
    "nateraw/food101",
    "MichalMlodawski/vit-finetuned-food101",
    "Oysiyl/vit-base-patch16-224-in21k-finetuned-food101"
]

data = json.dumps({"inputs": "https://upload.wikimedia.org/wikipedia/commons/a/a3/Eq_it-na_pizza-margherita_sep2005_sml.jpg"}).encode('utf-8')

for model in models_to_test:
    url = f"https://router.huggingface.co/hf-inference/models/{model}"
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            print(f"{model}: {response.getcode()} - {response.read().decode('utf-8')[:100]}")
    except urllib.error.HTTPError as e:
        print(f"{model}: HTTP {e.code} - {e.read().decode('utf-8')[:100]}")
    except Exception as e:
        print(f"{model}: ERROR - {e}")
