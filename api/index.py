from http.server import BaseHTTPRequestHandler
import json
import os
import time
from google import genai

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemma-4-31b-it"
client = genai.Client(api_key=API_KEY) if API_KEY else None


def extract_text(response):
    try:
        return response.text.strip()
    except Exception:
        return "unknown"


def call_with_retry(fn, max_attempts=5, delay=2):
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except Exception as e:
            last_error = e
            if attempt < max_attempts:
                time.sleep(delay)
    raise last_error


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "message": "API is running. Use POST with imageBase64 and mimeType."
        }).encode("utf-8"))

    def do_POST(self):
        if not client:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Missing GEMINI_API_KEY"}).encode("utf-8"))
            return

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            payload = json.loads(body.decode("utf-8"))

            image_base64 = payload.get("imageBase64")
            mime_type = payload.get("mimeType", "image/jpeg")
            extra_prompt = payload.get("extraPrompt", "")

            if not image_base64:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing imageBase64"}).encode("utf-8"))
                return

            identify_prompt = (
                "Identify the product shown in this image. "
                "Return only the most likely product name. "
                "If visible, include brand, variant and volume like ml. "
                "If uncertain, return: unknown. "
                "Display Answer as Product Name: Brand: Size:"
            )

            if extra_prompt.strip():
                identify_prompt += f" {extra_prompt.strip()}"

            identify_response = call_with_retry(lambda: client.models.generate_content(
                model=MODEL_NAME,
                contents=[
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": image_base64
                        }
                    },
                    "\n\n",
                    identify_prompt
                ]
            ))
            product_name = extract_text(identify_response)

            price_prompt = f"""
Estimate the likely retail price for this product: {product_name}
Convert currency to Euros
Return in this format:
Product Name: Brand | Product Name
Estimated Price Range: ...
Size: ...
Description of Product: ...
Confidence: low/medium/high and as percentage
"""

            price_response = call_with_retry(lambda: client.models.generate_content(
                model=MODEL_NAME,
                contents=price_prompt
            ))
            answer = extract_text(price_response)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "product_name": product_name,
                "result": answer
            }).encode("utf-8"))

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
