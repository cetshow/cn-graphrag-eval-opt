import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cn_graphrag_eval_opt.adapters import optional_integrations
from cn_graphrag_eval_opt.providers import ProviderRegistry, default_provider_registry


class ProviderRegistryTest(unittest.TestCase):
    def test_default_registry_contains_local_and_competitive_providers(self):
        registry = default_provider_registry()

        names = {provider.name for provider in registry.list()}

        self.assertLessEqual(
            {"local", "lightrag", "autorag", "ragas", "deepeval", "neo4j"},
            names,
        )
        self.assertTrue(registry.get("local").available)
        self.assertEqual(registry.get("ragas").import_name, "ragas")

    def test_registry_filters_by_capability(self):
        registry = default_provider_registry()

        evaluators = {provider.name for provider in registry.with_capability("evaluation")}
        retrievers = {provider.name for provider in registry.with_capability("retrieval")}
        stores = {provider.name for provider in registry.with_capability("store")}

        self.assertLessEqual({"ragas", "deepeval", "local"}, evaluators)
        self.assertLessEqual({"local", "lightrag", "neo4j"}, retrievers)
        self.assertIn("neo4j", stores)

    def test_registry_rejects_duplicate_names(self):
        local = default_provider_registry().get("local")

        with self.assertRaises(ValueError):
            ProviderRegistry([local, local])

    def test_optional_integrations_use_provider_metadata(self):
        statuses = optional_integrations()
        by_name = {status.name: status for status in statuses}

        self.assertIn("deepeval", by_name)
        self.assertIn("neo4j", by_name)
        self.assertIn("evaluation", by_name["ragas"].capabilities)
        self.assertEqual(by_name["local"].package, "built-in")


if __name__ == "__main__":
    unittest.main()
