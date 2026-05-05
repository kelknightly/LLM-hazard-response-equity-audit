# LLM Hazard Response Equity Audit (LHREA)

## Origin

This project is a direct response to the findings in **"Governing Generative AI in Disaster Risk Management"** (Rafiezadeh Shahi et al., 2026 — [EarthArXiv preprint 11940](https://eartharxiv.org/repository/view/11940/), [PDF](https://eartharxiv.org/repository/object/11940/download/21441/)), which identified a pattern the authors call **"Representational Flattening"** in large language models: when asked for emergency guidance, LLMs systematically default to advice calibrated for Western, high-income, car-dependent, grid-connected users — regardless of what the user actually described about their situation.

The practical danger is concrete. A person in an informal settlement in Freetown who asks an LLM for cyclone guidance and receives advice to *"drive to the nearest shelter"* or *"charge your devices and monitor the emergency alert app"* has been given information that is not just useless — it may be actively harmful, because it consumes the time and trust that should be spent on actions they can actually take.

## Vision

A rigorous, reproducible, pre-registered benchmark that quantifies how badly each major LLM fails users in low-resource infrastructure contexts during natural hazard emergencies — and provides a scoring framework that researchers, journalists, and developers can use to hold models accountable.

## Goals

1. **Measure the gap** — Produce paired Phronesis scores (structured vs. unstructured) for 8 frontier models across 50 location pairs and 5 hazard types, generating 800 evaluated responses.
2. **Isolate the variable** — By holding the "ask" constant and varying only the infrastructure description, any difference in advice quality is attributable to the model's assumptions about the user, not to the prompt phrasing.
3. **Pre-register the rubric** — The evaluation criteria (`evaluation_criteria.md`) were designed before any model outputs were collected, preventing post-hoc score rationalization.
4. **Be reproducible** — The full benchmark is runnable by anyone with an OpenRouter API key and `promptfoo` installed. No proprietary tooling, no hidden prompts.

## Approach

### The "Blind" Test

The models under evaluation are not told they are being audited for bias. They receive neutral, realistic user requests for emergency help. The only difference between a **Scenario A** (structured) and **Scenario B** (unstructured) row is the description of local infrastructure embedded in the prompt. If a model gives structurally different advice, it is because it inferred something about the user's resources or location — not because the question was asked differently.

### Dataset

`scenarios.csv` contains 100 prompts: 10 pairs × 2 infrastructure types × 5 hazard categories (Flash Flood, Extreme Heat, Wildfire, Landslide, Hurricane/Cyclone). Pairs span Latin America, Sub-Saharan Africa, South Asia, Southeast Asia, and Eastern Europe as unstructured counterparts to locations in the USA, EU, and Australia.

### Evaluation

Responses are scored on the **Phronesis Scale** (1–5), defined in `evaluation_criteria.md`. The scale measures a single quality: *can a person in the described environment actually follow this advice with only the resources the prompt says they have?* It does not reward correct disaster science; it rewards contextual humility.

The primary bias signal is the **paired score gap**: a model that scores 4.2 on structured scenarios and 1.8 on unstructured scenarios has demonstrated Representational Flattening. A model that scores consistently across the pair is exhibiting equitable contextual reasoning.

### Models Tested

Claude 3.7 Sonnet, Claude 3 Haiku, GPT-4o, Gemini 2.5 Flash, Llama 3.1 8B Instruct,
Llama 3.1 70B Instruct, Mistral NeMo 12B, DeepSeek V3.2. See [METHODOLOGY.md](METHODOLOGY.md)
for the rationale behind this spread.

---

## Results

The audit confirmed the Representational Flattening pattern described in preprint 11940,
and extended it with a new experimental dimension: testing whether the gap persists when
models are given only a location name and hazard type, with no infrastructure description
(Condition B).

**Key findings** — full analysis in [FINDINGS.md](FINDINGS.md):

- **The equity gap is real but context-dependent.** When infrastructure constraints are
  explicitly stated (Condition A), six of eight models score 4/5 for both structured and
  unstructured users — no gap. When context is removed (Condition B), the gap opens:
  unstructured users degrade more than structured users, confirming the paper's hypothesis
  that models default to high-resource assumptions in the absence of explicit signals.

- **Llama 3.1 8B is the primary risk model.** The only open-weights 8B model in the
  benchmark dropped from 4.00 to 3.79 in Condition B, with an equity gap (structured −
  unstructured) of 0.14 — absent in all other models. It also refused to provide emergency
  wildfire guidance entirely for several scenarios when infrastructure context was removed,
  scoring 1/5 for both structured (Malibu, Sacramento) and unstructured (Bogotá, Jakarta)
  locations. This matters because Llama 3.1 8B is the model most likely to be self-hosted
  by NGOs and community organisations in exactly the settings where unstructured
  infrastructure is the reality.

- **Wildfire is the highest-risk hazard.** The only hazard with meaningful score degradation
  in Condition B (Δ = −0.12), entirely driven by the Llama 3.1 8B refusal pattern.

- **Frontier models are robust.** Claude (both tiers), GPT-4o, Gemini 2.5 Flash, Llama 70B,
  and DeepSeek V3.2 all maintained a mean score of 4.00 across both conditions with zero
  equity gap — demonstrating that geographic inference without explicit context is achievable
  at scale.

**A note on AI-as-evaluator:** During review, the Claude 3 Haiku judge was found to
hallucinate evaluation steps for responses that were outright refusals, awarding scores of
3–4/5 to empty or one-sentence outputs by fabricating steps that were never written. This
was caught through manual review and corrected with human-assigned scores. The incident is
documented in full in [LLM_JUDGE_HALLUCINATION.md](LLM_JUDGE_HALLUCINATION.md) and is
itself a finding: AI evaluation pipelines require human spot-checks for refusal-class
responses.

---

## Files

| File | Purpose |
|------|---------|
| `scenarios.csv` | 100 test prompts (the benchmark dataset) |
| `evaluation_criteria.md` | Pre-registered Phronesis rubric for scoring responses |
| `promptfooconfig.yaml` | Promptfoo configuration to run the evaluation (Condition A) |
| `METHODOLOGY.md` | Models, framework, API setup, judge design, and rubric summary |
| `FINDINGS.md` | Full results and analysis |
| `LLM_JUDGE_HALLUCINATION.md` | Forensic record of judge hallucination with raw evidence |
| `results/` | Eval outputs (JSON) and row-level comparison CSV |

## Running the Audit

```bash
# Install promptfoo
npm install -g promptfoo

# Set your OpenRouter API key
export OPENROUTER_API_KEY=sk-or-...

# Run all 800 evaluations (Condition A)
promptfoo eval

# Open the interactive results viewer
promptfoo view
```

## Reference

Rafiezadeh Shahi, K., Kuglitsch, M. M., Bove, J. B., Ronco, M., Ghamisi, P., Sun, Y.,
Duca, G., Gargiulo, M. V., Berlin, A., Jäpölä, J.-P., Pharand-Deschênes, F.,
Malamud, B. D., Sakschewski, B., Rockström, J., & Kreibich, H. (2026).
*Governing Generative AI in Disaster Risk Management.*
EarthArXiv. https://doi.org/10.31223/X5HJ2B
