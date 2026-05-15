# File: core/analysis/advanced_scoring.py
"""
Advanced scoring algorithms using 50+ protocol dataset.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import statistics
from scipy import stats
import json

# Placeholder imports - these will need to be created
# from core.data.protocol_database import protocol_db, ProtocolMetadata
# from core.data.protocol_resolver import protocol_resolver

class ScoreComponent(str, Enum):
    """Components of the advanced scoring system."""
    DEVELOPER_ACTIVITY = "developer_activity"
    CODE_QUALITY = "code_quality"
    ONCHAIN_LIQUIDITY = "onchain_liquidity"
    FINANCIAL_HEALTH = "financial_health"
    REGULATORY_EXPOSURE = "regulatory_exposure"
    TOKENOMICS = "tokenomics"
    MARKET_SENTIMENT = "market_sentiment"
    ECOSYSTEM_INTEGRATION = "ecosystem_integration"
    SECURITY_POSTURE = "security_posture"
    TEAM_BACKGROUND = "team_background"

@dataclass
class ScoringWeights:
    """Dynamic weights for scoring components."""
    base_weights: Dict[ScoreComponent, float]
    market_conditions: Dict[str, float]
    regulatory_environment: Dict[str, float]
    protocol_age_factor: float

    @classmethod
    def default(cls):
        """Default weights optimized for regulatory arbitrage."""
        return cls(
            base_weights={
                ScoreComponent.DEVELOPER_ACTIVITY: 0.15,
                ScoreComponent.CODE_QUALITY: 0.12,
                ScoreComponent.ONCHAIN_LIQUIDITY: 0.18,
                ScoreComponent.FINANCIAL_HEALTH: 0.16,
                ScoreComponent.REGULATORY_EXPOSURE: 0.20,
                ScoreComponent.TOKENOMICS: 0.08,
                ScoreComponent.MARKET_SENTIMENT: 0.05,
                ScoreComponent.ECOSYSTEM_INTEGRATION: 0.04,
                ScoreComponent.SECURITY_POSTURE: 0.10,
                ScoreComponent.TEAM_BACKGROUND: 0.02,
            },
            market_conditions={
                "bull": 1.1,
                "bear": 0.9,
                "neutral": 1.0
            },
            regulatory_environment={
                "usa": 1.2,
                "eu": 1.1,
                "asia": 0.9,
                "global": 1.0
            },
            protocol_age_factor=0.3
        )

class AdvancedScoringEngine:
    """Calculates a multi-dimensional risk score for a protocol."""

    def __init__(self, weights: Optional[ScoringWeights] = None):
        self.weights = weights or ScoringWeights.default()
        # In a real app, you'd load the full dataset into memory or have a DB connection
        # self.full_dataset = self._load_comparative_dataset()

    def _load_comparative_dataset(self):
        # Placeholder: This would load data for all 50+ protocols to enable percentile ranks
        # For now, we'll use static values.
        return {"avg_commit_rate": 15, "avg_tvl": 500_000_000}

    def _calculate_developer_activity(self, protocol_data: Any, full_dataset: Dict) -> float:
        """Scores developer activity based on commit rate and contributor count."""
        
        # In a real implementation, we'd fetch live data. Here we use dummy data.
        # recent_commits = get_github_activity(protocol_data.github_url).get('recent_commit_count')
        recent_commits = 20 # Dummy data
        
        # Score based on percentile rank against the dataset average
        avg_commits = full_dataset.get("avg_commit_rate", 15)
        
        # Simple linear scoring: 100 if at or above average, scaled down if below.
        score = min(100.0, (recent_commits / avg_commits) * 100) if avg_commits > 0 else 0.0
        
        return score

    def _calculate_onchain_liquidity(self, protocol_data: Any, full_dataset: Dict) -> float:
        """Scores on-chain liquidity based on TVL."""
        
        # In a real implementation, we'd fetch live data. Here we use dummy data.
        # tvl = get_onchain_data(protocol_data.protocol_id).get('tvl_usd')
        tvl = 750_000_000 # Dummy data
        
        avg_tvl = full_dataset.get("avg_tvl", 500_000_000)
        
        # Use a logarithmic scale to avoid extreme scores from top protocols
        # A score of 100 means TVL is 10x the average or more.
        if not tvl or not avg_tvl:
            return 0.0
            
        score = (np.log10(tvl) / np.log10(avg_tvl * 10)) * 100
        
        return min(100.0, score)

    def _calculate_regulatory_exposure(self, protocol_data: Any, full_dataset: Dict) -> float:
        """Scores regulatory exposure based on known classifications and jurisdictions."""
        
        # In a real implementation, this would involve complex logic based on token classification,
        # team jurisdiction, and specific features (e.g., privacy).
        # For the placeholder, we'll use a dummy score.
        # clarity_score = protocol_data.regulatory_clarity_score # e.g., 0-100
        clarity_score = 30 # Dummy data: low clarity = high risk
        
        # Invert the score: high clarity = low risk (high score), low clarity = high risk (low score)
        risk_score = 100.0 - clarity_score
        return risk_score

    def _calculate_component_score(self, component: ScoreComponent, protocol_data: Any, full_dataset: Dict) -> float:
        """Dispatcher to calculate score for a specific component."""
        if component == ScoreComponent.DEVELOPER_ACTIVITY:
            return self._calculate_developer_activity(protocol_data, full_dataset)
        if component == ScoreComponent.ONCHAIN_LIQUIDITY:
            return self._calculate_onchain_liquidity(protocol_data, full_dataset)
        if component == ScoreComponent.REGULATORY_EXPOSURE:
            return self._calculate_regulatory_exposure(protocol_data, full_dataset)
        
        # Placeholder for other components
        return 50.0

    def calculate_final_score(
        self,
        protocol_id: str,
        market_condition: str = "neutral",
        regulatory_jurisdiction: str = "global"
    ) -> Dict[str, Any]:
        """
        Calculates the final, weighted risk score for a protocol.
        """
        # In a real implementation:
        # protocol_data = protocol_db.get_protocol(protocol_id)
        # if not protocol_data:
        #     raise ValueError(f"Protocol with ID '{protocol_id}' not found.")
        protocol_data = {"github_url": "dummy"} # Dummy data for now

        full_dataset = self._load_comparative_dataset()

        component_scores: Dict[ScoreComponent, float] = {}
        for component in ScoreComponent:
            component_scores[component] = self._calculate_component_score(component, protocol_data, full_dataset)

        # Apply dynamic weighting (simplified example)
        final_score = 0.0
        applied_weights = {}
        for component, score in component_scores.items():
            base_weight = self.weights.base_weights[component]
            market_adj = self.weights.market_conditions.get(market_condition, 1.0)
            reg_adj = self.weights.regulatory_environment.get(regulatory_jurisdiction, 1.0)
            
            final_weight = base_weight # Start with base
            if component == ScoreComponent.REGULATORY_EXPOSURE:
                final_weight *= reg_adj
            elif component in [ScoreComponent.ONCHAIN_LIQUIDITY, ScoreComponent.FINANCIAL_HEALTH]:
                 final_weight *= market_adj
            
            applied_weights[component.value] = round(final_weight, 3)
            final_score += score * final_weight
        
        # Normalize score
        total_weight_applied = sum(applied_weights.values())
        normalized_score = (final_score / total_weight_applied) if total_weight_applied > 0 else 0.0
        
        return {
            "protocol_id": protocol_id,
            "final_score": round(normalized_score, 2),
            "component_scores": {k.value: round(v, 2) for k, v in component_scores.items()},
            "applied_weights": applied_weights
        }

engine = AdvancedScoringEngine()
