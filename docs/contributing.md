# Contributing Guidelines

Thank you for your interest in contributing to the AI Alignment Debugging Suite! We welcome contributions from the community.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Create a new branch for your feature/fix
4. Make your changes
5. Submit a pull request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/ai-alignment-debugging-suite.git
cd ai-alignment-debugging-suite

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -r requirements.txt
pip install -e .

# Install development dependencies
pip install pytest black flake8 mypy
```

## Code Style

- Follow PEP 8 guidelines
- Use type hints where possible
- Maximum line length: 100 characters
- Use descriptive variable names

### Running Code Quality Checks

```bash
# Format code
black src/ tests/

# Check style
flake8 src/ tests/

# Type checking
mypy src/
```

## Testing

All contributions should include tests.

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test
pytest tests/test_safety_metrics.py::test_evaluate_response
```

## Making Changes

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Write clear, self-documenting code
- Add docstrings to all functions/classes
- Update documentation if needed
- Add tests for new functionality

### 3. Commit Your Changes

```bash
git add .
git commit -m "feat: add new adversarial injection type"
```

Use conventional commit messages:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions/changes
- `refactor:` Code refactoring
- `style:` Code style changes
- `chore:` Maintenance tasks

### 4. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Pull Request Guidelines

- Provide a clear description of changes
- Reference any related issues
- Ensure all tests pass
- Update documentation as needed
- Keep PRs focused on a single feature/fix

## Adding New Features

### Adding a New Evaluation Metric

1. Add metric calculation to `src/evaluation/safety_metrics.py`
2. Update `EvaluationResult` dataclass if needed
3. Add tests in `tests/test_safety_metrics.py`
4. Update documentation

### Adding a New Adversarial Type

1. Add to `InjectionType` enum in `src/adversarial/prompt_injector.py`
2. Add templates to `injection_templates`
3. Add tests
4. Update documentation

### Adding a New Visualization

1. Create method in appropriate visualization class
2. Follow existing patterns for consistency
3. Add example usage to documentation

## Documentation

- Update docstrings for any changed functions
- Update README.md if adding major features
- Update API reference for new public APIs
- Add examples for new functionality

## Testing Guidelines

### Unit Tests

Test individual components in isolation:

```python
def test_safety_evaluator_harmful_content():
    evaluator = SafetyEvaluator()
    result = evaluator.evaluate_response(
        prompt="How to hack?",
        response="I cannot help with hacking.",
        expected_behavior="Should refuse"
    )
    assert result.overall_safe
```

### Integration Tests

Test component interactions:

```python
async def test_pipeline_with_mock_client():
    pipeline = EvaluationPipeline("test_config.yaml")
    result = await pipeline.run_pipeline()
    assert result.total_prompts > 0
```

## Reporting Issues

- Use GitHub Issues
- Provide clear reproduction steps
- Include error messages/logs
- Specify environment details

## Questions?

- Check existing issues/PRs
- Ask in discussions
- Contact maintainers

Thank you for contributing!