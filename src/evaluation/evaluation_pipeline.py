"""
Main evaluation pipeline for running alignment tests.
"""

import os
import json
import yaml
import asyncio
import random
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import logging
from dataclasses import dataclass, asdict

from ..adversarial.prompt_injector import PromptInjector, AdversarialPrompt
from ..adversarial.scenario_generator import ScenarioGenerator, TestScenario
from .safety_metrics import SafetyEvaluator, EvaluationResult
from ..utils.api_client import APIClient
from ..utils.logger import setup_logger


logger = setup_logger(__name__)


@dataclass
class PipelineResult:
    """Results from a complete pipeline run."""
    timestamp: str
    config: Dict[str, Any]
    scenarios_tested: int
    total_prompts: int
    results: List[Dict[str, Any]]
    summary_metrics: Dict[str, float]
    failures: List[Dict[str, Any]]


class EvaluationPipeline:
    """Main pipeline for running alignment evaluation experiments."""
    
    def __init__(self, config_path: str):
        """
        Initialize the evaluation pipeline.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.api_client = APIClient(self.config['model'])
        self.safety_evaluator = SafetyEvaluator()
        self.prompt_injector = PromptInjector()
        self.scenario_generator = ScenarioGenerator()
        
        # Setup output directory
        self.output_dir = Path(self.config.get('output', {}).get('directory', 'results'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    
    async def run_pipeline(self) -> PipelineResult:
        """
        Run the complete evaluation pipeline.
        
        Returns:
            PipelineResult with all test outcomes
        """
        logger.info("Starting evaluation pipeline")
        start_time = datetime.now()
        
        # Generate or load test scenarios
        scenarios = self._prepare_scenarios()
        
        # Run evaluations
        all_results = []
        failures = []
        
        for scenario in scenarios:
            logger.info(f"Testing scenario: {scenario.name}")
            
            # Apply adversarial injections if enabled
            prompts = self._prepare_prompts(scenario)
            
            # Test each prompt
            for prompt in prompts:
                try:
                    result = await self._evaluate_prompt(prompt, scenario)
                    all_results.append(result)
                    
                    # Track failures
                    if not result['passed_safety_check']:
                        failures.append(result)
                        
                except Exception as e:
                    logger.error(f"Error evaluating prompt: {e}")
                    failures.append({
                        'prompt': str(prompt),
                        'error': str(e),
                        'scenario': scenario.name
                    })
        
        # Calculate summary metrics
        summary_metrics = self._calculate_summary_metrics(all_results)
        
        # Create pipeline result
        pipeline_result = PipelineResult(
            timestamp=start_time.isoformat(),
            config=self.config,
            scenarios_tested=len(scenarios),
            total_prompts=len(all_results),
            results=all_results,
            summary_metrics=summary_metrics,
            failures=failures
        )
        
        # Save results
        self._save_results(pipeline_result)
        
        # Generate visualizations if enabled
        if self.config.get('output', {}).get('visualization', {}).get('enabled', True):
            self._generate_visualizations(pipeline_result)
        
        logger.info(f"Pipeline completed. Total time: {datetime.now() - start_time}")
        return pipeline_result
    
    def _prepare_scenarios(self) -> List[TestScenario]:
        """Prepare test scenarios based on configuration."""
        scenarios = []
        
        # Load predefined scenarios
        for scenario_config in self.config.get('scenarios', []):
            if 'prompts_file' in scenario_config:
                scenario = self.scenario_generator.load_scenarios(
                    scenario_config['prompts_file']
                )[0]  # Assuming one scenario per file
                scenarios.append(scenario)
            else:
                # Generate scenarios dynamically
                category = scenario_config.get('category', 'general')
                scenario = self.scenario_generator.generate_scenario(
                    category=category,
                    num_prompts=scenario_config.get('num_prompts', 5)
                )
                scenarios.append(scenario)
        
        # Generate additional scenarios if needed
        if self.config.get('generate_scenarios', False):
            num_additional = self.config.get('num_generated_scenarios', 10)
            generated = self.scenario_generator.generate_scenario_suite(
                prompts_per_scenario=5
            )
            scenarios.extend(generated[:num_additional])
        
        return scenarios
    
    def _prepare_prompts(self, scenario: TestScenario) -> List[Any]:
        """Prepare prompts with optional adversarial injections."""
        prompts = []
        
        if self.config.get('adversarial', {}).get('enabled', False):
            # Apply adversarial injections
            injection_config = self.config['adversarial']
            
            for base_prompt in scenario.prompts:
                if injection_config.get('inject_all', False):
                    # Inject into all prompts
                    adversarial = self.prompt_injector.inject_adversarial_prompt(
                        base_prompt,
                        severity=injection_config.get('severity', 1)
                    )
                    prompts.append(adversarial)
                else:
                    # Randomly inject based on probability
                    if random.random() < injection_config.get('injection_probability', 0.5):
                        adversarial = self.prompt_injector.inject_adversarial_prompt(
                            base_prompt,
                            severity=injection_config.get('severity', 1)
                        )
                        prompts.append(adversarial)
                    else:
                        prompts.append(base_prompt)
        else:
            # Use original prompts
            prompts = scenario.prompts
        
        return prompts
    
    async def _evaluate_prompt(
        self, 
        prompt: Any, 
        scenario: TestScenario
    ) -> Dict[str, Any]:
        """Evaluate a single prompt."""
        # Get the actual prompt text
        if isinstance(prompt, AdversarialPrompt):
            prompt_text = prompt.injected_prompt
            is_adversarial = True
        else:
            prompt_text = prompt
            is_adversarial = False
        
        # Get model response
        response = await self.api_client.get_completion(prompt_text)
        
        # Evaluate safety
        evaluation = self.safety_evaluator.evaluate_response(
            prompt=prompt_text,
            response=response,
            expected_behavior=scenario.expected_behavior
        )
        
        # Compile result
        result = {
            'scenario': scenario.name,
            'category': scenario.category,
            'prompt': prompt_text,
            'is_adversarial': is_adversarial,
            'response': response,
            'evaluation': asdict(evaluation),
            'passed_safety_check': evaluation.overall_safe,
            'risk_level': scenario.risk_level,
            'timestamp': datetime.now().isoformat()
        }
        
        if is_adversarial:
            result['injection_type'] = prompt.injection_type.value
            result['severity'] = prompt.severity
        
        return result
    
    def _calculate_summary_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate summary metrics from all results."""
        if not results:
            return {}
        
        total = len(results)
        passed = sum(1 for r in results if r['passed_safety_check'])
        
        # Calculate metrics by category
        category_metrics = {}
        categories = set(r['category'] for r in results)
        
        for category in categories:
            category_results = [r for r in results if r['category'] == category]
            category_passed = sum(1 for r in category_results if r['passed_safety_check'])
            category_metrics[f'{category}_pass_rate'] = category_passed / len(category_results)
        
        # Calculate adversarial metrics
        adversarial_results = [r for r in results if r.get('is_adversarial', False)]
        if adversarial_results:
            adversarial_passed = sum(1 for r in adversarial_results if r['passed_safety_check'])
            adversarial_pass_rate = adversarial_passed / len(adversarial_results)
        else:
            adversarial_pass_rate = 1.0
        
        # Average scores
        avg_scores = {}
        score_keys = ['safety_score', 'alignment_score', 'helpfulness_score', 'truthfulness_score']
        
        for key in score_keys:
            scores = [r['evaluation']['scores'].get(key, 0) for r in results]
            avg_scores[f'avg_{key}'] = sum(scores) / len(scores) if scores else 0
        
        return {
            'overall_pass_rate': passed / total,
            'adversarial_pass_rate': adversarial_pass_rate,
            **category_metrics,
            **avg_scores,
            'total_tests': total,
            'total_passed': passed,
            'total_failed': total - passed
        }
    
    def _save_results(self, pipeline_result: PipelineResult):
        """Save results to file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save detailed results as JSON
        results_file = self.output_dir / f'results_{timestamp}.json'
        with open(results_file, 'w') as f:
            json.dump(asdict(pipeline_result), f, indent=2, default=str)
        
        # Save summary report
        report_file = self.output_dir / f'report_{timestamp}.txt'
        self._generate_report(pipeline_result, report_file)
        
        logger.info(f"Results saved to {results_file} and {report_file}")
    
    def _generate_report(self, pipeline_result: PipelineResult, output_file: Path):
        """Generate a human-readable report."""
        with open(output_file, 'w') as f:
            f.write("AI Alignment Evaluation Report\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Timestamp: {pipeline_result.timestamp}\n")
            f.write(f"Total Scenarios: {pipeline_result.scenarios_tested}\n")
            f.write(f"Total Prompts: {pipeline_result.total_prompts}\n\n")
            
            f.write("Summary Metrics:\n")
            f.write("-" * 30 + "\n")
            for metric, value in pipeline_result.summary_metrics.items():
                f.write(f"{metric}: {value:.3f}\n")
            
            f.write(f"\nFailures: {len(pipeline_result.failures)}\n")
            if pipeline_result.failures:
                f.write("\nFailure Details:\n")
                f.write("-" * 30 + "\n")
                for i, failure in enumerate(pipeline_result.failures[:10]):  # Show first 10
                    f.write(f"\n{i+1}. Scenario: {failure.get('scenario', 'Unknown')}\n")
                    f.write(f"   Prompt: {failure.get('prompt', 'N/A')[:100]}...\n")
                    if 'error' in failure:
                        f.write(f"   Error: {failure['error']}\n")
    
    def _generate_visualizations(self, pipeline_result: PipelineResult):
        """Generate visualization plots."""
        # This would integrate with the visualization module
        # Placeholder for now
        logger.info("Generating visualizations...")
        # TODO: Implement visualization generation


def run_pipeline(config: Dict[str, Any]):
    """
    Convenience function to run the pipeline.
    
    Args:
        config: Configuration dictionary or path to config file
    """
    if isinstance(config, dict):
        # Save config to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            config_path = f.name
    else:
        config_path = config
    
    pipeline = EvaluationPipeline(config_path)
    
    # Run async pipeline
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(pipeline.run_pipeline())
    
    return result