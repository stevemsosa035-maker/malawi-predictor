"""
Devaluation Risk Score for Malawi Kwacha.
Combines 6 economic indicators into one risk score 0-100.
0 = very safe, 100 = devaluation almost certain.
"""


def score_inflation(inflation):
    """
    High inflation pressures central bank to devalue.
    Above 20% is critical for Malawi.
    """
    if inflation is None:
        return 50
    if inflation >= 30:   return 100
    if inflation >= 25:   return 85
    if inflation >= 20:   return 70
    if inflation >= 15:   return 55
    if inflation >= 10:   return 35
    if inflation >= 5:    return 15
    return 5


def score_exchange_rate(mwk_per_usd):
    """
    How weak the kwacha already is.
    The weaker it is, the more pressure to formally devalue.
    """
    if mwk_per_usd is None:
        return 50
    if mwk_per_usd >= 2000:  return 100
    if mwk_per_usd >= 1700:  return 85
    if mwk_per_usd >= 1400:  return 65
    if mwk_per_usd >= 1000:  return 45
    if mwk_per_usd >= 700:   return 25
    return 10


def score_gdp_growth(gdp):
    """
    Slow or negative growth means less ability to
    earn foreign currency and defend the exchange rate.
    """
    if gdp is None:
        return 50
    if gdp < 0:    return 90
    if gdp < 1:    return 75
    if gdp < 2:    return 60
    if gdp < 3:    return 45
    if gdp < 5:    return 25
    return 10


def score_government_debt(debt):
    """
    High debt means government may pressure RBM
    to devalue to reduce real debt burden.
    """
    if debt is None:
        return 50
    if debt >= 90:   return 95
    if debt >= 75:   return 80
    if debt >= 60:   return 65
    if debt >= 50:   return 45
    if debt >= 35:   return 25
    return 10


def score_current_account(ca):
    """
    Large current account deficit means more USD
    going out than coming in. Drains reserves.
    """
    if ca is None:
        return 50
    if ca <= -20:   return 95
    if ca <= -15:   return 80
    if ca <= -10:   return 65
    if ca <= -5:    return 45
    if ca <= 0:     return 25
    return 10


def score_news_sentiment(negative_pct):
    """
    What percentage of economic headlines are negative.
    High negativity signals market expects devaluation.
    negative_pct is 0-100.
    """
    if negative_pct is None:
        return 50
    if negative_pct >= 80:  return 90
    if negative_pct >= 60:  return 70
    if negative_pct >= 40:  return 50
    if negative_pct >= 20:  return 30
    return 15


def calculate_devaluation_risk(
    inflation=None,
    mwk_per_usd=None,
    gdp_growth=None,
    government_debt=None,
    current_account=None,
    news_negative_pct=None,
):
    """
    Main function. Takes all indicators and returns
    a risk score 0-100 with full breakdown.

    Weights reflect how much each factor matters
    for Malawi specifically.
    """
    components = {
        "Inflation":        (score_inflation(inflation),        0.25),
        "Exchange Rate":    (score_exchange_rate(mwk_per_usd),  0.20),
        "GDP Growth":       (score_gdp_growth(gdp_growth),      0.20),
        "Government Debt":  (score_government_debt(government_debt), 0.15),
        "Current Account":  (score_current_account(current_account), 0.15),
        "News Sentiment":   (score_news_sentiment(news_negative_pct), 0.05),
    }

    total_score = sum(score * weight for score, weight in components.values())
    total_score = round(total_score, 1)

    if total_score >= 75:
        level = "CRITICAL"
        color = "red"
        message = "Conditions strongly favour a devaluation event."
    elif total_score >= 55:
        level = "HIGH"
        color = "orange"
        message = "Significant devaluation pressure building."
    elif total_score >= 35:
        level = "MODERATE"
        color = "yellow"
        message = "Some risk. Monitor key indicators closely."
    else:
        level = "LOW"
        color = "green"
        message = "Conditions do not strongly favour devaluation."

    return {
        "score": total_score,
        "level": level,
        "color": color,
        "message": message,
        "components": {
            name: {"score": score, "weight": weight}
            for name, (score, weight) in components.items()
        },
        "inputs": {
            "inflation": inflation,
            "mwk_per_usd": mwk_per_usd,
            "gdp_growth": gdp_growth,
            "government_debt": government_debt,
            "current_account": current_account,
            "news_negative_pct": news_negative_pct,
        }
    }


def get_risk_label(score):
    """Quick label for any score."""
    if score >= 75: return "\U0001f534 CRITICAL"
    if score >= 55: return "\U0001f7e0 HIGH"
    if score >= 35: return "\U0001f7e1 MODERATE"
    return "\U0001f7e2 LOW"


if __name__ == "__main__":
    print("Testing Devaluation Risk Score with sentiment...")
    print("")

    import sys, os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from data.imf_collector import fetch_all, get_current_value
    from data.forex_collector import fetch_latest_rate
    from data.news_collector import fetch_all_news
    from data.sentiment_scorer import score_news_feed

    imf   = fetch_all()
    forex = fetch_latest_rate()
    news  = fetch_all_news()

    inflation, _ = get_current_value("Inflation Rate (%)", imf)
    gdp, _       = get_current_value("GDP Growth (%)", imf)
    debt, _      = get_current_value("Government Debt (% GDP)", imf)
    ca, _        = get_current_value("Current Account (% GDP)", imf)
    fx           = forex.get("rate")

    _, sentiment_summary = score_news_feed(news)
    neg_pct = sentiment_summary["negative_pct"]

    print(f"News sentiment: {neg_pct}% negative headlines")
    print("")

    result = calculate_devaluation_risk(
        inflation=inflation,
        mwk_per_usd=fx,
        gdp_growth=gdp,
        government_debt=debt,
        current_account=ca,
        news_negative_pct=neg_pct,
    )

    print(f"DEVALUATION RISK SCORE: {result['score']} / 100")
    print(f"Level: {result['level']}")
    print(f"Message: {result['message']}")
    print("")
    print("Component breakdown:")
    for name, data in result["components"].items():
        print(f"  {name}: {data['score']} (weight {data['weight']})")
