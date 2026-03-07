import pytest

class MockCognitiveJournal:
    def get_episode(self, episode_id):
        if episode_id == 1:
            return {
                'events': ['Event1', 'Event2', 'Event3', 'Event4', 'Event5', 'Event6'],
                'emotions': {'happy': 0.8, 'sad': 0.2},
                'outcome': 'Success'
            }
        elif episode_id == -1:
            return {
                'events': [],
                'emotions': {},
                'outcome': ''
            }
        elif episode_id is None:
            raise ValueError("Invalid episode ID")
        else:
            raise KeyError(f"Episode {episode_id} not found")

class MemorySummarizer:
    def __init__(self):
        self.cognitive_journal = MockCognitiveJournal()

    def _summarize_memory(self, episode_id: int) -> dict:
        episode_details = self.cognitive_journal.get_episode(episode_id)
        
        summary = {
            'episode_id': episode_id,
            'key_events': episode_details['events'][:5],
            'emotions': episode_details['emotions'],
            'outcome': episode_details['outcome']
        }
        
        return summary

@pytest.fixture
def memory_summarizer():
    return MemorySummarizer()

# Happy path (normal inputs)
def test_happy_path(memory_summarizer):
    result = memory_summarizer._summarize_memory(1)
    expected = {
        'episode_id': 1,
        'key_events': ['Event1', 'Event2', 'Event3', 'Event4', 'Event5'],
        'emotions': {'happy': 0.8, 'sad': 0.2},
        'outcome': 'Success'
    }
    assert result == expected

# Edge cases (empty, None, boundaries)
def test_edge_case_empty(memory_summarizer):
    result = memory_summarizer._summarize_memory(-1)
    expected = {
        'episode_id': -1,
        'key_events': [],
        'emotions': {},
        'outcome': ''
    }
    assert result == expected

# Error cases (invalid inputs)
def test_error_case_invalid_input(memory_summarizer):
    with pytest.raises(ValueError) as exc_info:
        memory_summarizer._summarize_memory(None)
    assert str(exc_info.value) == "Invalid episode ID"

# Async behavior (if applicable)
# This function is synchronous, so no async testing is needed.