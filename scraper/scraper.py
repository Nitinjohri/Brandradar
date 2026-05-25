import os
import sys
import time
import argparse
import requests
from dotenv import load_dotenv
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from backend.Database import SessionLocal, engine
from backend import models
from sqlalchemy import func

load_dotenv()
API_KEY         = os.getenv("RAINFOREST_API_KEY")
AMAZON_DOMAIN   = os.getenv("AMAZON_DOMAIN", "amazon.in")
BASE_URL        = "https://api.rainforestapi.com/request"

BRANDS = [
    "Safari",
    "Skybags",
    "American Tourister",
    "VIP",
]

PRODUCTS_PER_BRAND  = 10
REVIEWS_PER_PRODUCT = 50
REQUEST_DELAY       = 1.5
MAX_RETRIES         = 3

analyzer = SentimentIntensityAnalyzer()

def log(msg: str, indent: int = 0):
    print("  " * indent + msg)


def score_text(text: str) -> tuple:
    compound = analyzer.polarity_scores(text)["compound"]
    if compound >= 0.05:
        label = "positive"
    elif compound <= -0.05:
        label = "negative"
    else:
        label = "neutral"
    return round(compound, 4), label


def safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value) if value else default
    except (TypeError, ValueError):
        return default


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value) if value else default
    except (TypeError, ValueError):
        return default


def detect_category(title: str) -> str:
    t = title.lower()
    if any(w in t for w in ["cabin", "55cm", "carry-on", "carry on"]):
        return "cabin"
    elif any(w in t for w in ["75cm", "76cm", "large"]):
        return "check-in large"
    elif any(w in t for w in ["65cm", "medium"]):
        return "check-in medium"
    elif any(w in t for w in ["set", "combo", "pack of"]):
        return "luggage set"
    return "general"

def rainforest_get(params: dict):
    params["api_key"]       = API_KEY
    params["amazon_domain"] = AMAZON_DOMAIN
    
    resp = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(BASE_URL, params=params, timeout=30)
            
            if resp.status_code == 429:
                wait = attempt * 10
                log(f"Rate limited (429) — Attempt {attempt}/{MAX_RETRIES} — Waiting {wait}s...", indent=2)
                time.sleep(wait)
                continue
                
            if resp.status_code == 503:
                wait = attempt * 5
                log(f"Parsing Incident (503) — Attempt {attempt}/{MAX_RETRIES} — Waiting {wait}s...", indent=2)
                time.sleep(wait)
                continue
                
            resp.raise_for_status()
            return resp.json()
            
        except requests.exceptions.Timeout:
            log(f"Timeout — Attempt {attempt}/{MAX_RETRIES}...", indent=2)
            if attempt == MAX_RETRIES: return None
            time.sleep(2)
        except requests.exceptions.HTTPError as e:
            if resp is not None and resp.status_code not in [429, 503]:
                log(f"HTTP error: {e}", indent=2)
                return None
        except Exception as e:
            log(f"Error: {e}", indent=2)
            return None
            
    return None

def search_products(brand: str) -> list:
    log(f"Searching products for: {brand}", indent=1)

    data = rainforest_get({
        "type":              "search",
        "search_term":       f"{brand} luggage trolley bag",
        "sort_by":           "featured",
        "exclude_sponsored": "true",
    })

    if not data or "search_results" not in data:
        log(f"No results for {brand}", indent=2)
        return []

    products = []
    for item in data["search_results"]:
        if not item.get("asin") or not item.get("title"):
            continue
        if item.get("is_sponsored"):
            continue

        buy_box        = item.get("buybox_winner", {})
        price_data     = item.get("price", {})
        current_price  = safe_float(
            buy_box.get("price", {}).get("value") or price_data.get("value")
        )
        original_price = safe_float(
            buy_box.get("rrp", {}).get("value")
            or item.get("rrp", {}).get("value")
            or current_price
        )
        discount = 0.0
        if original_price > 0 and current_price > 0 and original_price > current_price:
            discount = round((1 - current_price / original_price) * 100, 1)

        products.append({
            "asin":             item["asin"],
            "title":            item["title"],
            "price":            current_price,
            "original_price":   original_price,
            "discount_percent": discount,
            "rating":           safe_float(item.get("rating")),
            "review_count":     safe_int(item.get("ratings_total")),
            "image_url":        item.get("image", ""),
            "product_url":      f"https://www.amazon.in/dp/{item['asin']}",
            "category":         detect_category(item["title"]),
        })

        if len(products) >= PRODUCTS_PER_BRAND:
            break

    log(f"Found {len(products)} products", indent=2)
    return products

