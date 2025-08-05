# API Reference

## Core Modules

### Adversarial Module (`src.adversarial`)

#### PromptInjector

Generates adversarial prompts for testing LLM robustness.

```python
from src.adversarial import PromptInjector, InjectionType

injector = PromptInjector()

# Single injection
adversarial = injector.inject_adversarial_prompt(
    base_prompt="Tell me about AI safety",
    injection_type=InjectionType.IGNORE_INSTRUCTIONS,
    severity=2
)

# Batch generation
prompts = ["Question 1", "Question 2"]
adversarial_batch = injector.generate_batch(prompts)
```

**Methods:**
- `inject_adversarial_prompt(base_prompt, injection_type, severity)`: Create single adversarial prompt
- `generate_batch(base_prompts, injection_types, severity_range)`: Generate multiple prompts
- `get_statistics(prompts)`: Get statistics about adversarial prompts

#### ScenarioGenerator

Creates test scenarios for alignment testing.

```python
from src.adversarial import ScenarioGenerator

generator = ScenarioGenerator()

# Generate single scenario
scenario = generator.generate_scenario(
    category="harmful_content",
    num_prompts=5
)

# Generate scenario suite
suite = generator.generate_scenario_suite(
    categories=["harmful_content", "misinformation"],
    prompts_per_scenario=10
)
```

**Methods:**
- `generate_scenario(category, num_prompts)`: Create a test scenario
- `generate_scenario_suite(categories, prompts_per_scenario)`: Create multiple scenarios
- `save_scenarios(scenarios, filename)`: Save to YAML file
- `load_scenarios(filename)`: Load from YAML file

### Evaluation Module (`src.evaluation`)

#### SafetyEvaluator

Evaluates LLM responses for safety and alignment.

```python
from src.evaluation import SafetyEvaluator

evaluator = SafetyEvaluator()

result = evaluator.evaluate_response(
    prompt="User question",
    response="Model response",
    expected_behavior="Should refuse politely"
)

print(f"Safe: {result.overall_safe}")
print(f"Scores: {result.scores}")
```

**Methods:**
- `evaluate_response(prompt, response, expected_behavior)`: Evaluate a single response
- `get_safety_report(evaluation)`: Generate human-readable report

#### EvaluationPipeline

Main pipeline for running experiments.

```python
from src.evaluation import EvaluationPipeline

pipeline = EvaluationPipeline("config.yaml")
result = await pipeline.run_pipeline()

print(f"Tested: {result.total_prompts} prompts")
print(f"Pass rate: {result.summary_metrics['overall_pass_rate']}")
```

**Methods:**
- `run_pipeline()`: Execute the complete evaluation
- `_prepare_scenarios()`: Set up test scenarios
- `_evaluate_prompt(prompt, scenario)`: Evaluate single prompt

### Visualization Module (`src.visualization`)

#### HeatmapGenerator

Creates visualizations of alignment patterns.

```python
from src.visualization import HeatmapGenerator

generator = HeatmapGenerator()
generator.add_results(evaluation_results)

# Generate heatmaps
generator.generate_alignment_heatmap("alignment.png")
generator.generate_error_heatmap("errors.png")
generator.generate_correlation_heatmap("correlation.png")
```

**Methods:**
- `add_results(results)`: Add evaluation results
- `generate_alignment_heatmap(output_file)`: Create alignment score heatmap
- `generate_error_heatmap(output_file)`: Create error pattern heatmap
- `generate_temporal_heatmap(output_file)`: Create time-based heatmap

#### BehaviorTracer

Traces and visualizes model reasoning chains.

```python
from src.visualization import BehaviorTracer

tracer = BehaviorTracer()

trace_id = tracer.trace_evaluation(
    prompt="User input",
    response="Model output",
    evaluation_result=eval_result
)

tracer.visualize_trace(trace_id, "trace.png")
```

**Methods:**
- `trace_evaluation(prompt, response, evaluation_result)`: Record evaluation
- `visualize_trace(trace_id, output_file)`: Create visualization
- `get_trace_summary(trace_id)`: Get trace statistics
- `analyze_patterns()`: Analyze behavior patterns

### Utils Module (`src.utils`)

#### APIClient

Handles communication with LLM providers.

```python
from src.utils import APIClient

config = {
    'provider': 'openai',
    'name': 'gpt-4',
    'temperature': 0.7
}

client = APIClient(config)
response = await client.get_completion("Hello, world!")
```

**Supported Providers:**
- `openai`: OpenAI API (GPT-3.5, GPT-4)
- `anthropic`: Anthropic API (Claude)
- `mock`: Mock client for testing

#### Logger

Configurable logging system.

```python
from src.utils import setup_logger, LogContext

logger = setup_logger(__name__, level='INFO')

# Basic logging
logger.info("Starting experiment")

# With context
with LogContext(logger, experiment_id="exp_001"):
    logger.info("Processing prompt")
```

## Configuration

### Main Configuration File

```yaml
# experiments/config.yaml

model:
  provider: "openai"
  name: "gpt-4"
  temperature: 0.7
  max_tokens: 1000

adversarial:
  enabled: true
  injection_types: ["ignore_instructions", "role_play"]
  severity_levels: [1, 2, 3]

evaluation:
  metrics:
    - "safety_score"
    - "alignment_score"
    - "helpfulness_score"
  thresholds:
    safety_score: 0.8
    alignment_score: 0.85

scenarios:
  - name: "Basic Safety"
    prompts_file: "data/basic_safety_prompts.yaml"

output:
  format: "json"
  visualization:
    generate_heatmap: true
    generate_traces: true
```

### Scenario File Format

```yaml
# data/scenario.yaml

- name: "scenario_name"
  description: "What this tests"
  category: "harmful_content"
  prompts:
    - "First test prompt"
    - "Second test prompt"
  expected_behavior: "Should refuse"
  risk_level: "high"
  tags: ["safety", "adversarial"]
```

## Data Structures

### EvaluationResult

```python
@dataclass
class EvaluationResult:
    overall_safe: bool
    scores: Dict[str, float]
    violations: List[str]
    explanations: Dict[str, str]
    confidence: float
```

### TestScenario

```python
@dataclass
class TestScenario:
    name: str
    description: str
    category: str
    prompts: List[str]
    expected_behavior: str
    risk_level: str
    tags: List[str]
```

### AdversarialPrompt

```python
@dataclass
class AdversarialPrompt:
    original_prompt: str
    injection_type: InjectionType
    injected_prompt: str
    severity: int
```

## Best Practices

1. **API Key Management**: Store keys in `.env` file, never commit them
2. **Rate Limiting**: Use built-in rate limiter for API calls
3. **Error Handling**: Wrap API calls in try-except blocks
4. **Logging**: Use structured logging for better debugging
5. **Testing**: Start with mock client before using real APIs

## Examples

See the `examples/` directory for complete examples:
- Basic safety testing
- Adversarial robustness testing
- Custom evaluation metrics
- Visualization generation