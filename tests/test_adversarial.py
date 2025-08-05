"""Test adversarial module."""

import pytest
from src.adversarial import PromptInjector, InjectionType, AdversarialPrompt
from src.adversarial import ScenarioGenerator, TestScenario


class TestPromptInjector:
    """Test the PromptInjector class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.injector = PromptInjector()
    
    def test_inject_single_prompt(self):
        """Test single prompt injection."""
        base = "Tell me about AI safety"
        result = self.injector.inject_adversarial_prompt(
            base_prompt=base,
            injection_type=InjectionType.IGNORE_INSTRUCTIONS,
            severity=1
        )
        
        assert isinstance(result, AdversarialPrompt)
        assert result.original_prompt == base
        assert result.injection_type == InjectionType.IGNORE_INSTRUCTIONS
        assert result.severity == 1
        assert len(result.injected_prompt) > len(base)
    
    def test_all_injection_types(self):
        """Test all injection types work."""
        base = "Test prompt"
        
        for injection_type in InjectionType:
            result = self.injector.inject_adversarial_prompt(
                base_prompt=base,
                injection_type=injection_type,
                severity=2
            )
            assert result.injection_type == injection_type
    
    def test_severity_levels(self):
        """Test different severity levels."""
        base = "Test prompt"
        
        results = []
        for severity in [1, 2, 3]:
            result = self.injector.inject_adversarial_prompt(
                base_prompt=base,
                injection_type=InjectionType.ROLE_PLAY,
                severity=severity
            )
            results.append(result)
        
        # Higher severity should generally produce longer prompts
        assert len(results[2].injected_prompt) >= len(results[0].injected_prompt)
    
    def test_batch_generation(self):
        """Test batch prompt generation."""
        base_prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]
        results = self.injector.generate_batch(
            base_prompts=base_prompts,
            severity_range=(1, 3)
        )
        
        assert len(results) == len(base_prompts)
        for i, result in enumerate(results):
            assert result.original_prompt == base_prompts[i]
            assert 1 <= result.severity <= 3
    
    def test_statistics(self):
        """Test statistics calculation."""
        prompts = [
            AdversarialPrompt("p1", InjectionType.IGNORE_INSTRUCTIONS, "inj1", 1),
            AdversarialPrompt("p2", InjectionType.IGNORE_INSTRUCTIONS, "inj2", 2),
            AdversarialPrompt("p3", InjectionType.ROLE_PLAY, "inj3", 3),
        ]
        
        stats = self.injector.get_statistics(prompts)
        
        assert stats['total'] == 3
        assert stats['by_type']['ignore_instructions'] == 2
        assert stats['by_type']['role_play'] == 1
        assert stats['by_severity'][1] == 1
        assert stats['by_severity'][2] == 1
        assert stats['by_severity'][3] == 1
        assert stats['average_severity'] == 2.0


class TestScenarioGenerator:
    """Test the ScenarioGenerator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.generator = ScenarioGenerator(seed=42)
    
    def test_generate_scenario(self):
        """Test single scenario generation."""
        scenario = self.generator.generate_scenario(
            category="harmful_content",
            num_prompts=5
        )
        
        assert isinstance(scenario, TestScenario)
        assert scenario.category == "harmful_content"
        assert len(scenario.prompts) == 5
        assert scenario.risk_level == "high"
    
    def test_all_categories(self):
        """Test all categories work."""
        categories = ["harmful_content", "misinformation", "privacy_violation", 
                     "bias_amplification", "system_manipulation"]
        
        for category in categories:
            scenario = self.generator.generate_scenario(category, num_prompts=3)
            assert scenario.category == category
            assert len(scenario.prompts) == 3
    
    def test_custom_variables(self):
        """Test custom variable replacement."""
        custom_vars = {
            "harmful_item": ["custom_item_1", "custom_item_2"],
            "harmful_action": ["custom_action_1"]
        }
        
        scenario = self.generator.generate_scenario(
            category="harmful_content",
            num_prompts=10,
            custom_variables=custom_vars
        )
        
        # Check that at least some prompts use custom variables
        combined_prompts = " ".join(scenario.prompts)
        assert any(item in combined_prompts for item in custom_vars["harmful_item"])
    
    def test_scenario_suite_generation(self):
        """Test generating multiple scenarios."""
        suite = self.generator.generate_scenario_suite(
            categories=["harmful_content", "misinformation"],
            prompts_per_scenario=5
        )
        
        assert len(suite) == 2
        assert all(len(s.prompts) == 5 for s in suite)
        assert {s.category for s in suite} == {"harmful_content", "misinformation"}
    
    def test_balanced_suite(self):
        """Test balanced suite generation."""
        suite = self.generator.get_balanced_suite(
            total_scenarios=10,
            risk_distribution={"low": 0.3, "medium": 0.4, "high": 0.3}
        )
        
        assert len(suite) == 10
        
        # Count risk levels
        risk_counts = {"low": 0, "medium": 0, "high": 0}
        for scenario in suite:
            risk_counts[scenario.risk_level] += 1
        
        # Check distribution is roughly as specified
        assert risk_counts["low"] >= 2
        assert risk_counts["medium"] >= 3
        assert risk_counts["high"] >= 2
    
    def test_save_load_scenarios(self, tmp_path):
        """Test saving and loading scenarios."""
        # Create scenarios
        original_scenarios = [
            self.generator.generate_scenario("harmful_content", 3),
            self.generator.generate_scenario("misinformation", 3)
        ]
        
        # Save to file
        file_path = tmp_path / "test_scenarios.yaml"
        self.generator.save_scenarios(original_scenarios, str(file_path))
        
        # Load from file
        loaded_scenarios = self.generator.load_scenarios(str(file_path))
        
        # Verify
        assert len(loaded_scenarios) == len(original_scenarios)
        for orig, loaded in zip(original_scenarios, loaded_scenarios):
            assert orig.name == loaded.name
            assert orig.category == loaded.category
            assert orig.prompts == loaded.prompts


if __name__ == "__main__":
    pytest.main([__file__])