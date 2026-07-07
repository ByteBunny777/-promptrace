"""Command-line interface: `promptrace stats|tail|export|models <file>`"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime

from .analyze import group_by_model, group_by_tag, load_entries, summarize, to_csv
from .pricing import DEFAULT_PRICING


def _fmt_money(v) -> str:
    return "n/a" if v is None else f"${v:.4f}"


def cmd_stats(args: argparse.Namespace) -> None:
    entries = load_entries(args.file)
    if not entries:
        print(f"No entries found in {args.file}")
        return

    overall = summarize(entries)
    print(f"=== {args.file} ===")
    print(f"Calls:            {overall['calls']}")
    print(f"Prompt tokens:    {overall['prompt_tokens']}")
    print(f"Completion tok.:  {overall['completion_tokens']}")
    print(f"Total tokens:     {overall['total_tokens']}")
    print(f"Estimated cost:   {_fmt_money(overall['cost_usd'])}")
    if overall["avg_latency_ms"] is not None:
        print(f"Avg latency:      {overall['avg_latency_ms']} ms")
    else:
        print("Avg latency:      n/a")

    if args.by == "model":
        print("\n-- by model --")
        for model, stats in sorted(group_by_model(entries).items()):
            print(f"{model:<24} calls={stats['calls']:<5} tokens={stats['total_tokens']:<8} cost={_fmt_money(stats['cost_usd'])}")
    elif args.by == "tag":
        print("\n-- by tag --")
        for tag, stats in sorted(group_by_tag(entries).items()):
            print(f"{tag:<24} calls={stats['calls']:<5} tokens={stats['total_tokens']:<8} cost={_fmt_money(stats['cost_usd'])}")


def cmd_tail(args: argparse.Namespace) -> None:
    entries = load_entries(args.file)
    for e in entries[-args.n:]:
        ts = datetime.fromtimestamp(e.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        tags = ",".join(e.tags) if e.tags else "-"
        print(f"[{ts}] {e.model:<20} tokens={e.total_tokens:<6} cost={_fmt_money(e.cost_usd):<10} tags={tags}")


def cmd_export(args: argparse.Namespace) -> None:
    entries = load_entries(args.file)
    to_csv(entries, args.out)
    print(f"Wrote {len(entries)} entries to {args.out}")


def cmd_models(_args: argparse.Namespace) -> None:
    print("Known models in default pricing table (USD / 1K tokens, input / output):")
    for model, (i, o) in sorted(DEFAULT_PRICING.items()):
        print(f"  {model:<24} in={i:<10} out={o}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="promptrace", description="Log and analyze LLM API calls.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_stats = sub.add_parser("stats", help="Show summary statistics for a log file")
    p_stats.add_argument("file", help="Path to a .jsonl log file")
    p_stats.add_argument("--by", choices=["model", "tag"], default="model", help="Group breakdown by model or tag")
    p_stats.set_defaults(func=cmd_stats)

    p_tail = sub.add_parser("tail", help="Show the most recent log entries")
    p_tail.add_argument("file", help="Path to a .jsonl log file")
    p_tail.add_argument("-n", type=int, default=10, help="Number of entries to show")
    p_tail.set_defaults(func=cmd_tail)

    p_export = sub.add_parser("export", help="Export a log file to CSV")
    p_export.add_argument("file", help="Path to a .jsonl log file")
    p_export.add_argument("--out", required=True, help="Output CSV path")
    p_export.set_defaults(func=cmd_export)

    p_models = sub.add_parser("models", help="List models known to the default pricing table")
    p_models.set_defaults(func=cmd_models)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
