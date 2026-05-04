"""
LHREA Condition A vs B Comparison Analysis
===========================================
Compares Phronesis scores across Condition A (explicit infrastructure context)
and Condition B (bare prompts — location and hazard only) to measure:

  1. Per-model score degradation when context is withheld (B - A delta)
  2. Equity gap in each condition: mean(structured) - mean(unstructured)
  3. Whether removing context disproportionately harms unstructured-location users
  4. Breakdown by hazard type and infrastructure type

Usage:
    python3 compare.py
    python3 compare.py --a results/eval-results-a.json --b results/eval-results-b.json
    python3 compare.py --out comparison.csv   # also export full row-level CSV
"""

import json
import re
import sys
import argparse
import csv
from pathlib import Path
from collections import defaultdict


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_results(path: str) -> list[dict]:
    """Load promptfoo eval-results.json and return a flat list of result dicts."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    # promptfoo nests results differently across versions; handle both.
    if isinstance(data, dict):
        results = (
            data.get("results", {}).get("results")        # v2/v3
            or data.get("results")                         # flat
            or []
        )
    elif isinstance(data, list):
        results = data
    else:
        results = []

    return results


def extract_phronesis_score(result: dict) -> float | None:
    """
    Return the raw 1-5 Phronesis score from a result row.

    The judge embeds the score in gradingResult.reason as "SCORE: N".
    We prefer parsing that over the normalised 0-1 float to keep the
    familiar 1-5 scale throughout.
    """
    grading = result.get("gradingResult") or {}
    reason = grading.get("reason", "")

    m = re.search(r"SCORE:\s*([1-5])", reason)
    if m:
        return float(m.group(1))

    # Fallback: unnormalise the 0-1 score field
    score_float = grading.get("score")
    if score_float is not None:
        return round(score_float * 5, 1)

    return None


def row_key(result: dict) -> tuple:
    """Return (scenario_id, model_label) as the join key between conditions."""
    vars_ = result.get("vars", {})
    provider = result.get("provider", {})
    scenario_id = vars_.get("scenario_id", "")
    label = provider.get("label") or provider.get("id", "")
    return (scenario_id, label)


def enrich(result: dict) -> dict:
    """Flatten the fields we care about into a plain dict."""
    vars_ = result.get("vars", {})
    provider = result.get("provider", {})
    meta = result.get("metadata") or result.get("testCase", {}).get("metadata", {})

    return {
        "scenario_id": vars_.get("scenario_id", ""),
        "pair_id": vars_.get("pair_id") or meta.get("pair_id", ""),
        "location": vars_.get("location") or meta.get("location", ""),
        "infra_type": vars_.get("infra_type") or meta.get("infra_type", ""),
        "hazard": vars_.get("hazard") or meta.get("hazard", ""),
        "model": provider.get("label") or provider.get("id", ""),
        "score": extract_phronesis_score(result),
        "pass": (result.get("gradingResult") or {}).get("pass"),
        "reason": (result.get("gradingResult") or {}).get("reason", ""),
        "error": result.get("error"),
    }


# ---------------------------------------------------------------------------
# Analysis functions
# ---------------------------------------------------------------------------

def mean(values):
    vals = [v for v in values if v is not None]
    return sum(vals) / len(vals) if vals else None


def fmt(v, decimals=2):
    return f"{v:.{decimals}f}" if v is not None else "N/A"


def print_table(title: str, rows: list[tuple], headers: list[str]):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")
    col_w = [max(len(h), max((len(str(r[i])) for r in rows), default=0)) for i, h in enumerate(headers)]
    fmt_str = "  " + "  ".join(f"{{:<{w}}}" for w in col_w)
    print(fmt_str.format(*headers))
    print("  " + "  ".join("-" * w for w in col_w))
    for row in rows:
        print(fmt_str.format(*row))


def analyse(a_results: list[dict], b_results: list[dict], export_csv: str | None = None):
    # Index both conditions by (scenario_id, model)
    a_index = {row_key(r): enrich(r) for r in a_results}
    b_index = {row_key(r): enrich(r) for r in b_results}

    all_keys = set(a_index) | set(b_index)

    # Build joined rows
    joined = []
    for key in sorted(all_keys):
        a = a_index.get(key)
        b = b_index.get(key)
        row = {
            "scenario_id": key[0],
            "model": key[1],
            "infra_type": (a or b).get("infra_type", ""),
            "hazard": (a or b).get("hazard", ""),
            "location": (a or b).get("location", ""),
            "pair_id": (a or b).get("pair_id", ""),
            "score_a": a["score"] if a else None,
            "score_b": b["score"] if b else None,
            "delta": (b["score"] - a["score"]) if (a and b and a["score"] is not None and b["score"] is not None) else None,
        }
        joined.append(row)

    # --- 1. Coverage ---
    a_count = sum(1 for r in joined if r["score_a"] is not None)
    b_count = sum(1 for r in joined if r["score_b"] is not None)
    print(f"\nCoverage: Condition A = {a_count} scored results | Condition B = {b_count} scored results")
    errors_a = sum(1 for r in a_results if r.get("error"))
    errors_b = sum(1 for r in b_results if r.get("error"))
    if errors_a or errors_b:
        print(f"  Errors: A={errors_a}  B={errors_b} (excluded from scoring)")

    # --- 2. Overall means ---
    overall_a = mean([r["score_a"] for r in joined])
    overall_b = mean([r["score_b"] for r in joined])
    delta_overall = (overall_b - overall_a) if (overall_a is not None and overall_b is not None) else None
    print(f"\nOverall mean Phronesis score (1–5):")
    print(f"  Condition A (explicit context): {fmt(overall_a)}")
    print(f"  Condition B (bare prompt):       {fmt(overall_b)}")
    print(f"  Delta (B − A):                   {fmt(delta_overall)}  {'↓ degradation' if delta_overall and delta_overall < 0 else '↑ improvement' if delta_overall and delta_overall > 0 else ''}")

    # --- 3. Per-model breakdown ---
    models = sorted({r["model"] for r in joined})
    model_rows = []
    for model in models:
        rows = [r for r in joined if r["model"] == model]
        sa = mean([r["score_a"] for r in rows])
        sb = mean([r["score_b"] for r in rows])
        d = (sb - sa) if (sa is not None and sb is not None) else None
        model_rows.append((model[:35], fmt(sa), fmt(sb), fmt(d)))

    print_table(
        "Per-model mean Phronesis score",
        model_rows,
        ["Model", "Cond A", "Cond B", "Delta (B−A)"]
    )

    # --- 4. Equity gap by condition ---
    # Equity gap = mean(structured) - mean(unstructured)
    # A positive gap means structured locations score higher.
    print(f"\n{'='*70}")
    print(f"  Equity gap (structured − unstructured mean score)")
    print(f"{'='*70}")
    for label, score_key in [("Condition A", "score_a"), ("Condition B", "score_b")]:
        s_scores = [r[score_key] for r in joined if r["infra_type"] == "structured" and r[score_key] is not None]
        u_scores = [r[score_key] for r in joined if r["infra_type"] == "unstructured" and r[score_key] is not None]
        s_mean = mean(s_scores)
        u_mean = mean(u_scores)
        gap = (s_mean - u_mean) if (s_mean is not None and u_mean is not None) else None
        print(f"  {label}: structured={fmt(s_mean)}  unstructured={fmt(u_mean)}  gap={fmt(gap)}")

    print(f"  (Larger gap in Condition B = context removal disproportionately")
    print(f"   harms unstructured-location users — primary bias finding)")

    # --- 5. Per-infra_type and per-hazard ---
    for group_key, title in [("infra_type", "Infrastructure type"), ("hazard", "Hazard type")]:
        groups = sorted({r[group_key] for r in joined})
        group_rows = []
        for g in groups:
            rows = [r for r in joined if r[group_key] == g]
            sa = mean([r["score_a"] for r in rows])
            sb = mean([r["score_b"] for r in rows])
            d = (sb - sa) if (sa is not None and sb is not None) else None
            group_rows.append((g[:30], fmt(sa), fmt(sb), fmt(d)))
        print_table(
            f"By {title}",
            group_rows,
            [title, "Cond A", "Cond B", "Delta (B−A)"]
        )

    # --- 6. Per-model equity gap comparison ---
    print(f"\n{'='*70}")
    print(f"  Per-model equity gap: structured − unstructured (each condition)")
    print(f"{'='*70}")
    headers = ["Model", "Gap A", "Gap B", "Gap widening (B−A gap)"]
    gap_rows = []
    for model in models:
        rows = [r for r in joined if r["model"] == model]
        def equity_gap(score_key):
            s = mean([r[score_key] for r in rows if r["infra_type"] == "structured"])
            u = mean([r[score_key] for r in rows if r["infra_type"] == "unstructured"])
            return (s - u) if (s is not None and u is not None) else None
        ga = equity_gap("score_a")
        gb = equity_gap("score_b")
        widening = (gb - ga) if (ga is not None and gb is not None) else None
        gap_rows.append((model[:35], fmt(ga), fmt(gb), fmt(widening)))
    col_w = [max(len(h), max((len(str(r[i])) for r in gap_rows), default=0)) for i, h in enumerate(headers)]
    fmt_str = "  " + "  ".join(f"{{:<{w}}}" for w in col_w)
    print(fmt_str.format(*headers))
    print("  " + "  ".join("-" * w for w in col_w))
    for row in gap_rows:
        print(fmt_str.format(*row))

    # --- 7. Worst degradation: top 10 scenarios ---
    worst = sorted(
        [r for r in joined if r["delta"] is not None],
        key=lambda r: r["delta"]
    )[:10]
    if worst:
        print_table(
            "Top 10 scenarios with worst score degradation in Condition B",
            [(r["scenario_id"], r["model"][:25], r["location"][:30],
              fmt(r["score_a"]), fmt(r["score_b"]), fmt(r["delta"]))
             for r in worst],
            ["Scenario", "Model", "Location", "Score A", "Score B", "Delta"]
        )

    # --- 8. CSV export ---
    if export_csv:
        fields = ["scenario_id", "pair_id", "location", "infra_type", "hazard",
                  "model", "score_a", "score_b", "delta"]
        with open(export_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for r in sorted(joined, key=lambda x: (x["scenario_id"], x["model"])):
                writer.writerow({k: r.get(k) for k in fields})
        print(f"\nRow-level data exported to: {export_csv}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Compare LHREA Condition A vs B results")
    parser.add_argument("--a", default="results/eval-results-a.json",
                        help="Path to Condition A results JSON (default: results/eval-results-a.json)")
    parser.add_argument("--b", default="results/eval-results-b.json",
                        help="Path to Condition B results JSON (default: results/eval-results-b.json)")
    parser.add_argument("--out", default=None,
                        help="Optional: export full row-level data as CSV")
    args = parser.parse_args()

    missing = [p for p in [args.a, args.b] if not Path(p).exists()]
    if missing:
        print(f"Missing result files: {missing}")
        print("Run Condition A:  promptfoo eval")
        print("Run Condition B:  promptfoo eval --config promptfooconfig_b.yaml")
        sys.exit(1)

    print(f"Loading Condition A: {args.a}")
    a_results = load_results(args.a)
    print(f"Loading Condition B: {args.b}")
    b_results = load_results(args.b)

    analyse(a_results, b_results, export_csv=args.out)


if __name__ == "__main__":
    main()
