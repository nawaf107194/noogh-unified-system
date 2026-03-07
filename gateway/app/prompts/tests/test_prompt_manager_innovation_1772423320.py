import os
import json
from unittest.mock import patch

class MockPromptTemplate:
    def __init__(self, id):
        self.id = id

class TestPromptManager:

    @pytest.fixture
    def prompt_manager(self, tmpdir):
        from gateway.app.prompts.prompt_manager import PromptManager
        manager = PromptManager(storage_dir=tmpdir)
        yield manager

    def test_load_prompts_happy_path(self, prompt_manager, tmpdir):
        prompts_data = [
            {"id": "1", "template": "Prompt 1"},
            {"id": "2", "template": "Prompt 2"}
        ]
        os.makedirs(tmpdir)
        with open(os.path.join(tmpdir, "prompts.json"), "w") as f:
            json.dump(prompts_data, f)

        prompt_manager._load_prompts()

        assert len(prompt_manager.prompts) == 2
        assert prompt_manager.prompts["1"].id == "1"
        assert prompt_manager.prompts["2"].id == "2"

    def test_load_prompts_empty_file(self, prompt_manager, tmpdir):
        os.makedirs(tmpdir)
        with open(os.path.join(tmpdir, "prompts.json"), "w") as f:
            json.dump([], f)

        prompt_manager._load_prompts()

        assert len(prompt_manager.prompts) == 0

    def test_load_prompts_file_not_exists(self, prompt_manager, tmpdir):
        prompt_manager.storage_dir = os.path.join(tmpdir, "nonexistent")

        prompt_manager._load_prompts()

        assert len(prompt_manager.prompts) == 0

    def test_load_prompts_invalid_json(self, prompt_manager, tmpdir):
        prompts_data = '{"id": "1", "template": "Prompt 1"'
        os.makedirs(tmpdir)
        with open(os.path.join(tmpdir, "prompts.json"), "w") as f:
            f.write(prompts_data)

        prompt_manager._load_prompts()

        assert len(prompt_manager.prompts) == 0

    def test_load_prompts_with_duplicates(self, prompt_manager, tmpdir):
        prompts_data = [
            {"id": "1", "template": "Prompt 1"},
            {"id": "1", "template": "Prompt 2"}
        ]
        os.makedirs(tmpdir)
        with open(os.path.join(tmpdir, "prompts.json"), "w") as f:
            json.dump(prompts_data, f)

        prompt_manager._load_prompts()

        assert len(prompt_manager.prompts) == 1
        assert prompt_manager.prompts["1"].id == "1"