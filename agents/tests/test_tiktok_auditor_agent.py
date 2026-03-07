import pytest

class MockTikTokAuditorAgent:
    def _get_ytdlp_options(self, max_downloads: int = 5):
        """Configurations to extract metadata safely without downloading the massive MP4."""
        return {
            'extract_flat': True,       # Fast extraction, don't follow all links deeply immediately
            'playlistend': max_downloads, # Max number of videos to fetch from the profile
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,       # Skip deleted/private videos
            'skip_download': True,      # Do NOT download the actual video file, we just want metadata
            # Add user agent to prevent blocks
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
        }

@pytest.fixture
def agent():
    return MockTikTokAuditorAgent()

def test_get_ytdlp_options_happy_path(agent):
    result = agent._get_ytdlp_options(max_downloads=3)
    assert isinstance(result, dict)
    assert 'extract_flat' in result and result['extract_flat'] is True
    assert 'playlistend' in result and result['playlistend'] == 3
    assert 'quiet' in result and result['quiet'] is True
    assert 'no_warnings' in result and result['no_warnings'] is True
    assert 'ignoreerrors' in result and result['ignoreerrors'] is True
    assert 'skip_download' in result and result['skip_download'] is True
    assert 'http_headers' in result and result['http_headers']['User-Agent'] == 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

def test_get_ytdlp_options_edge_cases(agent):
    result = agent._get_ytdlp_options(max_downloads=0)
    assert isinstance(result, dict)
    assert 'playlistend' in result and result['playlistend'] == 0
    
    result = agent._get_ytdlp_options(max_downloads=None)
    assert isinstance(result, dict)
    assert 'playlistend' not in result

def test_get_ytdlp_options_error_cases(agent):
    # There are no explicit error cases in the function, so this test is omitted
    pass

# async tests would be added here if the method were async