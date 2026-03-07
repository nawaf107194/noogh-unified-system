import pytest

class TestTrajectoryRecorder:

    def test_happy_path(self):
        # Normal inputs
        api_url = "https://example.com/api"
        api_key = "my_api_key"
        model = "noogh-teacher"

        recorder = TrajectoryRecorder(api_url, api_key, model)
        assert recorder.api_url == api_url.rstrip("/")
        assert recorder.api_key == api_key
        assert recorder.model == model
        assert recorder.headers == {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

    def test_edge_case_empty_api_key(self):
        # Empty api_key
        api_url = "https://example.com/api"
        api_key = ""
        model = "noogh-teacher"

        recorder = TrajectoryRecorder(api_url, api_key, model)
        assert recorder.api_url == api_url.rstrip("/")
        assert recorder.api_key == "EMPTY"
        assert recorder.model == model
        assert recorder.headers == {
            "Content-Type": "application/json",
            "Authorization": f"Bearer EMPTY"
        }

    def test_edge_case_none_api_key(self):
        # None api_key
        api_url = "https://example.com/api"
        api_key = None
        model = "noogh-teacher"

        recorder = TrajectoryRecorder(api_url, api_key, model)
        assert recorder.api_url == api_url.rstrip("/")
        assert recorder.api_key == "EMPTY"
        assert recorder.model == model
        assert recorder.headers == {
            "Content-Type": "application/json",
            "Authorization": f"Bearer EMPTY"
        }

    def test_edge_case_empty_model(self):
        # Empty model
        api_url = "https://example.com/api"
        api_key = "my_api_key"
        model = ""

        recorder = TrajectoryRecorder(api_url, api_key, model)
        assert recorder.api_url == api_url.rstrip("/")
        assert recorder.api_key == api_key
        assert recorder.model == "noogh-teacher"
        assert recorder.headers == {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

    def test_edge_case_none_model(self):
        # None model
        api_url = "https://example.com/api"
        api_key = "my_api_key"
        model = None

        recorder = TrajectoryRecorder(api_url, api_key, model)
        assert recorder.api_url == api_url.rstrip("/")
        assert recorder.api_key == api_key
        assert recorder.model == "noogh-teacher"
        assert recorder.headers == {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

    def test_edge_case_empty_api_url(self):
        # Empty api_url
        api_url = ""
        api_key = "my_api_key"
        model = "noogh-teacher"

        recorder = TrajectoryRecorder(api_url, api_key, model)
        assert recorder.api_url == "/"
        assert recorder.api_key == api_key
        assert recorder.model == model
        assert recorder.headers == {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

    def test_edge_case_none_api_url(self):
        # None api_url
        api_url = None
        api_key = "my_api_key"
        model = "noogh-teacher"

        recorder = TrajectoryRecorder(api_url, api_key, model)
        assert recorder.api_url == "/"
        assert recorder.api_key == api_key
        assert recorder.model == model
        assert recorder.headers == {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

    def test_edge_case_empty_headers(self):
        # Empty headers
        api_url = "https://example.com/api"
        api_key = ""
        model = ""

        recorder = TrajectoryRecorder(api_url, api_key, model)
        assert recorder.api_url == api_url.rstrip("/")
        assert recorder.api_key == "EMPTY"
        assert recorder.model == "noogh-teacher"
        assert recorder.headers == {
            "Content-Type": "application/json",
            "Authorization": f"Bearer EMPTY"
        }

    def test_edge_case_none_headers(self):
        # None headers
        api_url = "https://example.com/api"
        api_key = None
        model = None

        recorder = TrajectoryRecorder(api_url, api_key, model)
        assert recorder.api_url == api_url.rstrip("/")
        assert recorder.api_key == "EMPTY"
        assert recorder.model == "noogh-teacher"
        assert recorder.headers == {
            "Content-Type": "application/json",
            "Authorization": f"Bearer EMPTY"
        }