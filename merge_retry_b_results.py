#!/usr/bin/env python3
"""
Merge Condition B retry results into a complete eval-results-b.json.

Combines:
  - results/eval-results-b-partial.json  (8 fully-done scenarios, 74 results)
  - results/eval-results-b-retry.json    (92 retried scenarios, 736 results)

Output: results/eval-results-b.json

Usage:
  python3 merge_retry_b_results.py
"""
import json
import copy

PARTIAL = "results/eval-results-b-partial.json"
RETRY   = "results/eval-results-b-retry.json"
OUTPUT  = "results/eval-results-b.json"


def provider_id(r):
    p = r.get("provider")
    return p["id"] if isinstance(p, dict) else str(p)


def scenario_id(r):
    return r.get("vars", {}).get("scenario_id", "")


def is_good(r):
    return not r.get("error") and r.get("score", 0) > 0


def main():
    with open(PARTIAL) as f:
        partial = json.load(f)
    with open(RETRY) as f:
        retry = json.load(f)

    partial_results = partial["results"]["results"]
    retry_results = retry["results"]["results"]

    # Index by (scenario_id, provider_id)
    partial_index = {}
    for r in partial_results:
        key = (scenario_id(r), provider_id(r))
        partial_index[key] = r

    retry_index = {}
    for r in retry_results:
        key = (scenario_id(r), provider_id(r))
        retry_index[key] = r

    added = replaced = kept = 0

    # Start with partial results, replacing bad ones
    merged = []
    for r in partial_results:
        key = (scenario_id(r), provider_id(r))
        if not is_good(r) and key in retry_index and is_good(retry_index[key]):
            merged.append(retry_index[key])
            replaced += 1
        else:
            merged.append(r)
            kept += 1

    # Add retry results absent from partial
    for key, r in retry_index.items():
        if key not in partial_index:
            merged.append(r)
            added += 1

    passed  = sum(1 for r in merged if r.get("success"))
    failed  = sum(1 for r in merged if not r.get("success"))
    errored = sum(1 for r in merged if r.get("error"))

    print(f"Partial results  : {len(partial_results)}")
    print(f"Retry results    : {len(retry_results)}")
    print(f"Kept from partial: {kept}")
    print(f"Replaced         : {replaced}")
    print(f"Added (new)      : {added}")
    print(f"Total merged     : {len(merged)}")
    print(f"  Passed: {passed}  Failed: {failed}  Errored: {errored}")

    out = copy.deepcopy(partial)
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
