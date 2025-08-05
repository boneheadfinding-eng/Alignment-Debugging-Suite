"""
Main experiment runner for the AI Alignment Debugging Suite.
"""

import os
import sys
import yaml
import asyncio
import argparse
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.evaluation import EvaluationPipeline
from src.utils import setup_logger
from src.visualization import HeatmapGenerator, BehaviorTracer


logger = setup_logger(__name__)


def main():
    """Main entry point for running experiments."""
    parser = argparse.ArgumentParser(
        description="Run AI Alignment Debugging experiments"
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='results',
        help='Directory for output files'
    )
    
    parser.add_argument(
        '--visualize',
        action='store_true',
        help='Generate visualizations after experiment'
    )
    
    parser.add_argument(
        '--mock',
        action='store_true',
        help='Use mock API client for testing'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Override with command line arguments
    if args.mock:
        config['model']['provider'] = 'mock'
    
    if args.output_dir:
        config.setdefault('output', {})['directory'] = args.output_dir
    
    # Create output directory
    output_dir = Path(config.get('output', {}).get('directory', 'results'))
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize pipeline
    logger.info("Initializing evaluation pipeline...")
    pipeline = EvaluationPipeline(str(config_path))
    
    # Run experiment
    logger.info("Starting experiment...")
    start_time = datetime.now()
    
    try:
        # Run async pipeline
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(pipeline.run_pipeline())
        
        logger.info(f"Experiment completed successfully in {datetime.now() - start_time}")
        logger.info(f"Total scenarios tested: {result.scenarios_tested}")
        logger.info(f"Total prompts evaluated: {result.total_prompts}")
        logger.info(f"Overall pass rate: {result.summary_metrics.get('overall_pass_rate', 0):.2%}")
        
        # Generate visualizations if requested
        if args.visualize:
            logger.info("Generating visualizations...")
            
            # Create visualization directory
            viz_dir = output_dir / 'visualizations'
            viz_dir.mkdir(exist_ok=True)
            
            # Generate heatmaps
            heatmap_gen = HeatmapGenerator()
            heatmap_gen.add_results(result.results)
            heatmap_gen.generate_summary_report(str(viz_dir))
            
            # Generate behavior traces
            tracer = BehaviorTracer()
            for i, res in enumerate(result.results[:10]):  # First 10 results
                if 'evaluation' in res:
                    trace_id = tracer.trace_evaluation(
                        res.get('prompt', ''),
                        res.get('response', ''),
                        res['evaluation']
                    )
                    
                    if i < 3:  # Visualize first 3 traces
                        tracer.visualize_trace(
                            trace_id,
                            str(viz_dir / f'trace_{i+1}.png')
                        )
            
            logger.info(f"Visualizations saved to {viz_dir}")
        
        # Print summary
        print("\n" + "="*50)
        print("EXPERIMENT SUMMARY")
        print("="*50)
        print(f"Timestamp: {result.timestamp}")
        print(f"Scenarios tested: {result.scenarios_tested}")
        print(f"Total prompts: {result.total_prompts}")
        print(f"Failures: {len(result.failures)}")
        print("\nKey Metrics:")
        for metric, value in sorted(result.summary_metrics.items()):
            if isinstance(value, float):
                print(f"  {metric}: {value:.3f}")
            else:
                print(f"  {metric}: {value}")
        
        if result.failures:
            print(f"\nFirst 5 failures:")
            for i, failure in enumerate(result.failures[:5]):
                print(f"\n{i+1}. {failure.get('scenario', 'Unknown scenario')}")
                print(f"   Prompt: {failure.get('prompt', 'N/A')[:100]}...")
        
    except Exception as e:
        logger.error(f"Experiment failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()