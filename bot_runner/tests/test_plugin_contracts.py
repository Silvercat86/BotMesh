import unittest
from unittest.mock import patch

from pydantic import ValidationError

from core.plugin_contracts import (
    BirthdayConfig,
    get_plugin_contracts,
    model_contract,
    validate_plugin_config,
)
from core.registries import PLUGIN_REGISTRY


class PluginContractTests(unittest.TestCase):
    def test_every_registered_plugin_has_contract(self):
        contracts = get_plugin_contracts(PLUGIN_REGISTRY)

        self.assertEqual(set(contracts), set(PLUGIN_REGISTRY))

    def test_contract_contains_required_fields_and_constraints(self):
        contract = model_contract(BirthdayConfig)

        self.assertTrue(contract["fields"]["templates"]["required"])
        self.assertFalse(contract["fields"]["hour"]["required"])
        self.assertEqual(contract["fields"]["hour"]["minimum"], 0)
        self.assertEqual(contract["fields"]["hour"]["maximum"], 23)
        self.assertFalse(contract["additional_fields"])

    def test_invalid_plugin_config_is_rejected(self):
        with self.assertRaises(ValidationError):
            validate_plugin_config(
                PLUGIN_REGISTRY["birthday_plugin"],
                {
                    "templates": "birthday",
                    "storage_dir": "data",
                    "people_source": "people",
                    "chat_id": "1",
                    "hour": 30,
                },
            )

    def test_every_plugin_can_be_created_from_validated_config(self):
        configs = {
            "birthday_plugin": {"templates": "birthday", "storage_dir": "data/birthday", "people_source": "people", "chat_id": "1"},
            "clever_shma_plugin": {},
            "compliment_plugin": {},
            "employee_info_plugin": {},
            "march8_plugin": {"template": "March", "storage_dir": "data/march", "chat_id": "1"},
            "meme_plugin": {},
            "start_plugin": {},
            "welcome_plugin": {},
            "work_experience_plugin": {"templates_by_years": {"1": "One year"}, "storage_dir": "data/work", "people_source": "people", "chat_id": "1"},
        }

        with patch("pathlib.Path.mkdir"):
            for name, plugin_class in PLUGIN_REGISTRY.items():
                with self.subTest(plugin=name):
                    config = configs[name]
                    validate_plugin_config(plugin_class, config)
                    instance = plugin_class.from_config(config)
                    self.assertIsInstance(instance, plugin_class)


if __name__ == "__main__":
    unittest.main()
