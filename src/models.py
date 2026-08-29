"""The model ladder: one registry, every field the scaling curve needs.

Parameter counts are the published figures for each checkpoint; MoE models
carry both total and active so the curve can be drawn on either x-axis.
The host and quantisation are pinned per model (FINDINGS D-009): the host
is part of the instrument. Nothing downstream types a parameter count.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Model:
    id: str                 # OpenRouter id
    family: str
    params_total_b: float   # billions
    params_active_b: float  # billions; equals total for dense models
    quant: str              # as OpenRouter reports for the pinned host
    host: str               # OpenRouter provider name, pinned with allow_fallbacks=false
    max_tokens: int = 1024  # 4096 for reasoning models (D-007)
    note: str = ""

    @property
    def moe(self) -> bool:
        return self.params_active_b != self.params_total_b

    @property
    def inspect_model(self) -> str:
        return f"openrouter/{self.id}"

    @property
    def provider_arg(self) -> str:
        return f'provider={{"order":["{self.host}"],"allow_fallbacks":false}}'


LADDER: list[Model] = [
    Model("meta-llama/llama-3.2-1b-instruct", "llama-3", 1.24, 1.24, "unknown", "Cloudflare", note="only host; the one that 500'd in D-009, host errors watched"),
    Model("meta-llama/llama-3.2-3b-instruct", "llama-3", 3.21, 3.21, "bf16", "Parasail"),
    Model("google/gemma-3-4b-it", "gemma-3", 4.3, 4.3, "bf16", "DeepInfra"),
    Model("meta-llama/llama-3.1-8b-instruct", "llama-3", 8.03, 8.03, "fp8", "DeepInfra", note="no bf16 host under $0.20 per M; fp8 recorded"),
    Model("google/gemma-3-12b-it", "gemma-3", 12.2, 12.2, "bf16", "DeepInfra"),
    Model("google/gemma-3-27b-it", "gemma-3", 27.4, 27.4, "bf16", "Novita", note="bf16 chosen over cheaper fp8 to keep the family at one quantisation"),
    Model("qwen/qwen3-30b-a3b-instruct-2507", "qwen-3", 30.5, 3.3, "bf16", "CoreWeave", note="MoE: 3.3B active"),
    Model("qwen/qwen3-32b", "qwen-3", 32.8, 32.8, "fp8", "DeepInfra", note="dense pair for the 30B-A3B MoE; no bf16 host"),
    Model("qwen/qwen3-235b-a22b-2507", "qwen-3", 235.0, 22.0, "fp8", "GMICloud", note="MoE: 22B active; dev runs were spread over ten hosts (D-009)"),
    Model("openai/gpt-5-nano", "gpt-5", float("nan"), float("nan"), "unknown", "Azure", max_tokens=4096, note="ceiling reference; size undisclosed, not on the curve. Pinned to Azure (served every dev call); pinning 'OpenAI' returned 404 No endpoints found"),
    # REVIEW4.md: the Qwen3 dense rungs below the 32B, same thinking regime as the 32B (hybrid model,
    # reasoning on by default), 4,096 tokens like the 32B rerun. Run into their own log dir, not logs/pinned.
    Model("qwen/qwen3-8b", "qwen-3", 8.2, 8.2, "unknown", "Alibaba", max_tokens=4096, note="REVIEW4 run 1; only host on OpenRouter, quantisation not reported"),
    Model("qwen/qwen3-14b", "qwen-3", 14.8, 14.8, "fp8", "DeepInfra", max_tokens=4096, note="REVIEW4 run 1; same host and quantisation as the 32B"),
]

# Dev-only models, reported as dev numbers and not on the pinned curve (D-010).
DEV_ONLY: list[Model] = [
    Model("anthropic/claude-haiku-4.5", "claude", float("nan"), float("nan"), "unknown", "Anthropic", note="size undisclosed; $1.60 per pinned pass"),
    Model("google/gemini-2.5-flash-lite", "gemini", float("nan"), float("nan"), "unknown", "Google", note="size undisclosed"),
]

BY_ID: dict[str, Model] = {m.id: m for m in LADDER + DEV_ONLY}
