# Related work

Leads came from a ChatGPT conversation on 2026-08-29, filed verbatim in
`raw/`. Every entry below was opened and checked on 2026-08-29 (arXiv abstract
page, publisher page, or vendor page); the status column says what was
confirmed and what the paper is allowed to say about it. Three entries were
carried over from the digital-minds paper's bib, where they were verified the
same way.

## Threshold sweeps, rules in context, on-device, routing

| paper | verified as | what the paper says | status |
|---|---|---|---|
| Chauhan and Pendyala, *Benchmarking LLM-Guided Control-Plane Policies for Backend Fault Isolation in HAProxy*, arXiv:2608.10532 (2026) | 15 open-weight models, five families, 0.35B to 35B, one fault-injection task; "a capability threshold near 3B active parameters"; Gemma 4 E2B clears it at 2B active while dense 3B Granite does not | closest design; the direct foil on active vs total | cited |
| Xu et al., *Benchmarking and Enhancing Rule Knowledge-Driven Reasoning of LLMs* (RULER), AAAI-26 | 32K verified questions from 1K expert rules; rule memorisation, single-rule, multi-rule | the construct, not the size question | cited |
| Liu et al., *MobileLLM*, ICML 2024, PMLR 235:32431-32454 | sub-billion on-device models; architecture matters at that scale | the deployment target | cited |
| Gunter et al., *Apple Intelligence Foundation Language Models*, arXiv:2407.21075 (2024, rev. 2026) | describes a ~3B on-device model plus a server model | the "Siri-class" size in the intro | cited |
| Hu et al., *RouterBench*, arXiv:2403.12031 (2024); Ong et al., *RouteLLM*, arXiv:2406.18665 (2024) | routing between cheaper and stronger models; 405K+ outcomes; preference-trained routers | the downstream consumer of a threshold | cited |

## Scaling, emergence, mixture of experts

| paper | verified as | what the paper says | status |
|---|---|---|---|
| Kaplan et al., *Scaling Laws for Neural Language Models*, arXiv:2001.08361 (2020) | power-law loss in model size, data, compute | loss is smooth; accuracy need not be | cited |
| Wei et al., *Emergent Abilities of Large Language Models*, TMLR 2022 | abilities absent in smaller models and present in larger | names the knee | cited |
| Schaeffer, Miranda, Koyejo, *Are Emergent Abilities of LLMs a Mirage?*, arXiv:2304.15004 (2023) | discontinuous metrics produce apparent emergence; continuous ones show smooth change | why we report exact and graded scores on the same items | cited |
| Fedus, Zoph, Shazeer, *Switch Transformers*, JMLR 2022 | sparse MoE: parameter count decoupled from compute per token | the MoE framing | cited |
| Clark et al., *Unified Scaling Laws for Routed Language Models*, arXiv:2202.01169 (2022) | routed models scale along an effective parameter count; parameters and compute are independent axes | what our two MoE points are consistent with | cited |

## Format, option order, tables, chain of thought, eval practice

| paper | verified as | what the paper says | status |
|---|---|---|---|
| Sclar et al., *Quantifying LMs' Sensitivity to Spurious Features in Prompt Design*, ICLR 2024 | formatting choices move accuracy by tens of points | our table-vs-rows effect is the same phenomenon | cited (from digital-minds bib) |
| Sui et al., *Table Meets LLM*, WSDM 2024, arXiv:2305.13062 | table serialisation, content order, partition marks change what a model reads | tabular-input sensitivity, directly on point | cited |
| Zheng et al., *LLMs Are Not Robust Multiple Choice Selectors*, ICLR 2024 | option-order sensitivity | why the order is fixed and the letter distribution reported | cited (from digital-minds bib) |
| Pezeshkpour and Hruschka, *LLMs Sensitivity to the Order of Options in MCQ*, Findings of NAACL 2024 | same | same | cited (from digital-minds bib) |
| Wei et al., *Chain-of-Thought Prompting Elicits Reasoning*, arXiv:2201.11903 (2022) | reasoning traces before the answer | why reasoning is allowed and the token budget is part of the instrument | cited |
| Biderman et al., *Lessons from the Trenches on Reproducible Evaluation of LMs*, arXiv:2405.14782 (2024) | practical harness pitfalls from the lm-eval-harness | the harness as a source of error | cited |

Model reports, verified: Llama 3 (arXiv:2407.21783), Gemma 3 (arXiv:2503.19786),
Qwen3 (arXiv:2505.09388), GPT-5 nano (OpenAI docs, snapshot 2025-08-07, no
parameter count), Claude Haiku 4.5 (Anthropic page, 2025-10-15, no parameter
count).

What the write-up claims about novelty, at most: the combination of a
reference-grounded procedural task with a code-generated key, closeness scored
beside exact match, a pre-registered replication, and a parameter sweep aimed
at a minimum-sufficient scale was not found in this search. Not "nobody has
done this"; the HAProxy paper does the sweep, RULER does the construct, Sui et
al. do the table-format question.
