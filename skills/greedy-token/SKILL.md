---
name: greedy-token
description: Reduce token use on coding tasks when asked for Greedy Token, low-token mode, or less context. Scope file reads, tool output, and replies while preserving correctness and verification.
---

# Greedy Token

- Start from the request, relevant instructions, and facts already gathered. Search exact paths, symbols, or error strings first. Read matching sections and nearby callers. Widen the scope when uncertainty, dependencies, or the requested review requires it.
- Ask tools for relevant fields, paths, or line ranges. Keep verbose logs out of model context and retrieve the failure, exit status, and useful surrounding lines. Expand when an excerpt hides the cause or may omit relevant results.
- Reuse unchanged evidence. Reread after edits or when freshness matters. Batch independent checks when that reduces calls without flooding context.
- Follow project requirements and run the checks needed for the change. Preserve errors, edge cases, and evidence needed to verify the result. Treat output limits as adjustable, especially for audits and cross-cutting changes.
- Reply with the result, verification, and any material gaps. Match the user's requested detail. Cite actual usage data when reporting token savings.
