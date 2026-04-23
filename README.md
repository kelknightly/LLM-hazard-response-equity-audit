# LLM Hazard Response Equity Audit (LHREA)

## Origin

This project is a direct response to the findings in **EarthArXiv preprint 11940**, which identified a pattern the authors call **"Representational Flattening"** in large language models: when asked for emergency guidance, LLMs systematically default to advice calibrated for Western, high-income, car-dependent, grid-connected users — regardless of what the user actually described about their situation.

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

| Model | Provider |
|-------|----------|
| Claude 3.5 Sonnet v2 | Anthropic |
| Claude 3 Haiku | Anthropic |
| GPT-4o | OpenAI |
| Gemini 1.5 Pro v2 | Google |
| Llama 3.1 8B Instruct | Meta |
| Llama 3.1 70B Instruct | Meta |
| Mistral NeMo 12B | Mistral AI |
| DeepSeek V3.2 | DeepSeek |

## Files

| File | Purpose |
|------|---------|
| `scenarios.csv` | 100 test prompts (the benchmark dataset) |
| `evaluation_criteria.md` | Pre-registered Phronesis rubric for scoring responses |
| `promptfooconfig.yaml` | Promptfoo configuration to run the evaluation |
| `results/` | Output directory for eval results (created on first run) |

## Running the Audit

```bash
# Install promptfoo
npm install -g promptfoo

# Set your OpenRouter API key
export OPENROUTER_API_KEY=sk-or-...

# Run all 800 evaluations
promptfoo eval

# Open the interactive results viewer
promptfoo view
```

## Reference

> EarthArXiv preprint 11940 — *[Representational Flattening in LLM Disaster Response]*  
> https://eartharxiv.org/repository/object/11940/
