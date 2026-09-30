"""
Adaptive Error-Guided Memory Governance (AEMG)
Implements generalized repair knowledge storage, vector/semantic retrieval,
confidence scoring, temporal decay, and self-pruning.
"""

import json
import math
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class MemoryItem(BaseModel):
    id: str
    error_category: str
    trigger_pattern: str
    generalized_rule: str
    target_tables: List[str] = Field(default_factory=list)
    confidence_score: float = 0.85
    usage_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    last_accessed_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    decay_rate: float = 0.05  # lambda decay parameter

    def apply_decay(self, decay_factor: Optional[float] = None) -> float:
        """Applies mathematical decay function C(t) = C_0 * e^(-lambda * dt)"""
        rate = decay_factor if decay_factor is not None else self.decay_rate
        self.confidence_score = max(0.0, round(self.confidence_score * math.exp(-rate), 4))
        return self.confidence_score

    def record_usage(self, success: bool):
        self.usage_count += 1
        self.last_accessed_at = datetime.now().isoformat()
        if success:
            self.success_count += 1
            # Successful usage increases confidence (+0.08, capped at 1.0)
            self.confidence_score = min(1.0, round(self.confidence_score + 0.08, 4))
        else:
            self.failure_count += 1
            # Unsuccessful usage decreases confidence (-0.15)
            self.confidence_score = max(0.0, round(self.confidence_score - 0.15, 4))


