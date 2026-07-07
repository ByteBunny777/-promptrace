"""Minimal example: logging a couple of LLM calls and reading them back.

Run: python example.py
"""
from promptrace import LLMLogger, load_entries, summarize

logger = LLMLogger("example_logs/session.jsonl")

# Option 1: log a call you already completed
logger.log(
    model="claude-sonnet-5",
    prompt="Write a haiku about autumn",
    response="Leaves drift to the ground...",
    prompt_tokens=8,
    completion_tokens=17,
    tags=["creative"],
)

# Option 2: wrap the call and measure latency automatically
with logger.track(model="gpt-4o-mini", prompt="Summarize this article", tags=["summary"]) as call:
    response_text = "Here is a short summary."  # <- replace with your real API call
    call.set_response(response_text, prompt_tokens=300, completion_tokens=40)

# Read the log back and print a quick summary
entries = load_entries("example_logs/session.jsonl")
stats = summarize(entries)
print(f"Logged {stats['calls']} calls, {stats['total_tokens']} tokens, "
      f"~${stats['cost_usd']:.4f} estimated cost.")
print("Try: promptrace stats example_logs/session.jsonl --by model")
