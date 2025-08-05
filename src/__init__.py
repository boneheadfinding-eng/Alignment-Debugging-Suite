"""AI Alignment Debugging Suite - Main Package"""

from .adversarial import PromptInjector, ScenarioGenerator
from .evaluation import EvaluationPipeline, SafetyEvaluator
from .visualization import BehaviorTracer, HeatmapGenerator
from .utils import APIClient, setup_logger

__version__ = "1.0.0"

__all__ = [
    'PromptInjector',
    'ScenarioGenerator',
    'EvaluationPipeline',
    'SafetyEvaluator',
    'BehaviorTracer',
    'HeatmapGenerator',
    'APIClient',
    'setup_logger'
]