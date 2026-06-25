from pathlib import Path
from google import genai
import os
import base64
from html import escape

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("Missing GEMINI_API_KEY environment variable")

client = genai.Client(api_key=API_KEY)
MODEL_NAME = "gemma-4-31b-it"


def ask_prompt(prompt: str, model: str = MODEL_NAME) -> str:
    response = client.models.generate_content(
        model=model,
        contents=prompt
    )
    return response.text


def lookup_product_from_image(image_path: str, extra_prompt: str = "", model: str = MODEL_NAME) -> str:
    uploaded_file = client.files.upload(file=Path(image_path))

    prompt = (
        "Identify the product shown in this image. "
        "Return only the most likely product name. "
        "If visible, include brand, variant and volume like ml. "
        "If uncertain, return: unknown. "
        "Display Answer as Product Name: Brand: Size:"
    )

    if extra_prompt.strip():
        prompt += f" {extra_prompt.strip()}"

    response = client.models.generate_content(
        model=model,
        contents=[uploaded_file, "\n\n", prompt]
    )
    return response.text


image_path = input("Enter image path: ").strip()
if not image_path:
    raise ValueError("Please provide an image path")

for attempt in range(5):
    try:
        product_name = lookup_product_from_image(image_path)
        print(product_name)
        break
    except Exception:
        if attempt == 4:
            raise

answer = ask_prompt(f"""
Estimate the likely retail price for this product: {product_name}
Convert currency to Euros
Return in this format:
Product Name: Brand | Product Name
Estimated Price Range: ...
Size: ...
Description of Product: ...
Confidence: low/medium/high
""")

ext = os.path.splitext(image_path)[1].lower()
mime = "image/png" if ext == ".png" else "image/jpeg"

with open(image_path, "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()

html = f"""
<div style="display:flex; gap:20px; align-items:flex-start; font-family:Arial,sans-serif;">
  <div style="min-width:320px; max-width:320px;">
    <img src="data:{mime};base64,{img_b64}"
         style="width:100%; border-radius:12px; box-shadow:0 4px 14px rgba(0,0,0,0.15);">
  </div>

  <div style="flex:1; max-width:800px; background:#f7f7f7; padding:16px; border-radius:12px; border:1px solid #e2e2e2;">
    <div style="font-size:18px; font-weight:700; margin-bottom:10px;">Model output:</div>
    <pre style="white-space:pre-wrap; overflow-wrap:anywhere; word-break:break-word; margin:0; font-size:14px; line-height:1.5;">{escape(answer)}</pre>
  </div>
</div>
"""

with open("output.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Saved result to output.html")