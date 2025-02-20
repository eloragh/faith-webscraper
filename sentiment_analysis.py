import pandas as pd
from textblob import TextBlob

DATA = 'multi_subreddit_ukrainian_refugee.csv'
OUTPUT = 'multi_subreddit_ukrainian_refugee_sentiment.csv'

df = pd.read_csv(DATA)

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


# we will combine the title and text so we can analyze both
df['combined_text'] = df['title'] + ' ' + df['text'].fillna('')
df['sentiment'] = df['combined_text'].apply(get_sentiment)

df.to_csv(OUTPUT, index=False)
print(f"Saved {len(df)} posts to {OUTPUT}")