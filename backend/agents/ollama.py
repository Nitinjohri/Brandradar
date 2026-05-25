import requests
import json
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"

analyzer = SentimentIntensityAnalyzer()


def score_review(text: str) -> dict:
    scores = analyzer.polarity_scores(text)
    compound = scores["compound"]

    if compound >= 0.05:
        label = "positive"
    elif compound <= -0.05:
        label = "negative"
    else:
        label = "neutral"

    return {"score": compound, "label": label}


def score_reviews_bulk(reviews: list[str]) -> float:
    if not reviews:
        return 0.0
    scores = [analyzer.polarity_scores(r)["compound"] for r in reviews]
    return round(sum(scores) / len(scores), 4)


def call_ollama(prompt: str) -> str:
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except requests.RequestException as e:
        return f"Ollama error: {str(e)}"


def extract_themes(brand_name: str, reviews: list[str], sentiment: str) -> list[str]:
    sample = reviews[:30]
    reviews_text = "\n".join([f"- {r}" for r in sample])

    prompt = f"""
You are analyzing customer reviews for the luggage brand "{brand_name}" on Amazon India.

Here are {sentiment} customer reviews:
{reviews_text}

List the top 5 recurring {sentiment} themes customers mention.
Return ONLY a JSON array of 5 short theme strings.
Example: ["wheels broke easily", "zipper quality poor", "handle loose"]
Return only the JSON array, nothing else.
"""
    raw = call_ollama(prompt)

    try:
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        themes = json.loads(raw)
        if isinstance(themes, list):
            return [str(t) for t in themes][:5]
        return [raw]
    except Exception:
        return ["Could not extract themes"]


def generate_brand_insights(
    brand_name: str,
    avg_price: float,
    avg_discount: float,
    avg_rating: float,
    sentiment_score: float,
    top_complaints: list[str],
    top_praises: list[str]
) -> str:

    prompt = f"""
You are a competitive intelligence analyst for Amazon India luggage market.

Brand: {brand_name}
Average Price: ₹{avg_price}
Average Discount: {avg_discount}%
Average Rating: {avg_rating}/5
Sentiment Score: {sentiment_score} (scale -1 to +1)
Top Customer Complaints: {', '.join(top_complaints)}
Top Customer Praises: {', '.join(top_praises)}

Give 3 non-obvious business insights about this brand.
Focus on: hidden quality issues, pricing strategy red flags, or genuine strengths.
Keep each insight to 1-2 sentences.
Return ONLY a JSON array of 3 insight strings.
"""
    raw = call_ollama(prompt)

    try:
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        insights = json.loads(raw)
        if isinstance(insights, list):
            return [str(i['insight']) if isinstance(i, dict) and 'insight' in i else str(i) for i in insights]
        return [raw]
    except Exception:
        return [raw]


def generate_market_insights(brands_summary: list[dict]) -> list[dict]:
    summary_text = "\n".join([
        f"- {b['name']}: price ₹{b['avg_price']}, discount {b['avg_discount']}%, "
        f"rating {b['avg_rating']}, sentiment {b['sentiment_score']}"
        for b in brands_summary
    ])

    prompt = f"""
You are a competitive intelligence analyst for Amazon India luggage market.

Here is a summary of luggage brands:
{summary_text}

Generate 5 non-obvious market insights.
For each insight, identify which specific brand it primarily concerns.

Return ONLY a JSON array of 5 objects.
Example: [{{"brand": "Safari", "insight": "..."}}, {{"brand": "VIP", "insight": "..."}}]
Return only the JSON array, nothing else.
"""
    raw = call_ollama(prompt)

    try:
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        insights = json.loads(raw)
        if isinstance(insights, list):
            final_insights = []
            for i in insights:
                if isinstance(i, str) and (i.strip().startswith('{') or i.strip().startswith('[')):
                    try:
                        parsed = json.loads(i)
                        if isinstance(parsed, dict):
                            i = parsed
                    except Exception:
                        pass

                if isinstance(i, dict) and 'brand' in i and 'insight' in i:
                    final_insights.append(i)
                elif isinstance(i, str):
                    brand = "Market"
                    for b in brands_summary:
                        if b['name'].lower() in i.lower():
                            brand = b['name']
                            break
                    final_insights.append({"brand": brand, "insight": i})
            return final_insights[:5]
        return [{"brand": "Market", "insight": str(raw)}]
    except Exception:
        return [{"brand": "Market", "insight": str(raw)}]