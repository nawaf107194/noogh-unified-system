import pytest
from unified_core.intelligence.news_sentiment_signal_integration import analyze_sentiment
from textblob import TextBlob

def test_analyze_sentiment_happy_path():
    article = {
        'description': 'The weather is beautiful today.'
    }
    result = analyze_sentiment(article)
    assert -1 < result < 1, "Sentiment score should be between -1 and 1"

def test_analyze_sentiment_empty_input():
    article = {}
    result = analyze_sentiment(article)
    assert result == 0, "Empty input should return a neutral sentiment"

def test_analyze_sentiment_none_input():
    article = None
    result = analyze_sentiment(article)
    assert result is None, "None input should return None"

def test_analyze_sentiment_boundary_values():
    article_positive = {
        'description': 'This is the best news ever!'
    }
    result_positive = analyze_sentiment(article_positive)
    assert result_positive == 1, "Positive sentiment should be close to 1"

    article_negative = {
        'description': 'This is the worst news ever.'
    }
    result_negative = analyze_sentiment(article_negative)
    assert result_negative == -1, "Negative sentiment should be close to -1"

def test_analyze_sentiment_invalid_input_type():
    with pytest.raises(TypeError):
        analyze_sentiment("Not a dictionary")

    with pytest.raises(KeyError):
        article_missing_key = {'title': 'News'}
        analyze_sentiment(article_missing_key)