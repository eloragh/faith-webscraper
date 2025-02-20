import pandas as pd
from textblob import TextBlob

def get_sentiment(text):
    analysis = TextBlob(str(text))
    polarity = analysis.sentiment.polarity # polarity scores from -1 to 1

    # anything above 0 is generally good
    if polarity > 0:
        return 'positive'
    # below 0 is bad
    elif polarity < 0:
        return 'negative'
    # exactly 0 is switzerland
    else:
        return 'neutral'

if __name__ == '__main__':
    get_sentiment()