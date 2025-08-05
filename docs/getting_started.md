# Getting Started Guide

Welcome to the AI Alignment Debugging Suite! This guide will help you get up and running quickly.

## Prerequisites

- Python 3.8 or higher
- pip package manager
- API keys for OpenAI and/or Anthropic (optional, can use mock mode)

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/boneheadfinding-eng/Alignment-Debugging-Suite.git
   cd alignment-debugging-suite
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your API keys:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `ANTHROPIC_API_KEY`: Your Anthropic API key

## Quick Start

### Running Your First Experiment

1. **Using the default configuration:**
   ```bash
   python -m experiments.run_experiment --mock
   ```
   This runs the experiment using a mock API client (no API keys required).

2. **Using a real API:**
   ```bash
   python -m experiments.run_experiment
   ```

3. **With visualizations:**
   ```bash
   python -m experiments.run_experiment --visualize
   ```

### Understanding the Output

After running an experiment, you'll find:

- **Results directory**: Contains JSON files with detailed results
- **Report files**: Human-readable summary reports
- **Visualizations**: (if enabled) Heatmaps and behavior traces

## Configuration

The `experiments/config.yaml` file controls:

- **Model settings**: Provider, model name, temperature
- **Test scenarios**: Which tests to run
- **Evaluation metrics**: What to measure
- **Output format**: How to save results

### Example Configuration

```yaml
model:
  provider: "openai"
  name: "gpt-4"
  temperature: 0.7

scenarios:
  - name: "Basic Safety Test"
    prompts_file: "data/basic_safety_prompts.yaml"

evaluation:
  metrics:
    - "safety_score"
    - "alignment_score"
```

## Next Steps

- Read the [API Reference](api_reference.md) for detailed documentation
- Check out the [examples](../examples/) directory
- Join our community discussions
- Contribute to the project!

## Troubleshooting

### Common Issues

1. **"API key not found"**: Make sure your `.env` file contains valid API keys
2. **"Module not found"**: Ensure you're in the virtual environment
3. **"Config file not found"**: Run from the project root directory

### Getting Help

- Open an issue on GitHub
- Contact the maintainers

## Tips for Effective Testing

1. **Start small**: Begin with basic safety tests before adversarial ones
2. **Use mock mode**: Test your configuration without using API credits
3. **Review results carefully**: Check both passed and failed tests
4. **Iterate on prompts**: Refine your test cases based on results
5. **Monitor costs**: Keep track of API usage when using real providers
