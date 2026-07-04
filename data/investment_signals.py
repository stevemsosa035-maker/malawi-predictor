"""
Investment Signals — rate-aware sector rotation engine.
"""


def generate_signals(
    inflation=None,
    gdp_growth=None,
    government_debt=None,
    current_account=None,
    mwk_per_usd=None,
    devaluation_score=None,
    rate_env=None,
):
    signals = []
    policy_rate = rate_env["current_rate"] if rate_env else 26.0
    lending_rate = rate_env["estimated_lending_rate"] if rate_env else 37.0
    cycle = rate_env["cycle_phase"] if rate_env else "PLATEAU"
    tbill_364 = rate_env["tbill_rates"]["364-day"]["rate"] if rate_env else 28.0
    tbill_91  = rate_env["tbill_rates"]["91-day"]["rate"]  if rate_env else 26.5
    real_rate = (lending_rate - inflation) if inflation else None

    # USD
    if mwk_per_usd and devaluation_score:
        if devaluation_score >= 65:
            signals.append({"asset": "USD / Foreign Currency", "action": "BUY",
                "reason": f"Devaluation risk at {devaluation_score}/100. Policy rate cut to {policy_rate}% — kwacha may weaken further. Hold USD.",
                "confidence": "HIGH", "emoji": "\U0001f4b5"})
        else:
            signals.append({"asset": "USD / Foreign Currency", "action": "HOLD",
                "reason": f"Moderate risk. Policy rate at {policy_rate}% still supports kwacha. Monitor next MPC decision.",
                "confidence": "MEDIUM", "emoji": "\U0001f4b5"})

    # Bonds
    if cycle in ["EARLY_EASING", "DEEP_EASING"]:
        signals.append({"asset": "Government Bonds / T-Bills", "action": "BUY",
            "reason": f"Rate cutting cycle started ({policy_rate}%). Bond prices rise as rates fall. Buy 364-day T-bills at {tbill_364}% now before further cuts compress yields.",
            "confidence": "HIGH", "emoji": "\U0001f4dc"})
    elif inflation and inflation > 20:
        signals.append({"asset": "Government Bonds / T-Bills", "action": "AVOID",
            "reason": f"Inflation at {inflation}% with policy rate {policy_rate}%. Real bond returns negative. Avoid.",
            "confidence": "HIGH", "emoji": "\U0001f4dc"})
    else:
        signals.append({"asset": "Government Bonds / T-Bills", "action": "HOLD",
            "reason": f"91-day T-bill at {tbill_91}%. Check if rate exceeds inflation before committing.",
            "confidence": "MEDIUM", "emoji": "\U0001f4dc"})

    # Banks
    if cycle in ["EARLY_EASING", "DEEP_EASING"]:
        signals.append({"asset": "Commercial Banks (NICO, NBS, FDH)", "action": "HOLD",
            "reason": f"Banks have fat spreads ({lending_rate:.0f}% lending vs {policy_rate}% policy). But rate cuts will compress margins. Hold — watch next MPC.",
            "confidence": "MEDIUM", "emoji": "\U0001f3e6"})
    else:
        signals.append({"asset": "Commercial Banks (NICO, NBS, FDH)", "action": "BUY",
            "reason": f"High rate environment ({lending_rate:.0f}% lending rate) = fat spreads = strong net interest income. Banks printing money.",
            "confidence": "HIGH", "emoji": "\U0001f3e6"})

    # Real Estate
    if inflation and gdp_growth:
        if cycle == "EARLY_EASING" and inflation > 15:
            signals.append({"asset": "Real Estate / Property", "action": "BUY",
                "reason": f"Rate cuts starting — financing gets cheaper. Buy before lending rates fall and demand rises. Inflation {inflation}% still inflating asset values.",
                "confidence": "HIGH", "emoji": "\U0001f3e0"})
        elif real_rate and real_rate > 8:
            signals.append({"asset": "Real Estate / Property", "action": "HOLD",
                "reason": f"Real lending rate {real_rate:.1f}% makes leveraged property expensive. Cash buyers fine — avoid debt-financed purchases.",
                "confidence": "MEDIUM", "emoji": "\U0001f3e0"})
        else:
            signals.append({"asset": "Real Estate / Property", "action": "BUY",
                "reason": f"Property protects against {inflation}% inflation. GDP {gdp_growth}% supports demand.",
                "confidence": "MEDIUM", "emoji": "\U0001f3e0"})

    # Agriculture
    if inflation and current_account:
        signals.append({"asset": "Agriculture / Agribusiness", "action": "BUY",
            "reason": f"Agriculture is rate-insensitive — driven by rainfall and commodity prices, not credit. Trade deficit {current_account}% of GDP means export crops earn scarce forex. Inflation {inflation}% makes local production valuable. Rate-immune sector.",
            "confidence": "HIGH", "emoji": "\U0001f33d"})

    # Manufacturing
    if real_rate and real_rate > 5:
        signals.append({"asset": "Manufacturing / Capital-Intensive", "action": "AVOID",
            "reason": f"Real lending rate {real_rate:.1f}% destroys margins for businesses that borrow to operate. Avoid until rates fall further.",
            "confidence": "HIGH", "emoji": "\U0001f3ed"})
    else:
        signals.append({"asset": "Manufacturing / Capital-Intensive", "action": "HOLD",
            "reason": "Borrowing costs manageable. Watch rate trajectory.",
            "confidence": "LOW", "emoji": "\U0001f3ed"})

    # MSE
    if gdp_growth and inflation:
        if cycle == "EARLY_EASING" and gdp_growth > 2:
            signals.append({"asset": "Malawi Stock Exchange (MSE)", "action": "BUY",
                "reason": f"Early rate cut cycle with GDP {gdp_growth}% is textbook equity entry. Rate cuts lower discount rates — valuations expand. Target low-debt, cash-rich companies.",
                "confidence": "HIGH", "emoji": "\U0001f4c8"})
        elif gdp_growth < 2 and inflation > 20:
            signals.append({"asset": "Malawi Stock Exchange (MSE)", "action": "AVOID",
                "reason": f"Stagflation — {gdp_growth}% growth with {inflation}% inflation crushes earnings. Lending at {lending_rate:.0f}% destroys leveraged companies.",
                "confidence": "HIGH", "emoji": "\U0001f4c9"})
        else:
            signals.append({"asset": "Malawi Stock Exchange (MSE)", "action": "HOLD",
                "reason": "Mixed signals. Favour low-debt, forex-earning companies.",
                "confidence": "LOW", "emoji": "\U0001f4ca"})

    # Cash
    if inflation:
        if inflation > 20:
            signals.append({"asset": "Cash savings (MWK)", "action": "AVOID",
                "reason": f"Inflation {inflation}% destroys idle cash. Real return on MWK deposits is negative. Move to T-bills, USD or real assets.",
                "confidence": "HIGH", "emoji": "\U0001f4b0"})
        else:
            signals.append({"asset": "Cash savings (MWK)", "action": "HOLD",
                "reason": "Inflation manageable. Short-term MWK deposits acceptable.",
                "confidence": "LOW", "emoji": "\U0001f4b0"})

    return signals


def get_action_color(action):
    return {"BUY": "green", "HOLD": "orange", "AVOID": "red", "HEDGE": "blue"}.get(action, "grey")


def get_action_emoji(action):
    return {"BUY": "\U0001f7e2", "HOLD": "\U0001f7e1", "AVOID": "\U0001f534", "HEDGE": "\U0001f535"}.get(action, "")
