import os
import requests
from duckduckgo_search import DDGS

import time

def download_images(query, folder, num=50):
    os.makedirs(folder, exist_ok=True)
    with DDGS() as ddgs:
        results = ddgs.images(query, max_results=num)
        for i, result in enumerate(results):
            url = result["image"]
            try:
                img_data = requests.get(url, timeout=10).content
                with open(os.path.join(folder, f"{query}_{i}.jpg"), "wb") as f:
                    f.write(img_data)
                time.sleep(1)  # <-- add delay to avoid rate limit
            except Exception as e:
                print("Failed:", url, e)


animals = ["cat", "dog", "lion", "tiger", "elephant"]
for animal in animals:
    download_images(animal, f"dataset/train/{animal}", num=50)
