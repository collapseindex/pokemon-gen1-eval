# Related work

Pointers for the write-up. Source: a ChatGPT conversation on 2026-08-29,
filed verbatim in `raw/`. Nothing here is cited until it has been opened and
the claim checked against the paper; the status column says where each one
is. A chat-sourced citation is a lead, not a reference.

| # | paper | why it matters here | status |
|---|---|---|---|
| 1 | HAProxy control-plane benchmark, arXiv 2608.10532 (2026) | same question (smallest reliable model for one bounded task), 15 open models 0.35B to 35B, threshold claimed near 3B active | UNVERIFIED: open the paper, confirm the sweep and the threshold claim, check whether "active" is their word |
| 2 | RULER, AAAI 2026 (ojs.aaai.org 40714) | rule knowledge given in context, single- and multi-rule application scored; the construct, not the size question | UNVERIFIED: confirm title, venue, and that rules are supplied in context |
| 3 | MobileLLM, PMLR v235 (ICML 2024) | sub-billion models for on-device use; the deployment target | UNVERIFIED: confirm venue and which tasks they benchmark |
| 4 | RouterBench, arXiv 2403.12031; RouteLLM | routing weak vs strong models on cost/quality; the downstream use of a threshold like ours | UNVERIFIED: confirm RouterBench scale; find the RouteLLM reference separately |

What the write-up can claim about novelty, at most: the combination of a
reference-grounded procedural task, a code-generated key, closeness scored
beside exact match, and a parameter sweep aimed at a minimum-sufficient
scale was not found in a light search. Not "nobody has done this."

Framing worth keeping from the conversation: the result is a knee, not a
winner; "active parameters" is the axis the MoE points test (A7); and the
natural extension is a capability-cost frontier once latency and memory
per model are measured, which this project does not do.
