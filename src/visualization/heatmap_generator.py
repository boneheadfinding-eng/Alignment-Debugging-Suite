"""
Heatmap generator for visualizing alignment patterns.
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from datetime import datetime
import json


class HeatmapGenerator:
    """Generates heatmaps for visualizing alignment patterns and errors."""
    
    def __init__(self):
        self.data = []
        self.categories = set()
        self.metrics = set()
        
    def add_result(self, result: Dict[str, Any]):
        """Add a single evaluation result."""
        self.data.append(result)
        if 'category' in result:
            self.categories.add(result['category'])
        if 'evaluation' in result and 'scores' in result['evaluation']:
            self.metrics.update(result['evaluation']['scores'].keys())
    
    def add_results(self, results: List[Dict[str, Any]]):
        """Add multiple evaluation results."""
        for result in results:
            self.add_result(result)
    
    def generate_alignment_heatmap(
        self, 
        output_file: Optional[str] = None,
        figsize: Tuple[int, int] = (12, 8)
    ):
        """
        Generate a heatmap showing alignment scores across categories and metrics.
        
        Args:
            output_file: Save to file if provided
            figsize: Figure size
        """
        if not self.data:
            raise ValueError("No data available for heatmap generation")
        
        # Prepare data matrix
        categories = sorted(list(self.categories))
        metrics = sorted(list(self.metrics))
        
        # Initialize matrix
        matrix = np.zeros((len(categories), len(metrics)))
        counts = np.zeros((len(categories), len(metrics)))
        
        # Fill matrix with average scores
        for result in self.data:
            if 'category' not in result or 'evaluation' not in result:
                continue
                
            cat_idx = categories.index(result['category'])
            scores = result['evaluation'].get('scores', {})
            
            for metric, score in scores.items():
                if metric in metrics:
                    metric_idx = metrics.index(metric)
                    matrix[cat_idx, metric_idx] += score
                    counts[cat_idx, metric_idx] += 1
        
        # Calculate averages
        with np.errstate(divide='ignore', invalid='ignore'):
            matrix = np.divide(matrix, counts)
            matrix = np.nan_to_num(matrix, nan=0.0)
        
        # Create heatmap
        fig, ax = plt.subplots(figsize=figsize)
        
        # Create custom colormap (red to yellow to green)
        cmap = sns.diverging_palette(10, 130, as_cmap=True)
        
        # Plot heatmap
        sns.heatmap(
            matrix,
            annot=True,
            fmt='.2f',
            cmap=cmap,
            center=0.7,
            vmin=0,
            vmax=1,
            xticklabels=metrics,
            yticklabels=categories,
            cbar_kws={'label': 'Score'},
            linewidths=0.5,
            linecolor='gray'
        )
        
        # Customize
        plt.title('Alignment Scores Heatmap', fontsize=16, weight='bold', pad=20)
        plt.xlabel('Metrics', fontsize=12, weight='bold')
        plt.ylabel('Categories', fontsize=12, weight='bold')
        
        # Rotate x labels for better readability
        plt.xticks(rotation=45, ha='right')
        
        # Add grid
        ax.set_facecolor('#f0f0f0')
        
        # Tight layout
        plt.tight_layout()
        
        # Save or show
        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
        else:
            plt.show()
            
        plt.close()
    
    def generate_error_heatmap(
        self,
        output_file: Optional[str] = None,
        figsize: Tuple[int, int] = (10, 8)
    ):
        """
        Generate a heatmap showing error patterns.
        
        Args:
            output_file: Save to file if provided
            figsize: Figure size
        """
        # Extract error data
        error_matrix = {}
        
        for result in self.data:
            if not result.get('passed_safety_check', True):
                category = result.get('category', 'unknown')
                
                if category not in error_matrix:
                    error_matrix[category] = {
                        'total': 0,
                        'by_severity': {},
                        'by_type': {}
                    }
                
                error_matrix[category]['total'] += 1
                
                # Track severity if adversarial
                if result.get('is_adversarial', False):
                    severity = result.get('severity', 'unknown')
                    error_matrix[category]['by_severity'][severity] = \
                        error_matrix[category]['by_severity'].get(severity, 0) + 1
                
                # Track injection type
                if 'injection_type' in result:
                    inj_type = result['injection_type']
                    error_matrix[category]['by_type'][inj_type] = \
                        error_matrix[category]['by_type'].get(inj_type, 0) + 1
        
        if not error_matrix:
            print("No errors found in data")
            return
        
        # Create severity heatmap
        categories = sorted(error_matrix.keys())
        severities = sorted(set(s for cat_data in error_matrix.values() 
                              for s in cat_data['by_severity'].keys()))
        
        if severities:
            severity_matrix = np.zeros((len(categories), len(severities)))
            
            for i, cat in enumerate(categories):
                for j, sev in enumerate(severities):
                    severity_matrix[i, j] = error_matrix[cat]['by_severity'].get(sev, 0)
            
            # Plot
            fig, ax = plt.subplots(figsize=figsize)
            
            sns.heatmap(
                severity_matrix,
                annot=True,
                fmt='d',
                cmap='Reds',
                xticklabels=severities,
                yticklabels=categories,
                cbar_kws={'label': 'Error Count'}
            )
            
            plt.title('Error Distribution by Category and Severity', 
                     fontsize=14, weight='bold')
            plt.xlabel('Severity Level', fontsize=12)
            plt.ylabel('Category', fontsize=12)
            
            plt.tight_layout()
            
            if output_file:
                base_name = output_file.rsplit('.', 1)[0]
                plt.savefig(f"{base_name}_severity.png", dpi=300, bbox_inches='tight')
            else:
                plt.show()
                
            plt.close()
    
    def generate_temporal_heatmap(
        self,
        output_file: Optional[str] = None,
        time_bins: int = 10,
        figsize: Tuple[int, int] = (12, 6)
    ):
        """
        Generate a heatmap showing performance over time.
        
        Args:
            output_file: Save to file if provided
            time_bins: Number of time bins
            figsize: Figure size
        """
        if not self.data:
            return
        
        # Extract timestamps and scores
        temporal_data = []
        
        for result in self.data:
            if 'timestamp' in result and 'evaluation' in result:
                timestamp = datetime.fromisoformat(result['timestamp'])
                scores = result['evaluation'].get('scores', {})
                
                temporal_data.append({
                    'timestamp': timestamp,
                    'overall_score': np.mean(list(scores.values())) if scores else 0,
                    **scores
                })
        
        if not temporal_data:
            print("No temporal data available")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(temporal_data)
        df = df.sort_values('timestamp')
        
        # Create time bins
        df['time_bin'] = pd.cut(df.index, bins=time_bins, labels=False)
        
        # Aggregate by time bin
        metrics = [col for col in df.columns 
                  if col not in ['timestamp', 'time_bin']]
        
        aggregated = df.groupby('time_bin')[metrics].mean()
        
        # Create heatmap
        fig, ax = plt.subplots(figsize=figsize)
        
        sns.heatmap(
            aggregated.T,
            annot=True,
            fmt='.2f',
            cmap='RdYlGn',
            center=0.7,
            vmin=0,
            vmax=1,
            xticklabels=[f"T{i}" for i in range(len(aggregated))],
            cbar_kws={'label': 'Score'}
        )
        
        plt.title('Performance Over Time', fontsize=14, weight='bold')
        plt.xlabel('Time Period', fontsize=12)
        plt.ylabel('Metrics', fontsize=12)
        
        plt.tight_layout()
        
        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
        else:
            plt.show()
            
        plt.close()
    
    def generate_correlation_heatmap(
        self,
        output_file: Optional[str] = None,
        figsize: Tuple[int, int] = (10, 8)
    ):
        """
        Generate a correlation heatmap between different metrics.
        
        Args:
            output_file: Save to file if provided
            figsize: Figure size
        """
        # Extract scores into DataFrame
        scores_data = []
        
        for result in self.data:
            if 'evaluation' in result and 'scores' in result['evaluation']:
                scores = result['evaluation']['scores']
                scores_data.append(scores)
        
        if not scores_data:
            print("No score data available")
            return
        
        df = pd.DataFrame(scores_data)
        
        # Calculate correlation matrix
        corr_matrix = df.corr()
        
        # Create heatmap
        fig, ax = plt.subplots(figsize=figsize)
        
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
        
        sns.heatmap(
            corr_matrix,
            mask=mask,
            annot=True,
            fmt='.2f',
            cmap='coolwarm',
            center=0,
            vmin=-1,
            vmax=1,
            square=True,
            linewidths=0.5,
            cbar_kws={'label': 'Correlation'}
        )
        
        plt.title('Metric Correlation Heatmap', fontsize=14, weight='bold')
        
        plt.tight_layout()
        
        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
        else:
            plt.show()
            
        plt.close()
    
    def generate_summary_report(self, output_dir: str):
        """Generate a comprehensive visual report."""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate all heatmaps
        self.generate_alignment_heatmap(
            os.path.join(output_dir, 'alignment_heatmap.png')
        )
        
        self.generate_error_heatmap(
            os.path.join(output_dir, 'error_heatmap.png')
        )
        
        self.generate_temporal_heatmap(
            os.path.join(output_dir, 'temporal_heatmap.png')
        )
        
        self.generate_correlation_heatmap(
            os.path.join(output_dir, 'correlation_heatmap.png')
        )
        
        # Generate summary statistics
        summary = {
            'total_evaluations': len(self.data),
            'categories': list(self.categories),
            'metrics': list(self.metrics),
            'failure_rate': sum(1 for r in self.data 
                              if not r.get('passed_safety_check', True)) / len(self.data)
        }
        
        with open(os.path.join(output_dir, 'summary.json'), 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"Summary report generated in {output_dir}")