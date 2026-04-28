# -*- coding: utf-8 -*-
"""
Context Compressor -- Intelligent context compression strategies.

Provides multiple compression strategies for managing context window
utilization in multi-agent workflows:

1. Summary compression: Extract key points from long text
2. Layer-aware compression: Compress by memory layer priority
3. Dependency compression: Compress dependency outputs for downstream tasks
4. Sliding window: Keep recent context, compress older content
"""

from __future__ import annotations

import logging
import re
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

CHARS_PER_TOKEN = 4

LAYER_PRIORITY = {
    "L5_identity": 1,
    "task_context": 2,
    "L2_working": 3,
    "team_memory": 4,
    "L4_experience": 5,
    "L3_reference": 6,
}


class CompressionStrategy(Enum):
    SUMMARY = "summary"
    LAYER_AWARE = "layer_aware"
    DEPENDENCY = "dependency"
    SLIDING_WINDOW = "sliding_window"


class CompressionResult:
    """Result of a compression operation."""

    def __init__(
        self,
        original_chars: int,
        compressed_chars: int,
        strategy: CompressionStrategy,
        layers_affected: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.original_chars = original_chars
        self.compressed_chars = compressed_chars
        self.strategy = strategy
        self.layers_affected = layers_affected
        self.metadata = metadata or {}

    @property
    def compression_ratio(self) -> float:
        if self.original_chars == 0:
            return 0.0
        return 1.0 - (self.compressed_chars / self.original_chars)

    @property
    def estimated_tokens_saved(self) -> int:
        return (self.original_chars - self.compressed_chars) // CHARS_PER_TOKEN

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_chars": self.original_chars,
            "compressed_chars": self.compressed_chars,
            "compression_ratio": round(self.compression_ratio, 4),
            "estimated_tokens_saved": self.estimated_tokens_saved,
            "strategy": self.strategy.value,
            "layers_affected": self.layers_affected,
            "metadata": self.metadata,
        }


