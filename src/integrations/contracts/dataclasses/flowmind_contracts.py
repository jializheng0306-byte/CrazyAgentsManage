"""
FlowMind cross-repo contracts (GENERATED — DO NOT EDIT).

Source: FlowMindDeploy packages/ontology/semantic-dsl/objects/crazy.*.md
Generator: packages/ontology/src/generators/cross-repo-contract-generator.ts
Direction: FMD generates, Crazy consumes (irreversible, AGENTS.md decision tree 7).

Guards:
  Invariant 1: contracts do not adjudicate truth.status
  Invariant 2: evidence_class passed through unchanged
  Invariant 3: read-only consumption, no new truth invented
  R13: accessPolicy.allowStateDecision passed through (TaskTransmission guard)
  isDefinedBy ∈ {flowmind, team, host_pimo}
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional


@dataclass(kw_only=True)
class AccessPolicy:
    """TaskTransmission access policy (R13 guard: allowStateDecision passed through)."""
    allowDistribution: bool
    allowSubscribers: bool
    allowModifications: bool
    allowStateDecision: bool
    allowCopying: bool


@dataclass(kw_only=True)
class AgentTask:
    """Agent Task — evidence_class: INFERRED (Invariant 2: passed through)."""
    taskId: str
    assignedTo: str
    status: Literal["new", "running", "completed", "suspended", "archived", "deleted"]
    priority: Optional[int] = None
    contextTags: Optional[list[str]] = None
    dueDate: Optional[datetime] = None
    targetStart: Optional[datetime] = None
    actualStart: Optional[datetime] = None
    targetCompletion: Optional[datetime] = None
    actualCompletion: Optional[datetime] = None
    relatedCandidateId: Optional[str] = None
    relatedPromiseId: Optional[str] = None
    accessPolicy: AccessPolicy
    createdAt: datetime
    updatedAt: datetime


@dataclass(kw_only=True)
class Promise:
    """Promise — evidence_class: INFERRED (Invariant 2: passed through)."""
    promise_id: str
    status: Literal["pending", "in_progress", "blocked", "done", "completed", "expired", "rejected"]
    priority: Optional[Literal["P0", "P1", "P2", "P3"]] = None
    flowmind_candidate_id: Optional[str] = None


@dataclass(kw_only=True)
class TraceEvent:
    """Crazy Trace Event — evidence_class: EXTRACTED (Invariant 2: passed through)."""
    trace_id: str
    promise_id: str
    flowmind_module: str
    timestamp: datetime

