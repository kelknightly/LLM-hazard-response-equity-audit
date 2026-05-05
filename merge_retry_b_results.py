#!/usr/bin/env python3
"""
Merge all Condition B partial/batch results into a complete eval-results-b.json.

Combines all of:
  - results/eval-results-b-partial.json
  - results/eval-results-b-retry.json
  - results/eval-results-b-batch1.json  (if present)
  - results/eval-results-b-batch2.json  (if present)
  - results/eval-results-b-batch3.json  (if present)
  - results/eval-results-b-batch4.json  (if present)

Output: results/eval-results-b.json

Usage:
  python3 merge_retry_b_results.py
"""
import json
import copy
import os

SOURCES = [
    "results/eval-results-b-partial.json",
    "results/eval-results-b-retry.json",
    "results/eval-results-b-batch1.json",
    "results/eval-results-b-batch2.json",
    "results/eval-results-b-batch3.json",
    "results/eval-results-b-batch4.json",
    "results/eval-results-b-retry-sonnet.json",
]
OUTPUT  = "results/eval-results-b.json"


def provider_id(r):
    p = r.get("provider")
    return p["id"] if isinstance(p, dict) else str(p)


def scenario_id(r):
    return r.get("vars", {}).get("scenario_id", "")


def is_good(r):
    return not r.get("error") and r.get("score", 0) > 0


def main():
    # Load all source files that exist
    base = None
    all_results = []
    for path in SOURCES:
        if not os.path.exists(path):
            print(f"Skipping (not found): {path}")
            continue
        with open(path) as f:
            d = json.load(f)
        r = d.get("results", {}).get("results", [])
        print(f"{path}: {len(r)} results")
        all_results.extend(r)
        if base is None:
            base = d  # use first file as structural template

    if base is None:
        print("ERROR: no source files found")
        return

    # Deduplicate: last good result wins for each (scenario_id, provider_id)
    index = {}
    for r in all_results:
        key = (scenario_id(r), provider_id(r))
        if key not in index or (is_good(r) and not is_good(index[key])):
            index[key] = r

    merged = list(index.values())
    passed  = sum(1 for r in merged if r.get("success"))
    failed  = sum(1 for r in merged if not r.get("success"))
    errored = sum(1 for r in merged if r.get("error"))

    print(f"\nUnique (scenario, model) pairs: {len(merged)}")
    print(f"  Passed: {passed}  Failed: {failed}  Errored: {errored}")

    out = copy.deepcopy(base)
    out["results"]["results"] = merged
    out["results"]["stats"] = {
        "successes": passed,
        "failures": failed,
        "errors": errored,
        "tokenUsage": {}
    }

    with open(OUTPUT, "w") as f:
        json.dump(out, f, indent=2)

    print(f"\nWritten to {OUTPUT}")


if __name__ == "__main__":
    main()
