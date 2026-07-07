# promptrace

[![PyPI](https://img.shields.io/badge/pypi-promptrace-3775A9?logo=python&logoColor=white)](https://pypi.org/project/promptrace/)
[![Python](https://img.shields.io/badge/python-3.8%2B-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)](#design-notes)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](#license)

Lightweight, **dependency-free** logging and analytics for LLM API calls.

Log every prompt/response with token counts, latency, and estimated cost to a
plain JSONL file — then get instant stats from the CLI or Python API. No
external services, no config, no vendor lock-in: just a file on disk you own.

```
=== session.jsonl ===
Calls:            42
Prompt tokens:    18230
Completion tok.:  6110
Total tokens:     24340
Estimated cost:   $0.1187
Avg latency:      842.3 ms

-- by model --
claude-sonnet-5          calls=30    tokens=19800    cost=$0.0980
gpt-4o-mini              calls=12    tokens=4540     cost=$0.0207
```

## Why

Most projects that call LLM APIs end up needing the same three things sooner
or later: *how many tokens am I burning through*, *how much is this costing
me*, and *which calls are slow*. `promptrace` gives you all three with two
lines of code and zero dependencies — everything is Python standard library.

## Install

```bash
pip install .
# or just copy the promptrace/ folder into your project
```

## Usage

### Log calls from your code

```python
from promptrace import LLMLogger

logger = LLMLogger("logs/session.jsonl")

# Log a call you've already completed
logger.log(
    model="claude-sonnet-5",
    prompt="Write a haiku about autumn",
    response="Leaves drift to the ground...",
    prompt_tokens=8,
    completion_tokens=17,
    tags=["creative"],
)

# Or wrap the call to measure latency automatically
with logger.track(model="gpt-4o-mini", prompt="Summarize this") as call:
    response = your_llm_client.complete(...)
    call.set_response(response.text, prompt_tokens=300, completion_tokens=40)
```

### Analyze from the command line

```bash
promptrace stats logs/session.jsonl              # overall summary
promptrace stats logs/session.jsonl --by tag      # breakdown by tag
promptrace tail logs/session.jsonl -n 20          # recent calls
promptrace export logs/session.jsonl --out out.csv
promptrace models                                 # list known pricing
```

### Or from Python

```python
from promptrace import load_entries, summarize, group_by_model

entries = load_entries("logs/session.jsonl")
print(summarize(entries))
print(group_by_model(entries))
```

## Privacy: redact prompt/response text

If you don't want raw prompt/response text sitting on disk, turn it off
globally or per-call — only a SHA-256 hash and character length are kept,
still enough to detect duplicates or check length distributions:

```python
logger = LLMLogger("logs/session.jsonl", store_text=False)
```

## Cost estimation

`promptrace` ships with a small, editable pricing table (USD per 1,000
tokens) covering common models. Unknown models simply report `cost_usd=None`
instead of guessing. Bring your own table:

```python
from promptrace import LLMLogger

my_pricing = {"my-custom-model": (0.001, 0.002)}  # (input, output) per 1K tokens
logger = LLMLogger("logs/session.jsonl", pricing=my_pricing)
```

or load one from a JSON file with `load_pricing_file("pricing.json")`.

## Design notes

- **Storage format** is plain JSONL — one call per line, human-readable,
  append-only, trivially diffable, and greppable without any tooling.
- **No network calls, no external dependencies.** The whole library is
  standard-library Python, so it's safe to drop into any project.
- **Cost table is a starting point**, not a source of truth — check your
  provider's current pricing page for anything billing-critical.

## Run tests

```bash
python -m unittest tests.test_basic -v
```

## License

MIT
