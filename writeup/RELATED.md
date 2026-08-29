# Related work

Leads came from a ChatGPT conversation on 2026-08-29, filed verbatim in
`raw/`. Each was then opened and checked on 2026-08-29; the status column says
what was confirmed and what the paper is allowed to say about it.

| # | paper | verified as | what the paper says | status |
|---|---|---|---|---|
| 1 | Chauhan and Pendyala, *Benchmarking LLM-Guided Control-Plane Policies for Backend Fault Isolation in HAProxy*, arXiv:2608.10532 (2026) | 15 open-weight models, five families, 0.35B to 35B, one fault-injection task, 240 configurations; abstract states "a capability threshold near 3B active parameters", below which models are "typically unreliable and sometimes worse than no policy", above which they saturate; notes Gemma 4 E2B clears it at 2B active while dense 3B Granite does not | the closest design to ours and the direct foil on the active-vs-total question: their threshold is in active parameters, our 3.3B-active MoE behaves like a 30B model | VERIFIED, cited |
| 2 | Xu et al., *Benchmarking and Enhancing Rule Knowledge-Driven Reasoning of Large Language Models* (RULER), AAAI-26 | 32K verified questions from 1K expert emergency-response rules; tests rule memorisation, single-rule application, multi-rule reasoning; proposes RAMPS | the construct (rules supplied, application scored), not the size question | VERIFIED, cited |
| 3 | Liu et al., *MobileLLM: Optimizing Sub-billion Parameter Language Models for On-Device Use Cases*, ICML 2024, PMLR 235:32431-32454 | sub-billion models for mobile; architecture matters at that scale; API-calling as a practical task | the deployment target; they compare architectures on conventional tasks rather than locating a knee on one held task | VERIFIED, cited |
| 4 | Hu et al., *RouterBench: A Benchmark for Multi-LLM Routing System*, arXiv:2403.12031 (2024); Ong et al., *RouteLLM: Learning to Route LLMs with Preference Data*, arXiv:2406.18665 (2024) | RouterBench: 405K+ inference outcomes and a routing framework; RouteLLM: routers trained on preference data choosing between a strong and a weak model | the downstream consumer of a threshold like ours; neither constructs a diagnostic task to locate one | VERIFIED, cited |

Model reports, verified on arXiv and vendor pages the same day: Llama 3
(Grattafiori et al., arXiv:2407.21783, 2024), Gemma 3 (Gemma Team,
arXiv:2503.19786, 2025), Qwen3 (Yang et al., arXiv:2505.09388, 2025; abstract
confirms dense and MoE variants from 0.6B to 235B), GPT-5 nano (OpenAI model
documentation, snapshot gpt-5-nano-2025-08-07, no parameter count disclosed),
Claude Haiku 4.5 (Anthropic model page, released 2025-10-15, no parameter
count disclosed).

What the write-up claims about novelty, at most: the combination of a
reference-grounded procedural task with a code-generated key, closeness scored
beside exact match, a pre-registered replication, and a parameter sweep aimed
at a minimum-sufficient scale was not found in this search. Not "nobody has
done this"; the HAProxy paper does the sweep, RULER does the construct.

Not yet searched: format-sensitivity of tabular inputs to LLMs (the table vs
rows effect surely has prior work), and position bias in fixed-order MCQA.
Both are worth a pass before a conference submission.