def fetch_reviews(asin: str, product_title: str) -> list:
    short = product_title[:45] + "..." if len(product_title) > 45 else product_title
    log(f"Reviews → {short}", indent=2)

    collected = []
    page      = 1

    while len(collected) < REVIEWS_PER_PRODUCT:
        data = rainforest_get({
            "type":    "reviews",
            "asin":    asin,
            "page":    str(page),
            "sort_by": "most_recent",
        })

        if not data:
            if page == 1:
                log("⚠️  Reviews API down. Trying fallback to Product endpoint for real top reviews...", indent=3)
                product_data = rainforest_get({
                    "type": "product",
                    "asin": asin
                })
                if product_data and "product" in product_data:
                    top_reviews = product_data["product"].get("top_reviews", [])
                    for r in top_reviews:
                        body = (r.get("body") or "").strip()
                        if not body: continue
                        score, label = score_text(body)
                        collected.append({
                            "asin":               asin,
                            "reviewer_name":      r.get("profile", {}).get("name", "Anonymous"),
                            "rating":             safe_float(r.get("rating"), 3.0),
                            "title":              r.get("title", ""),
                            "body":               body,
                            "sentiment_score":    score,
                            "sentiment_label":    label,
                            "verified_purchase":  "True",
                            "review_date":        r.get("date", {}).get("raw", ""),
                        })
                break
            else:
                break

        reviews = data.get("reviews", [])
        if not reviews:
            break

        for r in reviews:
            body = (r.get("body") or "").strip()
            if not body or len(body) < 10:
                continue

            score, label = score_text(body)
            collected.append({
                "asin":               asin,
                "reviewer_name":      r.get("profile", {}).get("name", "Anonymous"),
                "rating":             safe_float(r.get("rating"), 3.0),
                "title":              r.get("title", ""),
                "body":               body,
                "sentiment_score":    score,
                "sentiment_label":    label,
                "verified_purchase":  str(r.get("verified_purchase", False)),
                "review_date":        r.get("date", {}).get("raw", ""),
            })

        has_next = bool(data.get("pagination", {}).get("next_page_link"))
        if not has_next or len(collected) >= REVIEWS_PER_PRODUCT:
            break

        page += 1
        time.sleep(REQUEST_DELAY)

    result = collected[:REVIEWS_PER_PRODUCT]
    log(f"{len(result)} real reviews collected", indent=3)
    return result

def save_brand_to_db(brand_name: str, products: list, all_reviews: dict):
    db = SessionLocal()
    try:
        brand = db.query(models.Brand).filter(
            models.Brand.name == brand_name
        ).first()
        
        if not brand:
            prices    = [p["price"] for p in products if p["price"] > 0]
            discounts = [p["discount_percent"] for p in products]
            ratings   = [p["rating"] for p in products if p["rating"] > 0]
            all_scores = [
                r["sentiment_score"]
                for reviews in all_reviews.values()
                for r in reviews
            ]
            total_reviews = sum(len(v) for v in all_reviews.values())
            avg_sentiment = round(sum(all_scores) / len(all_scores), 4) if all_scores else 0.0
            brand = models.Brand(
                name            = brand_name,
                avg_price       = round(sum(prices) / len(prices), 2) if prices else 0.0,
                avg_discount    = round(sum(discounts) / len(discounts), 2) if discounts else 0.0,
                avg_rating      = round(sum(ratings) / len(ratings), 2) if ratings else 0.0,
                total_reviews   = total_reviews,
                sentiment_score = avg_sentiment,
            )
            db.add(brand)
            db.commit()
            db.refresh(brand)
            log(f"Brand saved: {brand_name}", indent=2)
        else:
            log(f"Using existing brand: {brand_name}", indent=2)
        for p in products:
            existing_product = db.query(models.Product).filter(
                models.Product.asin == p["asin"]
            ).first()
            
            if existing_product:
                log(f"Product {p['asin']} already in DB — skipping", indent=3)
                continue

            reviews     = all_reviews.get(p["asin"], [])
            p_scores    = [r["sentiment_score"] for r in reviews]
            p_sentiment = round(sum(p_scores) / len(p_scores), 4) if p_scores else 0.0

            product = models.Product(
                brand_id         = brand.id,
                asin             = p["asin"],
                title            = p["title"],
                price            = p["price"],
                original_price   = p["original_price"],
                discount_percent = p["discount_percent"],
                rating           = p["rating"],
                review_count     = p["review_count"],
                category         = p["category"],
                image_url        = p["image_url"],
                product_url      = p["product_url"],
                sentiment_score  = p_sentiment,
            )
            db.add(product)
            db.commit()
            db.refresh(product)

            for r in reviews:
                db.add(models.Review(
                    product_id        = product.id,
                    asin              = r["asin"],
                    reviewer_name     = r["reviewer_name"],
                    rating            = r["rating"],
                    title             = r["title"],
                    body              = r["body"],
                    sentiment_score   = r["sentiment_score"],
                    sentiment_label   = r["sentiment_label"],
                    verified_purchase = r["verified_purchase"],
                    review_date       = r["review_date"],
                ))

            db.commit()
            log(f"Product: {p['title'][:50]}...", indent=3)
        all_prods = db.query(models.Product).filter(models.Product.brand_id == brand.id).all()
        if all_prods:
            prices    = [p.price for p in all_prods if p.price is not None and p.price > 0]
            discounts = [p.discount_percent for p in all_prods if p.discount_percent is not None]
            ratings   = [p.rating for p in all_prods if p.rating is not None and p.rating > 0]
            all_review_scores = db.query(models.Review.sentiment_score).join(models.Product).filter(
                models.Product.brand_id == brand.id
            ).all()
            scores = [s[0] for s in all_review_scores if s[0] is not None]

            brand.avg_price       = float(round(sum(prices) / len(prices), 2)) if prices else 0.0
            brand.avg_discount    = float(round(sum(discounts) / len(discounts), 2)) if discounts else 0.0
            brand.avg_rating      = float(round(sum(ratings) / len(ratings), 2)) if ratings else 0.0
            brand.total_reviews   = int(len(scores))
            brand.sentiment_score = float(round(sum(scores) / len(scores), 4)) if scores else 0.0
            
            db.commit()
            log(f"Brand metrics updated for {brand_name}", indent=2)

    except Exception as e:
        db.rollback()
        log(f"DB error: {e}", indent=2)
        raise
    finally:
        db.close()

