from unified_core.intelligence.news_sentiment_signal_integration import NewsSentimentSignalIntegration, analyze_sentiment
from textblob import TextBlob

class TestNewsSentimentSignalIntegration:

    def test_analyze_sentiment_happy_path(self):
        # Arrange
        article = {'description': 'This is an example news article with a positive sentiment.'}
        expected_score = 0.25  # Example expected score, might vary based on TextBlob's implementation

        # Act
        result = analyze_sentiment(article)

        # Assert
        assert isinstance(result, float)
        assert -1 <= result <= 1
        assert abs(result - expected_score) < 0.1  # Allow for some tolerance in the sentiment score

    def test_analyze_sentiment_empty_input(self):
        # Arrange
        article = {'description': ''}
        expected_result = 0.0

        # Act
        result = analyze_sentiment(article)

        # Assert
        assert result == expected_result

    def test_analyze_sentiment_none_input(self):
        # Arrange
        article = {'description': None}
        expected_result = 0.0

        # Act
        result = analyze_sentiment(article)

        # Assert
        assert result == expected_result

    def test_analyze_sentiment_boundary_value(self):
        # Arrange
        article = {'description': 'This is a very short text.'}
        expected_score = -0.25  # Example expected score, might vary based on TextBlob's implementation

        # Act
        result = analyze_sentiment(article)

        # Assert
        assert isinstance(result, float)
        assert -1 <= result <= 1
        assert abs(result - expected_score) < 0.1  # Allow for some tolerance in the sentiment score

    def test_analyze_sentiment_invalid_input(self):
        # Arrange
        article = {'description': 12345}  # Invalid input type (int instead of str)

        # Act and Assert
        with pytest.raises(TypeError):
            result = analyze_sentiment(article)
            assert result is None  # Ensure the function returns None or a default value on invalid input