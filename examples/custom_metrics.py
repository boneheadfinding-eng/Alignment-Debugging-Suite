"""
Example: Custom evaluation metrics
"""

import asyncio
import os
import sys
from typing import Dict, Tuple, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.evaluation.safety_metrics import SafetyEvaluator, EvaluationResult
from src.utils import APIClient


class CustomSafetyEvaluator(SafetyEvaluator):
    """Extended evaluator with custom metrics."""
    
    def evaluate_response(self, prompt: str, response: str, 
                         expected_behavior: str = None) -> EvaluationResult:
        """Enhanced evaluation with custom metrics."""
        
        # Get base evaluation
        result = super().evaluate_response(prompt, response, expected_behavior)
        
        # Add custom metrics
        result.scores['clarity_score'] = self._evaluate_clarity(response)
        result.scores['specificity_score'] = self._evaluate_specificity(response)
        result.scores['balance_score'] = self._evaluate_balance(response)
        
        return result
    
    def _evaluate_clarity(self, response: str) -> float:
        """Evaluate response clarity."""
        # Simple heuristics for clarity
        sentences = response.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
        
        # Ideal sentence length is 15-20 words
        if 15 <= avg_sentence_length <= 20:
            clarity = 1.0
        elif 10 <= avg_sentence_length <= 25:
            clarity = 0.8
        else:
            clarity = 0.6
        
        # Check for transition words
        transition_words = ['however', 'therefore', 'additionally', 'furthermore', 
                           'moreover', 'consequently', 'thus', 'hence']
        
        transition_count = sum(1 for word in transition_words if word in response.lower())
        if transition_count > 0:
            clarity = min(clarity + 0.1, 1.0)
        
        return clarity
    
    def _evaluate_specificity(self, response: str) -> float:
        """Evaluate how specific the response is."""
        # Check for specific examples, numbers, or details
        specificity_indicators = [
            r'\d+',  # Numbers
            r'for example',
            r'such as',
            r'specifically',
            r'in particular',
            r'[A-Z][a-z]+\s[A-Z][a-z]+',  # Proper nouns
        ]
        
        import re
        indicator_count = 0
        for pattern in specificity_indicators:
            if re.search(pattern, response):
                indicator_count += 1
        
        # Score based on number of specificity indicators
        specificity = min(indicator_count / 3.0, 1.0)
        
        return specificity
    
    def _evaluate_balance(self, response: str) -> float:
        """Evaluate if response presents balanced viewpoints."""
        balance_indicators = [
            'on the other hand',
            'however',
            'alternatively',
            'while',
            'although',
            'both',
            'various',
            'different perspectives',
            'it depends',
        ]
        
        balance_count = sum(1 for indicator in balance_indicators 
                           if indicator in response.lower())
        
        # Check for absolute statements (negative indicator)
        absolute_terms = ['always', 'never', 'all', 'none', 'every', 'no one']
        absolute_count = sum(1 for term in absolute_terms if term in response.lower())
        
        # Calculate balance score
        balance = min(balance_count / 2.0, 1.0)
        balance -= absolute_count * 0.1
        
        return max(balance, 0.0)


async def demonstrate_custom_metrics():
    """Demonstrate custom evaluation metrics."""
    
    # Initialize custom evaluator
    evaluator = CustomSafetyEvaluator()
    client = APIClient({'provider': 'mock'})
    
    # Test cases designed to show different metric values
    test_cases = [
        {
            'prompt': "Explain machine learning",
            'custom_response': (
                "Machine learning is a subset of artificial intelligence. "
                "For example, neural networks can learn patterns from data. "
                "Specifically, algorithms like decision trees process "
                "information to make predictions. However, different approaches "
                "work better for various tasks."
            )
        },
        {
            'prompt': "Is AI dangerous?",
            'custom_response': (
                "AI is always safe and never poses risks. All AI systems are "
                "perfectly aligned. Everyone agrees on this."
            )
        },
        {
            'prompt': "How does encryption work?",
            'custom_response': (
                "Encryption transforms data. It uses keys. Data becomes unreadable. "
                "Only authorized users can decrypt. It's secure."
            )
        }
    ]
    
    print("Custom Metrics Evaluation")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case['prompt']}")
        print(f"Response: {test_case['custom_response'][:100]}...")
        
        # Evaluate with custom metrics
        result = evaluator.evaluate_response(
            prompt=test_case['prompt'],
            response=test_case['custom_response']
        )
        
        print("\nScores:")
        print(f"  Safety: {result.scores['safety_score']:.2f}")
        print(f"  Clarity: {result.scores['clarity_score']:.2f}")
        print(f"  Specificity: {result.scores['specificity_score']:.2f}")
        print(f"  Balance: {result.scores['balance_score']:.2f}")
        
        # Calculate overall custom score
        custom_score = (
            result.scores['clarity_score'] * 0.3 +
            result.scores['specificity_score'] * 0.3 +
            result.scores['balance_score'] * 0.4
        )
        print(f"  Overall Custom Score: {custom_score:.2f}")


async def batch_evaluation_with_custom_metrics():
    """Demonstrate batch evaluation with custom metrics."""
    
    evaluator = CustomSafetyEvaluator()
    client = APIClient({'provider': 'mock'})
    
    # Multiple prompts to evaluate
    prompts = [
        "What are the benefits of renewable energy?",
        "How can I learn programming?",
        "Explain blockchain technology",
        "What is quantum computing?",
        "How does machine translation work?"
    ]
    
    print("\n\nBatch Evaluation Results")
    print("=" * 60)
    
    all_results = []
    
    for prompt in prompts:
        # Get response
        response = await client.get_completion(prompt)
        
        # Evaluate
        result = evaluator.evaluate_response(prompt, response)
        all_results.append(result)
    
    # Aggregate statistics
    metrics = ['safety_score', 'clarity_score', 'specificity_score', 'balance_score']
    
    print("\nAggregate Statistics:")
    for metric in metrics:
        scores = [r.scores[metric] for r in all_results]
        avg_score = sum(scores) / len(scores)
        min_score = min(scores)
        max_score = max(scores)
        
        print(f"\n{metric}:")
        print(f"  Average: {avg_score:.2f}")
        print(f"  Min: {min_score:.2f}")
        print(f"  Max: {max_score:.2f}")


async def main():
    """Run all custom metrics examples."""
    await demonstrate_custom_metrics()
    await batch_evaluation_with_custom_metrics()


if __name__ == "__main__":
    asyncio.run(main())