"""
Investment Signals for Malawi Economic Predictor.
Translates economic conditions into specific
investment decisions and recommendations.
"""


def generate_signals(
    inflation=None,
    gdp_growth=None,
    government_debt=None,
    current_account=None,
    mwk_per_usd=None,
    devaluation_score=None,
):
    """
    Takes all economic indicators and returns
    a list of investment signals with actions.

    Each signal has:
        - asset: what investment type
        - action: BUY / HOLD / AVOID / HEDGE
        - reason: plain English explanation
        - confidence: HIGH / MEDIUM / LOW
    """
    signals = []

    # ── USD / Foreign Currency ───────────────────────────────────
    if mwk_per_usd and devaluation_score:
        if devaluation_score >= 65:
            signals.append({
                "asset": "USD / Foreign Currency",
                "action": "BUY",
                "reason": f"Devaluation risk is {devaluation_score}/100. Holding USD protects your wealth if MWK weakens further. Current rate: 1 USD = {mwk_per_usd:,.0f} MWK.",
                "confidence": "HIGH",
                "emoji": "\U0001f4b5"
            })
        elif devaluation_score >= 45:
            signals.append({
                "asset": "USD / Foreign Currency",
                "action": "HOLD",
                "reason": f"Moderate devaluation risk at {devaluation_score}/100. Keep some savings in USD as a hedge but do not convert everything.",
                "confidence": "MEDIUM",
                "emoji": "\U0001f4b5"
            })
        else:
            signals.append({
                "asset": "USD / Foreign Currency",
                "action": "HOLD",
                "reason": "Low devaluation risk. No urgent need to convert to foreign currency.",
                "confidence": "MEDIUM",
                "emoji": "\U0001f4b5"
            })

    # ── Government Bonds / Treasury Bills ───────────────────────
    if inflation and government_debt:
        if inflation > 20 and government_debt > 70:
            signals.append({
                "asset": "Government Bonds / T-Bills",
                "action": "AVOID",
                "reason": f"Inflation at {inflation}% erodes bond returns. Government debt at {government_debt}% of GDP raises default risk. Real returns are likely negative.",
                "confidence": "HIGH",
                "emoji": "\U0001f4dc"
            })
        elif inflation > 15:
            signals.append({
                "asset": "Government Bonds / T-Bills",
                "action": "HOLD",
                "reason": f"Short-term T-Bills may still beat inflation if rates are above {inflation}%. Check current RBM T-Bill rates before committing.",
                "confidence": "MEDIUM",
                "emoji": "\U0001f4dc"
            })
        else:
            signals.append({
                "asset": "Government Bonds / T-Bills",
                "action": "BUY",
                "reason": "Inflation under control. Government bonds offer reasonable real returns.",
                "confidence": "MEDIUM",
                "emoji": "\U0001f4dc"
            })

    # ── Real Estate ──────────────────────────────────────────────
    if inflation and gdp_growth:
        if inflation > 20 and gdp_growth > 0:
            signals.append({
                "asset": "Real Estate / Property",
                "action": "BUY",
                "reason": f"High inflation at {inflation}% increases property values in nominal terms. Real assets protect wealth during inflationary periods. GDP still growing at {gdp_growth}%.",
                "confidence": "HIGH",
                "emoji": "\U0001f3e0"
            })
        elif gdp_growth < 1:
            signals.append({
                "asset": "Real Estate / Property",
                "action": "HOLD",
                "reason": f"GDP growth too slow at {gdp_growth}% to drive strong property demand. Hold existing property but delay new purchases.",
                "confidence": "MEDIUM",
                "emoji": "\U0001f3e0"
            })
        else:
            signals.append({
                "asset": "Real Estate / Property",
                "action": "BUY",
                "reason": f"Stable conditions. Property remains a good long-term store of value in Malawi.",
                "confidence": "MEDIUM",
                "emoji": "\U0001f3e0"
            })

    # ── Agricultural Investment ──────────────────────────────────
    if inflation and current_account:
        if inflation > 15 and current_account < -10:
            signals.append({
                "asset": "Agriculture / Agribusiness",
                "action": "BUY",
                "reason": f"Food price inflation and a large trade deficit of {current_account}% of GDP mean agricultural production is highly valuable. Export crops earn foreign currency.",
                "confidence": "HIGH",
                "emoji": "\U0001f33d"
            })
        else:
            signals.append({
                "asset": "Agriculture / Agribusiness",
                "action": "HOLD",
                "reason": "Agriculture remains a stable sector in Malawi. Monitor rainfall and tobacco prices.",
                "confidence": "MEDIUM",
                "emoji": "\U0001f33d"
            })

    # ── Stock Market / Malawi Stock Exchange ─────────────────────
    if gdp_growth and inflation:
        if gdp_growth < 2 and inflation > 20:
            signals.append({
                "asset": "Malawi Stock Exchange (MSE)",
                "action": "AVOID",
                "reason": f"Stagflation conditions — low growth at {gdp_growth}% with high inflation at {inflation}% — are bad for corporate earnings and stock valuations.",
                "confidence": "HIGH",
                "emoji": "\U0001f4c9"
            })
        elif gdp_growth >= 4 and inflation < 15:
            signals.append({
                "asset": "Malawi Stock Exchange (MSE)",
                "action": "BUY",
                "reason": f"Good growth at {gdp_growth}% with manageable inflation at {inflation}%. Corporate profits likely rising.",
                "confidence": "HIGH",
                "emoji": "\U0001f4c8"
            })
        else:
            signals.append({
                "asset": "Malawi Stock Exchange (MSE)",
                "action": "HOLD",
                "reason": "Mixed conditions. Selective stock picking may work but broad market entry is risky.",
                "confidence": "LOW",
                "emoji": "\U0001f4ca"
            })

    # ── Cash (MWK savings) ───────────────────────────────────────
    if inflation:
        if inflation > 20:
            signals.append({
                "asset": "Cash savings (MWK)",
                "action": "AVOID",
                "reason": f"Holding idle MWK cash at {inflation}% inflation means your money loses value fast. Move cash into assets or foreign currency.",
                "confidence": "HIGH",
                "emoji": "\U0001f4b0"
            })
        elif inflation > 10:
            signals.append({
                "asset": "Cash savings (MWK)",
                "action": "HOLD",
                "reason": f"Inflation at {inflation}% is elevated. Keep only emergency cash in MWK. Put the rest to work.",
                "confidence": "MEDIUM",
                "emoji": "\U0001f4b0"
            })
        else:
            signals.append({
                "asset": "Cash savings (MWK)",
                "action": "HOLD",
                "reason": "Inflation manageable. Cash savings are acceptable short term.",
                "confidence": "LOW",
                "emoji": "\U0001f4b0"
            })

    return signals


