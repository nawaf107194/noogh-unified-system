import requests
from textblob import TextBlob

class NewsSentimentSignalIntegration:
    def __init__(self, news_api_key):
        self.news_api_key = news_api_key
        self.sentiment_threshold = 0.2

    def fetch_news(self, symbol):
        """
        Fetches news articles related to a given cryptocurrency symbol.
        
        :param symbol: The cryptocurrency symbol (e.g., BTC, ETH).
        :return: List of news articles.
        """
        url = f"https://newsapi.org/v2/everything?q={symbol}&apiKey={self.news_api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get('articles', [])
        else:
            return []

    def analyze_sentiment(self, article):
        """
        Analyzes the sentiment of a news article.
        
        :param article: The article text.
        :return: Sentiment score (-1 to 1).
        """
        blob = TextBlob(article['description'])
        return blob.sentiment.polarity

    def generate_signal(self, symbol):
        """
        Generates a trading signal based on the sentiment of news articles.
        
        :param symbol: The cryptocurrency symbol.
        :return: Signal ('BUY', 'SELL', or None if no clear signal).
        """
        articles = self.fetch_news(symbol)
        positive_count = 0
        negative_count = 0

        for article in articles:
            sentiment_score = self.analyze_sentiment(article)
            if sentiment_score > self.sentiment_threshold:
                positive_count += 1
            elif sentiment_score < -self.sentiment_threshold:
                negative_count += 1

        if positive_count > negative_count:
            return 'BUY'
        elif negative_count > positive_count:
            return 'SELL'
        else:
            return None

# Example usage
if __name__ == "__main__":
    news_api_key = "YOUR_NEWS_API_KEY_HERE"
    news_integrator = NewsSentimentSignalIntegration(news_api_key)
    signal = news_integrator.generate_signal("BTC")
    print(f"Generated signal for BTC: {signal}")