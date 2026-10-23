import os
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

SERPAPI_URL = "https://serpapi.com/search.json"
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "cfe3538b9436ce397567de2095d38b6996b3e33ccbd44ed6fe045db780ff74bc").strip()
GOOGLE_LOCATION = os.getenv("SHOP_LOCATION", "India")
GOOGLE_COUNTRY = os.getenv("SHOP_GL", "in")
GOOGLE_LANGUAGE = os.getenv("SHOP_HL", "en")

def clean_price(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

def merchant_label(source):
    if not source:
        return "Unknown seller"
    return str(source).strip()

def search_live_shopping(query, limit=40):
    """Fetch live shopping results for ANY search term via Google Shopping through SerpApi.

    This is intentionally provider-based: the app does not hardcode products.
    A SERPAPI_KEY is required for live results.
    """
    if not SERPAPI_KEY:
        return {
            "ok": False,
            "provider": "SerpApi / Google Shopping",
            "error": "SERPAPI_KEY is not configured. Add your SerpApi key before searching live prices.",
            "results": [],
        }

    params = {
        "engine": "google_shopping",
        "q": query,
        "api_key": SERPAPI_KEY,
        "location": GOOGLE_LOCATION,
        "gl": GOOGLE_COUNTRY,
        "hl": GOOGLE_LANGUAGE,
        "device": "desktop",
        "no_cache": "true",
    }

    try:
        response = requests.get(SERPAPI_URL, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        return {
            "ok": False,
            "provider": "SerpApi / Google Shopping",
            "error": f"Live provider request failed: {exc}",
            "results": [],
        }
    except ValueError:
        return {
            "ok": False,
            "provider": "SerpApi / Google Shopping",
            "error": "The live provider returned an invalid JSON response.",
            "results": [],
        }

    if payload.get("error"):
        return {
            "ok": False,
            "provider": "SerpApi / Google Shopping",
            "error": str(payload["error"]),
            "results": [],
        }

    results = []
    for item in payload.get("shopping_results", [])[:limit]:
        price = clean_price(item.get("extracted_price"))
        if price is None:
            continue

        link = item.get("link") or item.get("product_link")
        results.append({
            "id": item.get("product_id"),
            "title": item.get("title", "Unnamed product"),
            "merchant": merchant_label(item.get("source")),
            "price": price,
            "price_display": item.get("price") or f"₹{price:,.0f}",
            "old_price": clean_price(item.get("extracted_old_price")),
            "delivery": item.get("delivery"),
            "rating": item.get("rating"),
            "reviews": item.get("reviews"),
            "thumbnail": item.get("thumbnail"),
            "link": link,
            "product_link": item.get("product_link"),
            "multiple_sources": item.get("multiple_sources", []),
        })

    results.sort(key=lambda x: x["price"])
    return {
        "ok": True,
        "provider": "SerpApi / Google Shopping",
        "query": query,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "result_count": len(results),
        "results": results,
    }

@app.get("/")
def index():
    return render_template("index.html", live_enabled=bool(SERPAPI_KEY))

@app.get("/api/health")
def health():
    return jsonify({
        "ok": True,
        "live_provider_configured": bool(SERPAPI_KEY),
        "provider": "SerpApi / Google Shopping",
    })

@app.get("/api/search")
def api_search():
    query = request.args.get("q", "").strip()
    if len(query) < 2:
        return jsonify({
            "ok": False,
            "error": "Enter at least 2 characters to search for a product.",
            "results": [],
        }), 400

    return jsonify(search_live_shopping(query))

@app.get("/api/products")
def api_products_compat():
    # Backward-compatible endpoint for the old frontend/API shape.
    query = request.args.get("search", "").strip()
    if not query:
        query = request.args.get("q", "").strip()

    if not query:
        return jsonify({
            "ok": True,
            "products": [],
            "message": "This version uses dynamic live search. Pass ?search=<product>.",
        })

    data = search_live_shopping(query)
    return jsonify({
        "ok": data.get("ok", False),
        "products": data.get("results", []),
        "error": data.get("error"),
        "checked_at": data.get("checked_at"),
    })

@app.post("/api/refresh")
def api_refresh():
    query = request.json.get("q", "").strip() if request.is_json else ""
    if len(query) < 2:
        return jsonify({"ok": False, "error": "Provide the product search query."}), 400
    return jsonify(search_live_shopping(query))

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