def get_action_color(action):
    colors = {
        "BUY":   "green",
        "HOLD":  "orange",
        "AVOID": "red",
        "HEDGE": "blue",
    }
    return colors.get(action, "grey")


def get_action_emoji(action):
    emojis = {
        "BUY":   "\U0001f7e2",
        "HOLD":  "\U0001f7e1",
        "AVOID": "\U0001f534",
        "HEDGE": "\U0001f535",
    }
    return emojis.get(action, "")


if __name__ == "__main__":
    print("Testing Investment Signals...")
    print("")

    import sys, os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from data.imf_collector import fetch_all, get_current_value
    from data.forex_collector import fetch_latest_rate
    from data.devaluation_risk import calculate_devaluation_risk

    imf = fetch_all()
    forex = fetch_latest_rate()

    inflation, _    = get_current_value("Inflation Rate (%)", imf)
    gdp, _          = get_current_value("GDP Growth (%)", imf)
    debt, _         = get_current_value("Government Debt (% GDP)", imf)
    ca, _           = get_current_value("Current Account (% GDP)", imf)
    fx              = forex.get("rate")

    risk = calculate_devaluation_risk(
        inflation=inflation, mwk_per_usd=fx,
        gdp_growth=gdp, government_debt=debt,
        current_account=ca
    )

    signals = generate_signals(
        inflation=inflation,
        gdp_growth=gdp,
        government_debt=debt,
        current_account=ca,
        mwk_per_usd=fx,
        devaluation_score=risk["score"]
    )

    print(f"Generated {len(signals)} investment signals:")
    print("")
    for s in signals:
        print(f"  {s['action']} — {s['asset']}")
        print(f"    {s['reason']}")
        print("")
