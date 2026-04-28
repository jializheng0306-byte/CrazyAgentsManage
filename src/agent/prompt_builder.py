# -*- coding: utf-8 -*-
"""
Prompt Builder -- Enhanced system prompt construction with memory integration.

Builds system prompts that automatically incorporate:
- L5 identity memory (always loaded)
- L4 experience memory (loaded by relevance)
- L3 reference memory (loaded by relevance)
- L2 working memory (current task context)
- Team memory (when team context is active)
- Role-specific prompt templates

v0.4.0: Added ContextCompressor integration for intelligent compression
         replacing simple truncation with layer-aware compression.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from src.agent.agent_factory import AgentRole, get_role_prompt, resolve_role
from src.agent.context_compressor import CompressionStrategy, ContextCompressor
from src.memory.memory_loader import MemoryLoader, MemoryLayer

logger = logging.getLogger(__name__)

DEFAULT_MAX_MEMORY_CHARS = 8000
DEFAULT_MAX_CONTEXT_TOKENS = 128000


class PromptBuilder:
    """Builds system prompts with integrated memory layers.

    v0.4.0: Supports intelligent context compression via ContextCompressor.
    When max_context_tokens is set, the builder will automatically compress
    memory layers using layer-aware compression instead of simple truncation.
    """

    def __init__(
        self,
        memory_loader: Optional[MemoryLoader] = None,
        max_memory_chars: int = DEFAULT_MAX_MEMORY_CHARS,
        max_context_tokens: int = DEFAULT_MAX_CONTEXT_TOKENS,
        compressor: Optional[ContextCompressor] = None,
    ):
        self.memory_loader = memory_loader or MemoryLoader()
        self.max_memory_chars = max_memory_chars
        self.max_context_tokens = max_context_tokens
        self.compressor = compressor or ContextCompressor(
            max_context_tokens=max_context_tokens,
        )

    def build_system_prompt(
        self,
        role: str,
        goal: str,
        context: str = "",
        task_id: str = "",
        team: str = "",
        session_prompt: str = "",
    ) -> str:
        """Build a complete system prompt with memory integration.

        Args:
            role: Role name or alias.
            goal: Task goal description.
            context: Additional context.
            task_id: Current task ID for working memory.
            team: Team name for team memory.
            session_prompt: Existing session system prompt (L1).

        Returns:
            Complete system prompt string.
        """
        resolved_role = resolve_role(role)
        role_prompt = get_role_prompt(resolved_role, goal, context)

        memory_parts = self._load_relevant_memory(
            task_id=task_id,
            team=team,
            context=f"{goal} {context}",
        )

        parts = [role_prompt]

        if memory_parts:
            parts.append("")
            parts.append("## Relevant Memory")
            parts.append("")
            for layer_name, content in memory_parts.items():
                display = MemoryLayer.display_name(layer_name)
                truncated = self._truncate(content, self.max_memory_chars // max(len(memory_parts), 1))
                parts.append(f"### {display}")
                parts.append(truncated)
                parts.append("")

        if session_prompt:
            parts.append("")
            parts.append("## Session Context")
            parts.append(session_prompt)

        return "\n".join(parts)

    def build_system_prompt_with_memory(
        self,
        role: str,
        goal: str,
        context: str = "",
        task_id: str = "",
        team: str = "",
        layers: Optional[List[str]] = None,
        use_compression: bool = True,
    ) -> str:
        """Build system prompt with explicit memory layer control.

        This is the main entry point for the Prompt Builder enhancement
        described in the v0.2.0 roadmap, with v0.4.0 compression support.

        Loading strategy:
        - L5 identity: Always loaded
        - L4 experience: Loaded by relevance to goal/context
        - L3 reference: Loaded by relevance
        - L2 working: Loaded when task_id is provided
        - Team memory: Loaded when team is provided

        v0.4.0: When use_compression=True and total estimated tokens exceed
        the budget, ContextCompressor is used instead of simple truncation.
        """
        resolved_role = resolve_role(role)
        role_prompt = get_role_prompt(resolved_role, goal, context)

        target_layers = layers or [
            MemoryLayer.L5_IDENTITY,
            MemoryLayer.L4_EXPERIENCE,
            MemoryLayer.L3_REFERENCE,
        ]

        if task_id:
            target_layers.append(MemoryLayer.L2_WORKING)

        memory_parts = self.memory_loader.load_all(
            task_id=task_id,
            team=team,
            context=f"{goal} {context}",
            layers=target_layers,
        )

        if use_compression and memory_parts:
            compressed_layers, compressed_ctx, result = self.compressor.compress(
                memory_layers=memory_parts,
                task_context=context,
                strategy=CompressionStrategy.LAYER_AWARE,
            )
            if result.compression_ratio > 0:
                logger.info(
                    f"Context compressed: {result.compression_ratio:.1%} reduction, "
                    f"{result.estimated_tokens_saved} tokens saved, "
                    f"layers affected: {result.layers_affected}"
                )
            memory_parts = compressed_layers
            context = compressed_ctx

        parts = [role_prompt]

        if memory_parts:
            parts.append("")
            parts.append("## Memory Context")
            parts.append("")
            per_layer_budget = self.max_memory_chars // max(len(memory_parts), 1)
            for layer_name, content in memory_parts.items():
                display = MemoryLayer.display_name(layer_name)
                if use_compression:
                    truncated = self._truncate(content, per_layer_budget)
                else:
                    truncated = self._truncate(content, per_layer_budget)
                parts.append(f"### {display}")
                parts.append(truncated)
                parts.append("")

        if context:
            parts.append("")
            parts.append("## Task Context")
            parts.append(context)

        return "\n".join(parts)

    def _load_relevant_memory(
        self,
        task_id: str = "",
        team: str = "",
        context: str = "",
    ) -> Dict[str, str]:
        """Load relevant memory layers based on context."""
        layers = [MemoryLayer.L5_IDENTITY]

        if context:
            layers.extend([MemoryLayer.L4_EXPERIENCE, MemoryLayer.L3_REFERENCE])

        if task_id:
            layers.append(MemoryLayer.L2_WORKING)

        return self.memory_loader.load_all(
            task_id=task_id,
            team=team,
            context=context,
            layers=layers,
        )

    def _truncate(self, text: str, max_chars: int) -> str:
        """Truncate text to max_chars, preserving line boundaries."""
        if len(text) <= max_chars:
            return text
        truncated = text[:max_chars]
        last_newline = truncated.rfind("\n")
        if last_newline > max_chars // 2:
            truncated = truncated[:last_newline]
        return truncated + "\n\n[... truncated]"

    def get_prompt_stats(self, prompt: str) -> Dict[str, Any]:
        """Get statistics about a built prompt."""
        memory_sections = prompt.count("### ")
        total_chars = len(prompt)
        estimated_tokens = total_chars // 4

        return {
            "total_chars": total_chars,
            "estimated_tokens": estimated_tokens,
            "memory_sections": memory_sections,
            "token_budget": self.max_context_tokens,
            "utilization": round(estimated_tokens / max(self.max_context_tokens, 1), 4),
            "has_identity": "身份记忆" in prompt or "Identity" in prompt,
            "has_experience": "经验记忆" in prompt or "Experience" in prompt,
            "has_reference": "参考记忆" in prompt or "Reference" in prompt,
            "has_team": "团队记忆" in prompt or "Team Memory" in prompt,
            "has_compression": "前文已压缩" in prompt,
        }
