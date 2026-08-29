# Raw: related-work conversation with ChatGPT, 2026-08-29

Pasted verbatim from Alex's chat. Citations NOT verified at time of filing; see
../RELATED.md for the verification status of each. The example curve in the
text (1B 19% ... 70B 99%) is hypothetical and is not a result of this project.

---

ROFLLLL yes, but I'm not finding many people doing your exact combination. There's a bunch of adjacent work, and one recent paper is surprisingly close to your research question.

The closest thing I found is a 2026 HAProxy control-plane benchmark that swept 15 open-weight models from 0.35B to 35B on one bounded operational task and explicitly asked where the capability threshold appears. They found an approximate threshold around ~3B active parameters: below it the models were generally unreliable, while above it performance largely saturated. That is basically your methodological question ("what is the smallest model that can reliably perform this class of task?") just applied to backend fault isolation rather than reference lookup + deterministic rules. [1]

Then there's RULER (AAAI 2026), which is close to the construct you're measuring. It gives models rule knowledge and tests single-rule application and multi-rule reasoning, rather than simply asking what they memorized. That maps nicely to your "here's the Gen 1 reference material; now apply it" setup. But RULER is mainly interested in reasoning performance and methods for improving it, not finding the smallest deployable model that clears a reliability threshold. [2]

On the device side, MobileLLM explicitly studies sub-billion-parameter models for on-device use cases and benchmarks things like commonsense reasoning, chat, and API calling. So they absolutely care about "how small can useful models get?" But again, they're mostly comparing model architectures/training recipes across conventional tasks, rather than holding one tightly controlled task constant and locating its capability knee as parameter count scales. [3]

And then RouterBench / RouteLLM are basically the downstream engineering consequence of what you're talking about. They ask how to route easier requests to cheaper/weaker models and hard requests to stronger ones, optimizing cost versus quality. RouterBench has hundreds of thousands of model outcomes; RouteLLM actually trains routers to select between weak and strong models. But they generally learn routing from performance data across existing benchmarks; they're not specifically constructing a diagnostic eval designed to say "this bounded capability emerges around 8B, therefore route this task class to >=8B." [4]

| Existing direction | Your version |
|---|---|
| Benchmark models broadly | Benchmark one narrow deployable capability deeply |
| Rank models | Find minimum sufficient model scale |
| Mix knowledge + reasoning | Give all required knowledge in-context |
| Open-ended scoring often used | Deterministic ground truth/scoring |
| Report overall accuracy | Diagnose parse -> lookup -> orientation -> combine errors |
| Compare unrelated models | Potentially sweep one family across parameter scales |
| Cost optimization after benchmarking | Benchmark is explicitly designed to inform routing/deployment |

The one-family sweep is particularly nice scientifically. If you can do something like 1B -> 3B -> 8B -> 14B -> 32B -> 70B within one training family, you remove a bunch of the "well Gemma was trained differently from Llama" nonsense. Then the x-axis is much closer to capacity/scale, rather than "a grab bag of model identities."

And your explicit-reference design matters a LOT. Suppose your curve eventually looks like: 1B: 19%, 3B: 18%, 4B: 34%, 8B: 79%, 12B: 96%, 32B: 99%, 70B: 99%. The interesting result isn't "70B wins." It's: "Reference-grounded lookup + two-factor deterministic rule application exhibits a sharp capability transition between approximately 4B and 12B parameters, with negligible gains beyond 12B." Now an app engineer can legitimately ask: why am I routing this operation to a 70B model?

Even better, once you add latency/RAM/quantization measurements, you can produce a capability-cost frontier. Then your endpoint becomes something like: "Smallest configuration meeting 95% reliability: 12B Q4, X GB RAM, Y ms median latency."

So: people are definitely studying all the pieces. Capability thresholds, small-model deployment, rule-grounded reasoning, and LLM routing all exist. But from the literature I checked, I didn't find an established benchmark doing your exact package: controlled reference-grounded procedural task + deterministic scoring + model-size scaling specifically to identify the minimum deployable capability threshold. I would not claim "nobody has ever done this" without a proper literature review.

[1] https://arxiv.org/abs/2608.10532  Benchmarking LLM-Guided Control-Plane Policies for Backend Fault Isolation in HAProxy
[2] https://ojs.aaai.org/index.php/AAAI/article/view/40714  Benchmarking and Enhancing Rule Knowledge-Driven Reasoning of Large Language Models (RULER)
[3] https://proceedings.mlr.press/v235/liu24ce.html  MobileLLM: Optimizing Sub-billion Parameter Language Models for On-Device Use Cases
[4] https://arxiv.org/abs/2403.12031  RouterBench: A Benchmark for Multi-LLM Routing System
