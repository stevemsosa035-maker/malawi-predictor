"""
Sentiment scorer for Malawi economic news.
Scores each headline as positive, negative or neutral.
Uses keyword matching tuned for Malawi economic context.
"""

import re
from datetime import datetime

# Words that signal BAD economic news
NEGATIVE_KEYWORDS = [
    # Inflation and prices
    "inflation", "price hike", "price increase", "cost of living",
    "fuel price", "rising prices", "expensive", "unaffordable",
    # Currency
    "devaluation", "depreciation", "kwacha weakens", "kwacha falls",
    "forex shortage", "foreign exchange crisis", "currency crisis",
    # Economy
    "recession", "economic crisis", "downturn", "contraction",
    "job losses", "unemployment", "retrenchment", "layoffs",
    "poverty", "hunger", "food insecurity", "famine", "drought",
    # Debt and fiscal
    "debt crisis", "default", "arrears", "budget deficit",
    "imf conditions", "austerity", "tax increase", "new tax",
    # Energy and supply
    "fuel shortage", "power outage", "blackout", "load shedding",
    "escom", "shortage", "supply shortage", "stock out",
    # Political/institutional
    "corruption", "scandal", "fraud", "mismanagement",
    "strike", "protest", "unrest", "crisis",
    # Specific Malawi terms
    "forex", "mra deficit", "rbm", "kwacha depreciation",
]

# Words that signal GOOD economic news
POSITIVE_KEYWORDS = [
    # Growth
    "growth", "gdp growth", "economic growth", "expansion",
    "investment", "foreign investment", "fdi", "development",
    # Currency
    "kwacha strengthens", "kwacha gains", "forex reserves",
    "exchange rate stable", "currency stable",
    # Trade and revenue
    "exports increase", "trade surplus", "revenue growth",
    "tax revenue", "budget surplus", "fiscal surplus",
    # Employment
    "jobs created", "employment", "hiring", "new jobs",
    # Agriculture
    "good harvest", "bumper harvest", "food surplus",
    "tobacco sales", "maize production",
    # IMF/World Bank positive
    "imf support", "world bank loan", "aid", "grant",
    "debt relief", "debt cancellation",
    # General positive
    "improved", "increase", "rises", "record", "success",
    "progress", "achievement", "reform",
]

# Words that increase negativity weight
INTENSIFIERS = [
    "severe", "critical", "alarming", "worst", "crisis",
    "historic", "record high", "skyrockets", "collapses",
]


def score_headline(headline):
    """
    Score a single headline.
    Returns dict with:
        - sentiment: positive / negative / neutral
        - score: -1.0 to +1.0
        - negative_hits: which negative words found
        - positive_hits: which positive words found
    """
    text = headline.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    negative_hits = [kw for kw in NEGATIVE_KEYWORDS if kw in text]
    positive_hits = [kw for kw in POSITIVE_KEYWORDS if kw in text]
    intensifier_hits = [kw for kw in INTENSIFIERS if kw in text]

    neg_score = len(negative_hits) + (len(intensifier_hits) * 0.5)
    pos_score = len(positive_hits)

    total = neg_score + pos_score
    if total == 0:
        return {
            "sentiment": "neutral",
            "score": 0.0,
            "negative_hits": [],
            "positive_hits": [],
        }

    raw = (pos_score - neg_score) / total
    score = round(raw, 3)

    if score > 0.1:
        sentiment = "positive"
    elif score < -0.1:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    return {
        "sentiment": sentiment,
        "score": score,
        "negative_hits": negative_hits,
        "positive_hits": positive_hits,
    }


def score_news_feed(df):
    """
    Score all headlines in a news DataFrame.
    Adds sentiment and score columns.
    Returns updated DataFrame and summary stats.
    """
    if df is None or df.empty:
        return df, {"negative_pct": 50, "positive_pct": 0, "neutral_pct": 50}

    results = []
    for _, row in df.iterrows():
        title = str(row.get("title", ""))
        result = score_headline(title)
        results.append(result)

    df = df.copy()
    df["sentiment"] = [r["sentiment"] for r in results]
    df["sentiment_score"] = [r["score"] for r in results]

    total = len(df)
    neg = (df["sentiment"] == "negative").sum()
    pos = (df["sentiment"] == "positive").sum()
    neu = (df["sentiment"] == "neutral").sum()

    summary = {
        "negative_pct": round((neg / total) * 100) if total > 0 else 0,
        "positive_pct": round((pos / total) * 100) if total > 0 else 0,
        "neutral_pct":  round((neu / total) * 100) if total > 0 else 0,
        "total":  total,
        "negative": int(neg),
        "positive": int(pos),
        "neutral":  int(neu),
        "avg_score": round(float(df["sentiment_score"].mean()), 3),
    }

    return df, summary


def get_sentiment_emoji(sentiment):
    emojis = {
        "positive": "\U0001f7e2",
        "negative": "\U0001f534",
        "neutral":  "\u26aa",
    }
    return emojis.get(sentiment, "\u26aa")


if __name__ == "__main__":
    print("Testing Sentiment Scorer...")
    print("")

    import sys, os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from data.news_collector import fetch_all_news

    news_df = fetch_all_news()

    if news_df.empty:
        print("No news available to score.")
    else:
        scored_df, summary = score_news_feed(news_df)
        print(f"Scored {summary['total']} headlines:")
        print(f"  Positive: {summary['positive']} ({summary['positive_pct']}%)")
        print(f"  Negative: {summary['negative']} ({summary['negative_pct']}%)")
        print(f"  Neutral:  {summary['neutral']} ({summary['neutral_pct']}%)")
        print(f"  Avg score: {summary['avg_score']} (-1=very negative, +1=very positive)")
        print("")
        print("Headline scores:")
        for _, row in scored_df.iterrows():
            emoji = get_sentiment_emoji(row["sentiment"])
            print(f"  {emoji} [{row['sentiment']}] {row['title'][:70]}")
