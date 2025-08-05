"""
Behavior tracer for visualizing model reasoning chains.
"""

import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import networkx as nx


@dataclass
class ReasoningNode:
    """Represents a node in the reasoning chain."""
    id: str
    content: str
    node_type: str  # prompt, response, evaluation, decision
    timestamp: datetime
    metadata: Dict[str, Any]
    safety_score: Optional[float] = None


@dataclass 
class ReasoningEdge:
    """Represents an edge in the reasoning chain."""
    source: str
    target: str
    edge_type: str  # leads_to, evaluates, triggers
    weight: float = 1.0


class BehaviorTracer:
    """Traces and visualizes model behavior and reasoning chains."""
    
    def __init__(self):
        self.nodes: List[ReasoningNode] = []
        self.edges: List[ReasoningEdge] = []
        self.graph = nx.DiGraph()
        
    def add_node(self, node: ReasoningNode):
        """Add a node to the reasoning chain."""
        self.nodes.append(node)
        
        # Add to graph with attributes
        self.graph.add_node(
            node.id,
            content=node.content[:50] + "..." if len(node.content) > 50 else node.content,
            node_type=node.node_type,
            safety_score=node.safety_score,
            full_content=node.content
        )
        
    def add_edge(self, edge: ReasoningEdge):
        """Add an edge to the reasoning chain."""
        self.edges.append(edge)
        self.graph.add_edge(edge.source, edge.target, 
                          edge_type=edge.edge_type, 
                          weight=edge.weight)
        
    def trace_evaluation(self, prompt: str, response: str, 
                        evaluation_result: Dict[str, Any]) -> str:
        """
        Trace a complete evaluation cycle.
        
        Args:
            prompt: Input prompt
            response: Model response  
            evaluation_result: Evaluation results
            
        Returns:
            Trace ID for this evaluation
        """
        timestamp = datetime.now()
        trace_id = f"trace_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        # Add prompt node
        prompt_node = ReasoningNode(
            id=f"{trace_id}_prompt",
            content=prompt,
            node_type="prompt",
            timestamp=timestamp,
            metadata={"trace_id": trace_id}
        )
        self.add_node(prompt_node)
        
        # Add response node
        response_node = ReasoningNode(
            id=f"{trace_id}_response",
            content=response,
            node_type="response",
            timestamp=timestamp,
            metadata={"trace_id": trace_id},
            safety_score=evaluation_result.get('scores', {}).get('safety_score')
        )
        self.add_node(response_node)
        
        # Add edge from prompt to response
        self.add_edge(ReasoningEdge(
            source=prompt_node.id,
            target=response_node.id,
            edge_type="leads_to"
        ))
        
        # Add evaluation nodes
        for metric, score in evaluation_result.get('scores', {}).items():
            eval_node = ReasoningNode(
                id=f"{trace_id}_eval_{metric}",
                content=f"{metric}: {score:.2f}",
                node_type="evaluation",
                timestamp=timestamp,
                metadata={"metric": metric, "score": score},
                safety_score=score
            )
            self.add_node(eval_node)
            
            # Add edge from response to evaluation
            self.add_edge(ReasoningEdge(
                source=response_node.id,
                target=eval_node.id,
                edge_type="evaluates"
            ))
        
        # Add decision node
        decision = "SAFE" if evaluation_result.get('overall_safe', False) else "UNSAFE"
        decision_node = ReasoningNode(
            id=f"{trace_id}_decision",
            content=f"Decision: {decision}",
            node_type="decision",
            timestamp=timestamp,
            metadata={"decision": decision}
        )
        self.add_node(decision_node)
        
        # Add edges from evaluations to decision
        for metric in evaluation_result.get('scores', {}).keys():
            self.add_edge(ReasoningEdge(
                source=f"{trace_id}_eval_{metric}",
                target=decision_node.id,
                edge_type="triggers"
            ))
        
        return trace_id
    
    def visualize_trace(self, trace_id: Optional[str] = None, 
                       output_file: Optional[str] = None,
                       show_full_content: bool = False):
        """
        Visualize a reasoning trace.
        
        Args:
            trace_id: Specific trace to visualize (all if None)
            output_file: Save to file if provided
            show_full_content: Show full content in nodes
        """
        # Filter nodes if trace_id provided
        if trace_id:
            nodes_to_show = [n for n in self.graph.nodes() 
                           if trace_id in n]
            subgraph = self.graph.subgraph(nodes_to_show)
        else:
            subgraph = self.graph
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Layout
        pos = nx.spring_layout(subgraph, k=2, iterations=50)
        
        # Color mapping for node types
        color_map = {
            'prompt': '#FFE5B4',      # Peach
            'response': '#B4D4FF',    # Light blue
            'evaluation': '#FFB4B4',  # Light red
            'decision': '#B4FFB4'     # Light green
        }
        
        # Draw nodes
        for node_id in subgraph.nodes():
            node_data = subgraph.nodes[node_id]
            node_type = node_data['node_type']
            
            # Get position
            x, y = pos[node_id]
            
            # Determine node color based on safety score
            if node_data.get('safety_score') is not None:
                score = node_data['safety_score']
                if score < 0.5:
                    face_color = '#FF6B6B'  # Red
                elif score < 0.8:
                    face_color = '#FFD93D'  # Yellow
                else:
                    face_color = '#6BCF7F'  # Green
            else:
                face_color = color_map.get(node_type, '#CCCCCC')
            
            # Create fancy box
            content = node_data['full_content'] if show_full_content else node_data['content']
            
            # Wrap long content
            if len(content) > 30 and not show_full_content:
                content = '\n'.join([content[i:i+30] 
                                   for i in range(0, len(content), 30)])
            
            box = FancyBboxPatch(
                (x - 0.15, y - 0.05),
                0.3, 0.1,
                boxstyle="round,pad=0.02",
                facecolor=face_color,
                edgecolor='black',
                linewidth=1.5
            )
            ax.add_patch(box)
            
            # Add text
            ax.text(x, y, content, ha='center', va='center', 
                   fontsize=8, weight='bold')
        
        # Draw edges
        for edge in subgraph.edges():
            source_pos = pos[edge[0]]
            target_pos = pos[edge[1]]
            edge_data = subgraph.edges[edge]
            
            # Arrow style based on edge type
            arrow_styles = {
                'leads_to': dict(arrowstyle='->', lw=2, color='blue'),
                'evaluates': dict(arrowstyle='->', lw=1.5, color='orange'),
                'triggers': dict(arrowstyle='->', lw=1, color='green', linestyle='dashed')
            }
            
            style = arrow_styles.get(edge_data['edge_type'], 
                                    dict(arrowstyle='->', lw=1, color='gray'))
            
            ax.annotate('', xy=target_pos, xytext=source_pos,
                       arrowprops=style)
        
        # Add legend
        legend_elements = [
            mpatches.Patch(color='#FFE5B4', label='Prompt'),
            mpatches.Patch(color='#B4D4FF', label='Response'),
            mpatches.Patch(color='#FFB4B4', label='Evaluation'),
            mpatches.Patch(color='#B4FFB4', label='Decision'),
            mpatches.Patch(color='#6BCF7F', label='Safe (>0.8)'),
            mpatches.Patch(color='#FFD93D', label='Warning (0.5-0.8)'),
            mpatches.Patch(color='#FF6B6B', label='Unsafe (<0.5)')
        ]
        ax.legend(handles=legend_elements, loc='upper right')
        
        # Set title and clean up
        ax.set_title('Model Behavior Trace', fontsize=16, weight='bold')
        ax.axis('off')
        
        # Save or show
        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
        else:
            plt.show()
            
        plt.close()
    
    def get_trace_summary(self, trace_id: str) -> Dict[str, Any]:
        """Get summary statistics for a trace."""
        trace_nodes = [n for n in self.nodes 
                      if n.metadata.get('trace_id') == trace_id]
        
        if not trace_nodes:
            return {}
        
        # Extract metrics
        eval_nodes = [n for n in trace_nodes if n.node_type == 'evaluation']
        scores = {n.metadata['metric']: n.metadata['score'] 
                 for n in eval_nodes if 'metric' in n.metadata}
        
        # Get decision
        decision_nodes = [n for n in trace_nodes if n.node_type == 'decision']
        decision = decision_nodes[0].metadata['decision'] if decision_nodes else 'UNKNOWN'
        
        return {
            'trace_id': trace_id,
            'timestamp': trace_nodes[0].timestamp.isoformat(),
            'num_nodes': len(trace_nodes),
            'scores': scores,
            'decision': decision,
            'avg_score': sum(scores.values()) / len(scores) if scores else 0
        }
    
    def export_traces(self, output_file: str):
        """Export all traces to JSON file."""
        traces = []
        
        # Group nodes by trace
        trace_ids = set(n.metadata.get('trace_id') 
                       for n in self.nodes 
                       if 'trace_id' in n.metadata)
        
        for trace_id in trace_ids:
            if trace_id:
                summary = self.get_trace_summary(trace_id)
                traces.append(summary)
        
        with open(output_file, 'w') as f:
            json.dump(traces, f, indent=2, default=str)
    
    def analyze_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in traced behaviors."""
        if not self.nodes:
            return {}
        
        # Collect all evaluation scores
        all_scores = {}
        for node in self.nodes:
            if node.node_type == 'evaluation' and 'metric' in node.metadata:
                metric = node.metadata['metric']
                score = node.metadata['score']
                if metric not in all_scores:
                    all_scores[metric] = []
                all_scores[metric].append(score)
        
        # Calculate statistics
        patterns = {
            'total_traces': len(set(n.metadata.get('trace_id') 
                                  for n in self.nodes 
                                  if 'trace_id' in n.metadata)),
            'metrics': {}
        }
        
        for metric, scores in all_scores.items():
            patterns['metrics'][metric] = {
                'mean': sum(scores) / len(scores),
                'min': min(scores),
                'max': max(scores),
                'count': len(scores)
            }
        
        # Decision distribution
        decisions = [n.metadata['decision'] 
                    for n in self.nodes 
                    if n.node_type == 'decision']
        
        patterns['decision_distribution'] = {
            'SAFE': decisions.count('SAFE'),
            'UNSAFE': decisions.count('UNSAFE')
        }
        
        return patterns