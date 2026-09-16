#!/usr/bin/env python3
"""Conditional betting arithmetic; no retrieval or probability estimation."""

import argparse
import json
import math


def finite(value, name):
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


def decimal_odds(value):
    finite(value, "odds")
    if value <= 1:
        raise ValueError("decimal odds must be greater than 1")
    return value


def probability(value):
    finite(value, "probability")
    if not 0 <= value <= 1:
        raise ValueError("probabilities must be between 0 and 1")
    return value


def probability_vector(values):
    values = [probability(value) for value in values]
    if not math.isclose(math.fsum(values), 1, rel_tol=0, abs_tol=1e-9):
        raise ValueError("mutually exclusive outcome probabilities must sum to 1")
    return values


def stake_value(value):
    finite(value, "stake")
    if value < 0:
        raise ValueError("stake cannot be negative")
    return value


def market(odds):
    if len(odds) < 2:
        raise ValueError("a complete market needs at least two outcomes")
    implied = [1 / decimal_odds(value) for value in odds]
    total = math.fsum(implied)
    return {
        "assumption": "one complete exclusive outcome set, same bookmaker and time",
        "raw_implied_probabilities": implied,
        "overround": total - 1,
        "normalized_market_benchmark": [value / total for value in implied],
        "push_note": "for push markets, benchmarks are conditional on no push",
    }


def single(odds, win, push=0, stake=1, kelly_fraction=None):
    odds, win, push = decimal_odds(odds), probability(win), probability(push)
    stake = stake_value(stake)
    if win + push > 1:
        raise ValueError("win plus push probability cannot exceed 1")
    loss = max(0, 1 - win - push)
    ev = finite(win * (odds - 1) - loss, "expected return")
    result = {
        "assumed_probabilities": {"win": win, "push": push, "loss": loss},
        "odds": odds,
        "break_even_win_probability_at_assumed_push_rate": (1 - push) / odds,
        "model_fair_odds": (1 - push) / win if win > 0 else None,
        "expected_net_roi": ev,
        "expected_net_profit": finite(stake * ev, "expected profit"),
        "full_win_gross_return": finite(stake * odds, "gross return"),
        "full_win_net_profit": finite(stake * (odds - 1), "net profit"),
    }
    if kelly_fraction is not None:
        probability(kelly_fraction)
        denominator = (odds - 1) * (win + loss)
        full = max(0, min(1, ev / denominator)) if denominator else 0
        result["model_full_kelly_fraction"] = full
        result["model_scaled_kelly_fraction"] = full * kelly_fraction
        result["kelly_note"] = "conditional model allocation; apply exposure limits separately"
    return result


def parlay(odds, probabilities=None, assume_independent=False, stake=1):
    if len(odds) < 2:
        raise ValueError("a parlay needs at least two legs")
    stake = stake_value(stake)
    combined = finite(math.prod(decimal_odds(value) for value in odds), "combined odds")
    result = {
        "assumption": "standard unboosted binary ticket; no pushes or partial outcomes",
        "indicative_combined_odds": combined,
        "full_win_break_even_probability": 1 / combined,
        "full_win_gross_return": finite(stake * combined, "gross return"),
        "full_win_net_profit": finite(stake * (combined - 1), "net profit"),
    }
    if probabilities is not None:
        if not assume_independent:
            raise ValueError("probability multiplication requires --assume-independent")
        if len(probabilities) != len(odds):
            raise ValueError("provide exactly one probability per leg")
        joint = math.prod(probability(value) for value in probabilities)
        ev = finite(joint * combined - 1, "expected return")
        result.update({
            "independence_assumed": True,
            "assumed_joint_win_probability": joint,
            "assumed_ticket_loss_probability": 1 - joint,
            "expected_net_roi": ev,
            "expected_net_profit": finite(stake * ev, "expected profit"),
        })
    return result


def settlement(odds, probabilities, stake=1):
    odds, stake = decimal_odds(odds), stake_value(stake)
    if len(probabilities) != 5:
        raise ValueError("provide full win, half win, push, half loss, full loss probabilities")
    probabilities = probability_vector(probabilities)
    returns = [odds - 1, (odds - 1) / 2, 0, -0.5, -1]
    ev = finite(math.fsum(p * r for p, r in zip(probabilities, returns)), "expected return")
    return {
        "outcome_order": ["full_win", "half_win", "push", "half_loss", "full_loss"],
        "assumed_probabilities": probabilities,
        "net_returns_per_unit": returns,
        "expected_net_roi": ev,
        "expected_net_profit": finite(stake * ev, "expected profit"),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    market_parser = sub.add_parser("market")
    market_parser.add_argument("--odds", type=float, nargs="+", required=True)
    single_parser = sub.add_parser("single")
    single_parser.add_argument("--odds", type=float, required=True)
    single_parser.add_argument("--win", type=float, required=True)
    single_parser.add_argument("--push", type=float, default=0)
    single_parser.add_argument("--stake", type=float, default=1)
    single_parser.add_argument("--kelly-fraction", type=float)
    parlay_parser = sub.add_parser("parlay")
    parlay_parser.add_argument("--odds", type=float, nargs="+", required=True)
    parlay_parser.add_argument("--probabilities", type=float, nargs="+")
    parlay_parser.add_argument("--assume-independent", action="store_true")
    parlay_parser.add_argument("--stake", type=float, default=1)
    settlement_parser = sub.add_parser("settlement")
    settlement_parser.add_argument("--odds", type=float, required=True)
    settlement_parser.add_argument("--probabilities", type=float, nargs=5, required=True)
    settlement_parser.add_argument("--stake", type=float, default=1)
    args = vars(parser.parse_args())
    command = args.pop("command")
    handlers = {"market": market, "single": single, "parlay": parlay, "settlement": settlement}
    try:
        print(json.dumps(handlers[command](**args), indent=2, ensure_ascii=False, allow_nan=False))
    except (ValueError, OverflowError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()