def reset_database():
    log("Resetting database...")
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    log("Database reset complete")


def run_scraper(brands: list):
    print("\n" + "=" * 56)
    print("  BrandRadar — Amazon India Luggage Intelligence")
    print("=" * 56)

    if not API_KEY or API_KEY == "YOUR_API_KEY_HERE":
        print("\nERROR: API key missing!")
        print("   Edit scraper/.env and set:")
        print("   RAINFOREST_API_KEY=your_actual_key\n")
        return

    models.Base.metadata.create_all(bind=engine)

    total_requests = 0
    total_products = 0
    total_reviews  = 0

    db = SessionLocal()
    try:
        for brand in brands:
            brand_obj = db.query(models.Brand).filter(models.Brand.name == brand).first()
            if brand_obj:
                count = db.query(func.count(models.Product.id)).filter(
                    models.Product.brand_id == brand_obj.id
                ).scalar()
                
                if count >= PRODUCTS_PER_BRAND:
                    log(f"{brand} has {count} products — skipping", indent=1)
                    continue
                else:
                    log(f"{brand} only has {count}/{PRODUCTS_PER_BRAND} products — continuing collection", indent=1)

            print(f"\n{'- ' * 28}")
            print(f"  {brand.upper()}")
            print(f"{'- ' * 28}")

            products = search_products(brand)
            total_requests += 1

            if not products:
                log(f"Skipping {brand}", indent=1)
                continue

            all_reviews = {}
            for i, product in enumerate(products, 1):
                existing = db.query(models.Product).filter(models.Product.asin == product["asin"]).first()
                if existing:
                    log(
                        f"[{i}/{len(products)}] Product {product['asin']} already in DB "
                        f"— skipping reviews",
                        indent=1
                    )
                    continue

                log(f"[{i}/{len(products)}]", indent=1)
                reviews = fetch_reviews(product["asin"], product["title"])
                all_reviews[product["asin"]] = reviews
                total_requests += 1
                total_reviews += len(reviews)
                time.sleep(REQUEST_DELAY)

            save_brand_to_db(brand, products, all_reviews)
            total_products += len(products)
            log(f"{brand} complete!", indent=1)
            time.sleep(2)
    finally:
        db.close()

    print("\n" + "=" * 56)
    print("  Done!")
    print(f"  Brands   : {len(brands)}")
    print(f"  Products : {total_products}")
    print(f"  Reviews  : {total_reviews}")
    print(f"  API calls: {total_requests}")
    print(f"  DB file  : luggage_intel.db")
    print("=" * 56 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BrandRadar Scraper")
    parser.add_argument(
        "--brand",
        type=str,
        help="Scrape single brand e.g. --brand Safari"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset DB before scraping"
    )
    args = parser.parse_args()

    if args.reset:
        reset_database()

    brands_to_run = [args.brand] if args.brand else BRANDS
    run_scraper(brands_to_run)