class MemoryGovernance:
    def __init__(self, persistence_path: str = "memory_store.json", pruning_threshold: float = 0.35):
        self.persistence_path = persistence_path
        self.pruning_threshold = pruning_threshold
        self.memories: Dict[str, MemoryItem] = {}
        self.load()
        if not self.memories:
            self._seed_default_foundational_memories()

    def _seed_default_foundational_memories(self):
        """Seeds foundational enterprise repair patterns derived from past validation and runtime failures."""
        initial_rules = [
            MemoryItem(
                id="mem_rule_01",
                error_category="COLUMN_HALLUCINATION",
                trigger_pattern="revenue sales_amount turn_over total_sales",
                generalized_rule="In fact_sales, the column representing total transaction monetary value is 'gross_revenue', not 'revenue' or 'sales_amount'. Always use 'fact_sales.gross_revenue'.",
                target_tables=["fact_sales"],
                confidence_score=0.92,
                decay_rate=0.03
            ),
            MemoryItem(
                id="mem_rule_02",
                error_category="GROUP_BY_MISSING_COLUMN",
                trigger_pattern="GROUP BY aggregate SUM AVG COUNT MIN MAX region market_type",
                generalized_rule="Whenever an aggregated column (e.g., SUM(profit), AVG(gross_revenue)) is selected with non-aggregated attributes (e.g., region, market_type, category), ensure ALL non-aggregated columns appear in the GROUP BY clause.",
                target_tables=["dim_store", "fact_sales", "dim_product"],
                confidence_score=0.95,
                decay_rate=0.02
            ),
            MemoryItem(
                id="mem_rule_03",
                error_category="STAR_SCHEMA_JOIN",
                trigger_pattern="store region product customer date join",
                generalized_rule="Always join fact_sales with dimensions using explicit foreign keys: fact_sales.store_id = dim_store.store_id, fact_sales.customer_id = dim_customer.customer_id, fact_sales.product_id = dim_product.product_id, fact_sales.date_id = dim_date.date_id.",
                target_tables=["fact_sales", "dim_store", "dim_customer", "dim_product", "dim_date"],
                confidence_score=0.90,
                decay_rate=0.02
            )
        ]
        for item in initial_rules:
            self.memories[item.id] = item
        self.save()

    def add_memory(
        self,
        error_category: str,
        trigger_pattern: str,
        generalized_rule: str,
        target_tables: Optional[List[str]] = None,
        initial_confidence: float = 0.85
    ) -> MemoryItem:
        """Registers newly diagnosed generalized repair knowledge."""
        item_id = f"mem_rule_{len(self.memories) + 1:02d}_{datetime.now().strftime('%H%M%S')}"
        item = MemoryItem(
            id=item_id,
            error_category=error_category,
            trigger_pattern=trigger_pattern,
            generalized_rule=generalized_rule,
            target_tables=target_tables or [],
            confidence_score=initial_confidence
        )
        self.memories[item.id] = item
        self.save()
        return item

    def retrieve_relevant_memories(
        self,
        query: str,
        active_tables: Optional[List[str]] = None,
        top_k: int = 3,
        min_confidence: Optional[float] = None
    ) -> List[MemoryItem]:
        """
        Retrieves top relevant generalized repair memories based on semantic keywords,
        target tables, and current confidence score above the threshold.
        """
        threshold = min_confidence if min_confidence is not None else self.pruning_threshold
        query_words = set(re.findall(r"\w+", query.lower()))
        active_tables_set = set(active_tables or [])

        scored_items = []
        for mem in self.memories.values():
            if mem.confidence_score < threshold:
                continue

            # Calculate relevance score: keyword overlap + table overlap + confidence weighting
            trigger_words = set(re.findall(r"\w+", mem.trigger_pattern.lower()))
            rule_words = set(re.findall(r"\w+", mem.generalized_rule.lower()))
            
            overlap_count = len(query_words.intersection(trigger_words)) * 2 + len(query_words.intersection(rule_words))
            
            table_overlap = len(active_tables_set.intersection(set(mem.target_tables))) if active_tables_set else 0
            
            relevance = (overlap_count * 1.5 + table_overlap * 2.0) * mem.confidence_score
            
            if overlap_count > 0 or table_overlap > 0:
                scored_items.append((relevance, mem))

        # Sort descending by relevance
        scored_items.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored_items[:top_k]]

    def record_feedback(self, memory_id: str, success: bool):
        """Updates confidence of a memory item based on query execution success or failure."""
        if memory_id in self.memories:
            self.memories[memory_id].record_usage(success)
            self.save()

    def apply_temporal_decay(self, decay_multiplier: float = 1.0) -> List[str]:
        """
        Decays all memory items. Returns list of pruned memory IDs whose confidence
        fell below the threshold.
        """
        pruned_ids = []
        for mem_id, mem in list(self.memories.items()):
            new_conf = mem.apply_decay(mem.decay_rate * decay_multiplier)
            if new_conf < self.pruning_threshold:
                pruned_ids.append(mem_id)
                del self.memories[mem_id]
        self.save()
        return pruned_ids

    def prune_stale_memories(self) -> List[str]:
        """Removes memories with confidence score below pruning threshold."""
        pruned = [m_id for m_id, m in self.memories.items() if m.confidence_score < self.pruning_threshold]
        for m_id in pruned:
            del self.memories[m_id]
        if pruned:
            self.save()
        return pruned

    def save(self):
        """Persists memory governance state."""
        try:
            data = {k: v.model_dump() for k, v in self.memories.items()}
            with open(self.persistence_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[AEMG Memory] Error saving memory store: {e}")

    def load(self):
        """Loads persisted memory governance state."""
        if os.path.exists(self.persistence_path):
            try:
                with open(self.persistence_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.memories = {k: MemoryItem(**v) for k, v in data.items()}
            except Exception as e:
                print(f"[AEMG Memory] Error loading memory store: {e}")
                self.memories = {}

    def get_statistics(self) -> Dict[str, Any]:
        """Returns health and governance metrics for the dashboard."""
        if not self.memories:
            return {"total_count": 0, "avg_confidence": 0.0, "category_counts": {}}
        
        avg_conf = sum(m.confidence_score for m in self.memories.values()) / len(self.memories)
        category_counts = {}
        for m in self.memories.values():
            category_counts[m.error_category] = category_counts.get(m.error_category, 0) + 1

        return {
            "total_count": len(self.memories),
            "avg_confidence": round(avg_conf, 3),
            "category_counts": category_counts,
            "pruning_threshold": self.pruning_threshold
        }
