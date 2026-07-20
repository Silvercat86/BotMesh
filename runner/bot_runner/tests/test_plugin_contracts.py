import unittest
from unittest.mock import patch

from pydantic import ValidationError

from core.plugin_contracts import (
    BirthdayConfig,
    get_plugin_contracts,
    get_service_contracts,
    model_contract,
    validate_plugin_config,
)
from core.registries import PLUGIN_REGISTRY
from core.registries import SERVICE_REGISTRY
from plugins.clever_shma.plugin import MODEL, OPENROUTER_URL
from plugins.march8.plugin import DEFAULT_TEMPLATE
from plugins.memes.plugin import MemePlugin
from plugins.start.plugin import DEFAULT_TEMPLATES
from plugins.welcome.plugin import DEFAULT_BASE_TEMPLATE, DEFAULT_QUESTIONS


class PluginContractTests(unittest.TestCase):
    def test_every_registered_plugin_has_contract(self):
        contracts = get_plugin_contracts(PLUGIN_REGISTRY)

        self.assertEqual(set(contracts), set(PLUGIN_REGISTRY))
        self.assertIn("config", contracts["birthday_plugin"])
        self.assertEqual(
            contracts["birthday_plugin"]["required_services"],
            ["people_directory_service"],
        )
        self.assertIn("birthday_test", contracts["birthday_plugin"]["actions"])

    def test_every_registered_service_has_contract(self):
        contracts = get_service_contracts(SERVICE_REGISTRY)
        self.assertEqual(set(contracts), set(SERVICE_REGISTRY))
        self.assertIn("sources", contracts["people_directory_service"]["fields"])

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
                    if name == "start_plugin":
                        self.assertTrue(instance.messages)

    def test_empty_values_use_plugin_fallbacks(self):
        start = PLUGIN_REGISTRY["start_plugin"].from_config({"messages": []})
        welcome = PLUGIN_REGISTRY["welcome_plugin"].from_config({
            "base_template": "", "questions": [], "n_questions": 3, "dedupe_ttl_seconds": 30,
        })
        march8 = PLUGIN_REGISTRY["march8_plugin"].from_config({
            "template": "", "storage_dir": "data/march", "photo": None,
            "hour": 6, "minute": 0, "chat_id": "",
        })
        meme = MemePlugin.from_config({"data_file": ""})
        clever = PLUGIN_REGISTRY["clever_shma_plugin"].from_config({
            "api_url": "", "model": "", "system_prompt": None,
            "temperature": 0.7, "max_tokens": 1024, "timeout_seconds": 60,
        })

        self.assertEqual(start.messages, DEFAULT_TEMPLATES)
        self.assertEqual(welcome.base_template, DEFAULT_BASE_TEMPLATE)
        self.assertEqual(welcome.questions, DEFAULT_QUESTIONS)
        self.assertEqual(march8.template, DEFAULT_TEMPLATE)
        self.assertEqual(str(meme.data_file).replace("\\", "/"), "data/memes/memes.txt")
        self.assertEqual(clever.api_url, OPENROUTER_URL)
        self.assertEqual(clever.model, MODEL)


if __name__ == "__main__":
    unittest.main()
