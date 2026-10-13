"""Deterministic placeholder for optional model-provider integrations."""
from .base import PHIGuard


class MockLLM:
    def __init__(self, system_name: str = "Immunopeptidome Neoantigen Agent"):
        self.system_name = system_name

    def invoke(self, prompt: str) -> str:
        PHIGuard.assert_no_phi(prompt)
        return (
            f"[{self.system_name}] MOCK response only. "
            "No language model or scientific validation was performed. "
            f"Query: {prompt[:60]!r}"
        )


class LLMFactory:
    """Return the deterministic placeholder; external model adapters are not implemented."""

    @staticmethod
    def create(provider: str = "mock", system_name: str = "Immunopeptidome Neoantigen Agent"):
        # Other names are retained for backward compatibility but are not live providers.
        return MockLLM(system_name)
