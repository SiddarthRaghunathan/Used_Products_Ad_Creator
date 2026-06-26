# AI resale listing assistant

This project uses Google's Gen AI SDK to identify a product from an image and return the most likely product name, brand, variant, and size.

**Live Demo: https://used-products-ad-creator-72bts3zqk-sidprojects.vercel.app/**

## What it does
- Uploads an image to the model
- Sends a prompt asking for the product identity
- Returns structured text output
- Handles uncertainity with a confidence metric

## Example use case
Useful for:
- resale listing automation
- ad creation workflows
- image-based product search

## Setup
```bash
pip install -r requirements.txt
export GEMINI_API_KEY=your_key_here
python product_lookup.py
```

## Limitations
- Product identity may be wrong when packaging is unclear
- Newer product (bought in last 12 months) may not reflect accurate pricing
- OCR quality depends on image clarity
- Output is probabilistic, not guaranteed
