# Greedy Token

An opt-in Agent Skill for token-conscious coding. It keeps file reads and tool results focused, reuses context already gathered, and keeps final reports concise. It expands the search when the task needs broader evidence.

## Use in a project

Run the applicable command from the Greedy Token repository. Replace `/path/to/project` with the target repository and choose a destination that does not already contain this skill.

| Client | Copy command | Example prompt |
| --- | --- | --- |
| Claude Code | `mkdir -p /path/to/project/.claude/skills && cp -R skills/greedy-token /path/to/project/.claude/skills/` | `/greedy-token Fix the failing checkout test and verify the fix.` |
| Codex | `mkdir -p /path/to/project/.agents/skills && cp -R skills/greedy-token /path/to/project/.agents/skills/` | `$greedy-token Find why the checkout test fails, then fix and verify it.` |

Start a session in the target project. See the [Claude Code skills docs](https://code.claude.com/docs/en/skills) and [Codex skills docs](https://developers.openai.com/codex/skills) for discovery and invocation details.

## Measure the effect

Run the same task in fresh sessions with and without the skill. Keep the model, settings, repository revision, and acceptance tests fixed. Compare the resulting patches and check results before comparing token use. Include the skill's own context overhead in the totals.

Record input, cached input, and output tokens separately, using the client's reported counts when available. Repeat on both a narrow bug fix and a change that requires reading across files. The skill guides model behavior. It does not enforce a token cap. Savings have yet to be benchmarked.

### Run the Claude Code benchmark

The benchmark creates a fresh synthetic checkout project for each run and
checks the resulting code against the same five cases. Both conditions get
the same task and tools. The skill condition adds the Markdown instructions
to the system prompt, so their token cost is included. This setup measures
the instructions under direct loading. Skill discovery is outside the benchmark.

Use Python 3.9+ and a Claude Code version that supports `--bare`. Configure
credentials supported by [bare mode](https://code.claude.com/docs/en/headless#start-faster-with-bare-mode)
and use an exact model ID available to your account. This command makes two
model runs per pair and can incur API charges.

```sh
python3 benchmarks/claude_tokens.py --model YOUR_MODEL_ID --pairs 3 --budget-per-run 0.25
```

Each JSON line reports the outcome and all four token counters. The total
includes uncached input, cache writes, cache reads, and output. It measures
token volume. Compare the cache counters separately to analyze billing.
The script alternates condition order and reports median savings from pairs
where both changes pass. A negative percentage means the skill used more
tokens. A nonzero exit indicates an incomplete or failed comparison.
