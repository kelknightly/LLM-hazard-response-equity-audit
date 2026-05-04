"""
Generate scenarios_b.csv (Condition B) from scenarios.csv (Condition A).

Condition B strips the explicit infrastructure description from each prompt,
leaving only the location and hazard. The model must infer infrastructure
constraints from geographic location alone — testing for representational bias
rather than instruction-following.

The infra_description column is KEPT in the CSV so the judge can still
evaluate responses against ground-truth infrastructure constraints.
"""

import csv
import re


def strip_infra_description(prompt: str) -> str:
    """
    Remove the 'Our neighborhood has ...' sentence from a prompt.

    Original structure:
      [Hazard statement]. [Family intro]. Our neighborhood has [description]. [Request].

    Condition B structure:
      [Hazard statement]. [Family intro]. [Request].
    """
    # Matches " Our neighborhood has" through the period and trailing space,
    # up to the action request ("Give us"). The description is always one sentence.
    stripped = re.sub(r" Our neighborhood has[^.]*\. ", " ", prompt)
    return stripped.strip()


def main():
    in_path = "scenarios.csv"
    out_path = "scenarios_b.csv"

    with open(in_path, newline="", encoding="utf-8") as fin:
        reader = csv.DictReader(fin)
        fieldnames = list(reader.fieldnames) + ["condition"]

        rows = []
        for row in reader:
            original_prompt = row["prompt"]
            bare_prompt = strip_infra_description(original_prompt)

            # Sanity check
            if original_prompt == bare_prompt:
                print(f"WARNING: No infra description stripped for {row['scenario_id']}")
                print(f"  Prompt: {original_prompt[:120]}")

            row["prompt"] = bare_prompt
            row["condition"] = "B"
            rows.append(row)

    with open(out_path, "w", newline="", encoding="utf-8") as fout:
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Written {len(rows)} rows to {out_path}")
    print("\nSample stripped prompts:")
    for row in rows[:4]:
        print(f"  [{row['scenario_id']}] {row['prompt'][:100]}...")


if __name__ == "__main__":
    main()