class ContextCompressor:
    """Intelligent context compression with multiple strategies.

    Integrates with PromptBuilder to replace simple truncation
    with smart compression that preserves key information.
    """

    def __init__(
        self,
        max_context_tokens: int = 128000,
        target_utilization: float = 0.7,
    ):
        self.max_context_tokens = max_context_tokens
        self.target_utilization = target_utilization
        self.target_tokens = int(max_context_tokens * target_utilization)

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count from text length."""
        return max(1, len(text) // CHARS_PER_TOKEN)

    def compress(
        self,
        memory_layers: Dict[str, str],
        task_context: str = "",
        strategy: CompressionStrategy = CompressionStrategy.LAYER_AWARE,
        target_tokens: Optional[int] = None,
    ) -> Tuple[Dict[str, str], str, CompressionResult]:
        """Compress context using the specified strategy.

        Args:
            memory_layers: Dict of layer_name -> content
            task_context: Current task context string
            strategy: Compression strategy to use
            target_tokens: Target token count (defaults to self.target_tokens)

        Returns:
            Tuple of (compressed_layers, compressed_task_context, result)
        """
        target = target_tokens or self.target_tokens

        total_chars = sum(len(v) for v in memory_layers.values()) + len(task_context)
        total_tokens = self.estimate_tokens(task_context) + sum(
            self.estimate_tokens(v) for v in memory_layers.values()
        )

        if total_tokens <= target:
            result = CompressionResult(
                original_chars=total_chars,
                compressed_chars=total_chars,
                strategy=strategy,
                layers_affected=[],
                metadata={"skipped": True, "reason": "already within budget"},
            )
            return memory_layers, task_context, result

        if strategy == CompressionStrategy.LAYER_AWARE:
            return self._compress_layer_aware(memory_layers, task_context, target)
        elif strategy == CompressionStrategy.SUMMARY:
            return self._compress_summary(memory_layers, task_context, target)
        elif strategy == CompressionStrategy.DEPENDENCY:
            return self._compress_dependency(memory_layers, task_context, target)
        elif strategy == CompressionStrategy.SLIDING_WINDOW:
            return self._compress_sliding_window(memory_layers, task_context, target)

        return self._compress_layer_aware(memory_layers, task_context, target)

    def _compress_layer_aware(
        self,
        memory_layers: Dict[str, str],
        task_context: str,
        target_tokens: int,
    ) -> Tuple[Dict[str, str], str, CompressionResult]:
        """Compress by reducing lower-priority layers first.

        Priority order (highest first):
        1. L5 Identity (always keep)
        2. Task context (always keep, may truncate)
        3. L2 Working memory
        4. Team memory
        5. L4 Experience
        6. L3 Reference (compress first)
        """
        original_chars = sum(len(v) for v in memory_layers.values()) + len(task_context)
        compressed = dict(memory_layers)
        compressed_ctx = task_context
        layers_affected = []

        sorted_layers = sorted(
            memory_layers.keys(),
            key=lambda k: LAYER_PRIORITY.get(k, 99),
            reverse=True,
        )

        identity_budget = self.estimate_tokens(compressed.get("L5_identity", ""))
        context_budget = self.estimate_tokens(compressed_ctx)
        reserved = identity_budget + context_budget
        remaining_budget = target_tokens - reserved

        if remaining_budget <= 0:
            remaining_budget = target_tokens // 2
            if len(compressed_ctx) > 0:
                max_ctx_chars = remaining_budget * CHARS_PER_TOKEN // 2
                compressed_ctx = self._extract_key_points(compressed_ctx, max_ctx_chars)

        layer_budgets = self._allocate_layer_budgets(sorted_layers, remaining_budget)

        for layer_name in sorted_layers:
            content = compressed.get(layer_name, "")
            if not content:
                continue

            budget = layer_budgets.get(layer_name, 0)
            current_tokens = self.estimate_tokens(content)

            if current_tokens > budget:
                max_chars = budget * CHARS_PER_TOKEN
                if layer_name in ("L3_reference", "L4_experience"):
                    compressed[layer_name] = self._extract_key_points(content, max_chars)
                elif layer_name == "L2_working":
                    compressed[layer_name] = self._sliding_window_text(content, max_chars)
                else:
                    compressed[layer_name] = self._extract_key_points(content, max_chars)
                layers_affected.append(layer_name)

        compressed_chars = sum(len(v) for v in compressed.values()) + len(compressed_ctx)

        result = CompressionResult(
            original_chars=original_chars,
            compressed_chars=compressed_chars,
            strategy=CompressionStrategy.LAYER_AWARE,
            layers_affected=layers_affected,
            metadata={"layer_budgets": {k: v for k, v in layer_budgets.items() if v > 0}},
        )

        return compressed, compressed_ctx, result

    def _compress_summary(
        self,
        memory_layers: Dict[str, str],
        task_context: str,
        target_tokens: int,
    ) -> Tuple[Dict[str, str], str, CompressionResult]:
        """Compress by extracting key points from all layers."""
        original_chars = sum(len(v) for v in memory_layers.values()) + len(task_context)
        compressed = {}
        layers_affected = []

        per_layer_budget = target_tokens // max(len(memory_layers) + 1, 1)

        for layer_name, content in memory_layers.items():
            max_chars = per_layer_budget * CHARS_PER_TOKEN
            if len(content) > max_chars:
                compressed[layer_name] = self._extract_key_points(content, max_chars)
                layers_affected.append(layer_name)
            else:
                compressed[layer_name] = content

        ctx_budget = per_layer_budget * CHARS_PER_TOKEN
        compressed_ctx = task_context
        if len(task_context) > ctx_budget:
            compressed_ctx = self._extract_key_points(task_context, ctx_budget)

        compressed_chars = sum(len(v) for v in compressed.values()) + len(compressed_ctx)

        result = CompressionResult(
            original_chars=original_chars,
            compressed_chars=compressed_chars,
            strategy=CompressionStrategy.SUMMARY,
            layers_affected=layers_affected,
        )

        return compressed, compressed_ctx, result

    def _compress_dependency(
        self,
        memory_layers: Dict[str, str],
        task_context: str,
        target_tokens: int,
    ) -> Tuple[Dict[str, str], str, CompressionResult]:
        """Compress dependency outputs for downstream task context.

        Designed for TaskOrchestrator: compresses the combined
        dependency outputs into a concise summary.
        """
        original_chars = sum(len(v) for v in memory_layers.values()) + len(task_context)
        compressed = dict(memory_layers)
        compressed_ctx = task_context
        layers_affected = []

        dep_sections = re.split(r'\n---\n', task_context)
        if len(dep_sections) <= 1:
            return self._compress_layer_aware(memory_layers, task_context, target_tokens)

        total_ctx_tokens = self.estimate_tokens(task_context)
        if total_ctx_tokens <= target_tokens // 2:
            result = CompressionResult(
                original_chars=original_chars,
                compressed_chars=original_chars,
                strategy=CompressionStrategy.DEPENDENCY,
                layers_affected=[],
                metadata={"skipped": True},
            )
            return compressed, compressed_ctx, result

        per_dep_budget = (target_tokens // 2) // max(len(dep_sections), 1)
        compressed_deps = []

        for section in dep_sections:
            max_chars = per_dep_budget * CHARS_PER_TOKEN
            if len(section) > max_chars:
                compressed_deps.append(self._extract_key_points(section, max_chars))
            else:
                compressed_deps.append(section)

        compressed_ctx = "\n---\n".join(compressed_deps)
        if "dependency" not in layers_affected:
            layers_affected.append("dependency_context")

        remaining_budget = target_tokens - self.estimate_tokens(compressed_ctx)
        if remaining_budget > 0:
            for layer_name in sorted(
                memory_layers.keys(),
                key=lambda k: LAYER_PRIORITY.get(k, 99),
                reverse=True,
            ):
                content = compressed.get(layer_name, "")
                if not content:
                    continue
                layer_tokens = self.estimate_tokens(content)
                if layer_tokens > remaining_budget // max(len(memory_layers), 1):
                    max_chars = (remaining_budget // max(len(memory_layers), 1)) * CHARS_PER_TOKEN
                    compressed[layer_name] = self._extract_key_points(content, max_chars)
                    layers_affected.append(layer_name)

        compressed_chars = sum(len(v) for v in compressed.values()) + len(compressed_ctx)

        result = CompressionResult(
            original_chars=original_chars,
            compressed_chars=compressed_chars,
            strategy=CompressionStrategy.DEPENDENCY,
            layers_affected=layers_affected,
        )

        return compressed, compressed_ctx, result

    def _compress_sliding_window(
        self,
        memory_layers: Dict[str, str],
        task_context: str,
        target_tokens: int,
    ) -> Tuple[Dict[str, str], str, CompressionResult]:
        """Compress by keeping recent content and summarizing older content.

        For each layer, keeps the last N chars and summarizes the rest.
        """
        original_chars = sum(len(v) for v in memory_layers.values()) + len(task_context)
        compressed = {}
        layers_affected = []

        per_layer_budget = target_tokens // max(len(memory_layers) + 1, 1)

        for layer_name, content in memory_layers.items():
            max_chars = per_layer_budget * CHARS_PER_TOKEN
            if len(content) > max_chars:
                compressed[layer_name] = self._sliding_window_text(content, max_chars)
                layers_affected.append(layer_name)
            else:
                compressed[layer_name] = content

        ctx_budget = per_layer_budget * CHARS_PER_TOKEN
        compressed_ctx = task_context
        if len(task_context) > ctx_budget:
            compressed_ctx = self._sliding_window_text(task_context, ctx_budget)

        compressed_chars = sum(len(v) for v in compressed.values()) + len(compressed_ctx)

        result = CompressionResult(
            original_chars=original_chars,
            compressed_chars=compressed_chars,
            strategy=CompressionStrategy.SLIDING_WINDOW,
            layers_affected=layers_affected,
        )

        return compressed, compressed_ctx, result

    def _extract_key_points(self, text: str, max_chars: int) -> str:
        """Extract key points from text to fit within max_chars.

        Strategy:
        1. Extract headers (## lines)
        2. Extract first sentence of each paragraph
        3. Keep bullet points
        4. Truncate if still too long
        """
        if len(text) <= max_chars:
            return text

        lines = text.splitlines()
        key_lines = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            if stripped.startswith("#"):
                key_lines.append(stripped)
            elif stripped.startswith("- ") or stripped.startswith("* ") or stripped.startswith("• "):
                key_lines.append(stripped)
            elif stripped.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.")):
                key_lines.append(stripped)
            elif any(stripped.startswith(f"{i}.") for i in range(1, 20)):
                key_lines.append(stripped)
            elif ":" in stripped and len(stripped) < 120:
                key_lines.append(stripped)

        result = "\n".join(key_lines)

        if len(result) > max_chars:
            result = self._sliding_window_text(result, max_chars)

        if len(result) < max_chars // 3:
            result = self._sliding_window_text(text, max_chars)

        return result

    def _sliding_window_text(self, text: str, max_chars: int) -> str:
        """Keep the most recent content that fits in max_chars.

        Preserves line boundaries. Adds a summary header.
        """
        if len(text) <= max_chars:
            return text

        header = f"[...前文已压缩，保留最近 {max_chars} 字符...]\n"
        available = max_chars - len(header)
        if available <= 0:
            return text[:max_chars]

        truncated = text[-available:]
        newline_pos = truncated.find("\n")
        if newline_pos > 0 and newline_pos < available // 2:
            truncated = truncated[newline_pos + 1:]

        return header + truncated

    def _allocate_layer_budgets(
        self,
        layers: List[str],
        total_budget: int,
    ) -> Dict[str, int]:
        """Allocate token budget across layers based on priority."""
        if not layers:
            return {}

        high_priority = []
        low_priority = []

        for layer in layers:
            if LAYER_PRIORITY.get(layer, 99) <= 3:
                high_priority.append(layer)
            else:
                low_priority.append(layer)

        budgets = {}

        if high_priority:
            hp_budget = int(total_budget * 0.6)
            per_hp = hp_budget // len(high_priority)
            for layer in high_priority:
                budgets[layer] = per_hp

        if low_priority:
            lp_budget = total_budget - sum(budgets.values())
            per_lp = lp_budget // len(low_priority)
            for layer in low_priority:
                budgets[layer] = per_lp

        return budgets
