"""Compare Claude Code token usage on a synthetic bug fix."""

import argparse
import json
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import tempfile


SKILL = Path(__file__).resolve().parents[1] / "skills/greedy-token/SKILL.md"
TASK = (
    "Fix checkout.py so discounts for quantities of 10 or more apply "
    "starting at exactly 10. Keep the function signature and other "
    "behavior unchanged. Context: the reported failure is in checkout.log. "
    "Only edit checkout.py. Reply with a short summary."
)
CHECK = """
from checkout import quote

for quantity, expected in [(0, 0), (1, 200), (9, 1800), (10, 1800), (11, 1980)]:
    actual = quote(quantity)
    assert actual == expected, (quantity, actual, expected)
"""
CHECKOUT = """def quote(quantity):
    total = quantity * 200
    return total * 90 // 100 if quantity > 10 else total
"""
TOKEN_FIELDS = (
    "input_tokens",
    "cache_creation_input_tokens",
    "cache_read_input_tokens",
    "output_tokens",
)


def run_case(claude, model, skill, budget):
    with tempfile.TemporaryDirectory(prefix="greedy-token-benchmark-") as tmp:
        root = Path(tmp)
        (root / "checkout.py").write_text(CHECKOUT, encoding="utf-8")
        log = ["INFO checkout loaded"]
        log.extend(f"INFO processed order {number}" for number in range(1, 1001))
        log.append("ERROR quantity=10 expected=1800 actual=2000")
        (root / "checkout.log").write_text("\n".join(log) + "\n", encoding="utf-8")

        command = [
            claude, "--bare", "--print", "--output-format", "json",
            "--model", model, "--no-session-persistence", "--max-turns", "10",
            "--max-budget-usd", str(budget), "--permission-mode", "acceptEdits",
            "--tools", "Read,Edit,Grep,Glob",
        ]
        if skill:
            command.extend(["--append-system-prompt", skill])
        command.extend(["--", TASK])
        completed = subprocess.run(
            command, cwd=root, capture_output=True, text=True,
            stdin=subprocess.DEVNULL, timeout=180,
        )
        if completed.returncode:
            detail = completed.stderr.strip() or completed.stdout.strip()
            raise ValueError(f"Claude Code exited with {completed.returncode}: {detail[:400]}")
        result = json.loads(completed.stdout)
        if not isinstance(result, dict) or result.get("is_error") or result.get("subtype") != "success":
            raise ValueError("Claude Code did not report a successful run.")
        usage = result.get("usage")
        if not isinstance(usage, dict) or not all(
            type(usage.get(key)) is int and usage[key] >= 0 for key in TOKEN_FIELDS
        ):
            raise ValueError("Claude Code returned incomplete token usage.")
        check = subprocess.run(
            [sys.executable, "-B", "-c", CHECK], cwd=root, capture_output=True,
            text=True, timeout=10,
        )
        counts = {key: usage[key] for key in TOKEN_FIELDS}
        return {
            "passed": check.returncode == 0,
            **counts,
            "total_tokens": sum(counts.values()),
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="Use the same explicit model ID for both conditions.")
    parser.add_argument("--pairs", type=int, default=1, help="Number of paired trials.")
    parser.add_argument("--budget-per-run", type=float, required=True, help="Claude Code's USD budget per run.")
    args = parser.parse_args()
    if args.pairs < 1 or not 0 < args.budget_per_run < float("inf"):
        parser.error("--pairs and --budget-per-run must be positive and finite")
    claude = shutil.which("claude")
    if claude is None:
        parser.error("Claude Code must be installed and available on PATH")

    savings = []
    try:
        skill = SKILL.read_text(encoding="utf-8").split("\n---\n", 1)[1].strip()
        for pair in range(1, args.pairs + 1):
            pair_results = {}
            order = ("baseline", "skill") if pair % 2 else ("skill", "baseline")
            for condition in order:
                counts = run_case(
                    claude, args.model, skill if condition == "skill" else "", args.budget_per_run,
                )
                pair_results[condition] = counts
                print(json.dumps({"pair": pair, "condition": condition, "model": args.model, **counts}), flush=True)
            baseline, treatment = pair_results["baseline"], pair_results["skill"]
            if baseline["passed"] and treatment["passed"] and baseline["total_tokens"] > 0:
                savings.append(100 * (baseline["total_tokens"] - treatment["total_tokens"]) / baseline["total_tokens"])
    except (OSError, IndexError, ValueError, subprocess.TimeoutExpired) as error:
        print(f"Benchmark stopped: {error}", file=sys.stderr)
        return 1

    print(json.dumps({
        "comparable_pairs": len(savings),
        "requested_pairs": args.pairs,
        "median_token_savings_pct": round(statistics.median(savings), 2) if savings else None,
    }))
    return 0 if len(savings) == args.pairs else 1


if __name__ == "__main__":
    sys.exit(main())
