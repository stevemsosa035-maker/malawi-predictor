"""
News collector for Malawi economic news.
Scrapes Nyasa Times and Malawi24 for headlines.
Tags each headline with economic keywords.
"""

import requests
import feedparser
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup


ECONOMIC_KEYWORDS = [
    "inflation", "kwacha", "forex", "exchange rate", "interest rate",
    "reserve bank", "rbm", "economy", "economic", "gdp", "debt",
    "budget", "tax", "import", "export", "fuel", "price", "cost",
    "investment", "devaluation", "depreciation", "imf", "world bank",
    "malawi revenue", "mra", "ministry of finance", "treasury",
    "tobacco", "maize", "harvest", "drought", "food security",
    "electricity", "escom", "power", "mpc", "monetary policy",
]


RSS_FEEDS = {
    "Nyasa Times":     "https://www.nyasatimes.com/feed/",
    "Malawi24":        "https://malawi24.com/feed/",
    "Times of Malawi": "https://www.times.mw/feed/",
    "Malawi Voice":    "https://www.malawivoice.com/feed/",
    "Zodiak Online":   "https://www.zodiakmalawi.com/feed",
    "MBC News":        "https://www.mbcmalawi.mw/feed/",
}

def fetch_rbm_statements():
    """
    Scrape RBM press statements from their website.
    Returns list of articles.
    """
    articles = []
    try:
        url = "https://www.rbm.mw/Publications/MPCPressStatements/"
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(resp.text, "lxml")
        for link in soup.find_all("a", href=True):
            title = link.get_text(strip=True)
            href = link["href"]
            if title and len(title) > 10:
                articles.append({
                    "source": "RBM",
                    "title": title,
                    "link": href,
                    "date": str(datetime.now()),
                    "is_economic": True
                })
        print(f"OK: RBM — {len(articles)} statements found")
    except Exception as e:
        print(f"FAILED: RBM — {e}")
    return articles[:10]



def is_economic(headline):
    """
    Returns True if headline contains any economic keyword.
    """
    text = headline.lower()
    return any(kw in text for kw in ECONOMIC_KEYWORDS)


def fetch_rss_feed(name, url):
    """
    Pull articles from an RSS feed.
    Returns list of dicts with title, link, date.
    """
    articles = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = entry.get("title", "").strip()
            link  = entry.get("link", "")
            date  = entry.get("published", str(datetime.now()))
            articles.append({
                "source": name,
                "title":  title,
                "link":   link,
                "date":   date,
                "is_economic": is_economic(title)
            })
        print(f"OK: {name} — {len(articles)} articles fetched")
    except Exception as e:
        print(f"FAILED: {name} — {e}")
    return articles


def fetch_all_news():
    """
    Fetch from all sources and return a combined DataFrame.
    """
    all_articles = []
    for name, url in RSS_FEEDS.items():
        articles = fetch_rss_feed(name, url)
        all_articles.extend(articles)

    # Add RBM press statements
    all_articles.extend(fetch_rbm_statements())

    if not all_articles:
        print("No articles retrieved from any source")
        return pd.DataFrame()

    df = pd.DataFrame(all_articles)
    df = df.drop_duplicates(subset=["title"])
    df = df.sort_values("date", ascending=False).reset_index(drop=True)
    return df


def fetch_economic_news_only():
    """
    Return only headlines that match economic keywords.
    This is what the dashboard will display.
    """
    df = fetch_all_news()
    if df.empty:
        return df
    economic = df[df["is_economic"] == True].reset_index(drop=True)
    return economic


if __name__ == "__main__":
    print("Testing News collector...")
    print("")

    df = fetch_all_news()

    if not df.empty:
        total = len(df)
        economic = df["is_economic"].sum()
        print(f"")
        print(f"Total articles: {total}")
        print(f"Economic articles: {economic}")
        print(f"")
        print("Latest economic headlines:")
        econ_df = df[df["is_economic"] == True].head(10)
        for _, row in econ_df.iterrows():
            print(f"  [{row['source']}] {row['title']}")
    else:
        print("No articles found — check internet connection")
