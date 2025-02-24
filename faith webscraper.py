# imports
from dotenv import load_dotenv
from datetime import datetime, timezone
from googletrans import Translator
from nltk.sentiment import SentimentIntensityAnalyzer
import os
import re
import nltk
import praw
import time
import pandas as pd

load_dotenv('config.env')

# globals
CLIENT_ID = os.getenv('CLIENT_ID')
SECRET = os.getenv('SECRET')
USER_AGENT = os.getenv('USER_AGENT')
OUTPUT = 'ukrainian_migration_to_poland_data.xlsx'

# nltk sentiment lexicon
# this lexicon is specifically designed to be used for social media analysis :)
nltk.download('vader_lexicon')

# initialize sentiment analysis object
sia = SentimentIntensityAnalyzer()

# initialize translator object
translator = Translator()

# creds
reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=SECRET,
    user_agent=USER_AGENT
)

subreddits_queries = {
    "poland": [
        "ukrainian",
        "ukraine",
        "ukrainians in poland", 
        "ukrainian migration", 
        "ukrainian asylum", 
        "poland refugees", 
        "poland border crisis"
    ],
    "polska": [
        "ukraina",
        "ukraina uchodźcy", 
        "ukraińscy uchodźcy", 
        "uchodźcy w polsce", 
        "migracja ukraina", 
        "granica polska ukraina"
    ]
}

# define the date range
start_date = datetime(2022, 2, 24, tzinfo=timezone.utc)  # the war started February 24, 2022
start_timestamp = int(start_date.timestamp())  # Convert to unix timestamp

def clean_text(text):

    # removes non-alphanumeric characters from strings
    if isinstance(text, str) and len(text) > 0:  # make sure it's a string and it's worth processing

        # remove emojis and symbols using Unicode ranges
        text = re.sub(r'[^\w\s\.,!?;:\'\"-]', '', text)
        return text.strip()
    
    return text  # return unprocessed text if it's not a string

def translate_text(text, index, src_lang="pl", dest_lang="en", max_retries=3):

    if not text or not isinstance(text, str):  # don't bother if it's not a string
        print(f'Row {index} is empty or not a string')
        return 'fail'  

    retries = 0
    while retries < max_retries:
        try:
            if pd.isna(text) or text.strip() == '':
                print(f'Row {index} is null')
                return 'fail'
            
            translated = translator.translate(text, src=src_lang, dest=dest_lang).text
            if translated and isinstance(translated, str):  # valid response
                return translated
            
        except Exception as e:
            wait_time = 2 ** retries  # exponential backoff (2, 4, 8, 16 sec)
            #print(f"Row {index} translation error: {e}. Retrying in {wait_time} seconds... ({retries+1}/{max_retries})")
            time.sleep(wait_time)  # google hates me
            retries += 1  

    print(f'Row {index} translation failed.')
    return 'fail'

def get_sentiment(text):
    # returns sia scores and simple translation of compound score
    sia_scores = sia.polarity_scores(str(text))
    compound = sia_scores['compound']

    if compound > 0.05:
        simple_sentiment = 'positive'
    elif compound < -0.05:
        simple_sentiment = 'negative'
    else:
        simple_sentiment = 'neutral'   

    return sia_scores, simple_sentiment

# get those posts bitch!
def get_posts(subreddit_name, query, limit=10000, start=start_timestamp):

    subreddit = reddit.subreddit(subreddit_name)
    posts = []

    for post in subreddit.search(query, limit=limit):
        sub_posts = []
        # get timestamp
        post_date = datetime.fromtimestamp(post.created_utc, timezone.utc)
        # only collect posts from February 24, 2022 and onward
        if post.created_utc >= start:

            sub_posts.append({
                "title": clean_text(post.title),
                "text": post.selftext,
                "subreddit": post.subreddit.display_name,
                "date": post_date.strftime('%Y-%m-%d %H:%M:%S'),
                "url": post.url
            })

        posts.extend(sub_posts)
    
    return posts

def main():

    all_posts = []
    # get posts from each subreddit and add them all to one list
    for sub, queries in subreddits_queries.items():
        for query in queries:
            print(f'Fetching posts from r/{sub} with query: {query}')
            all_posts.extend(get_posts(sub, query))

    # turn posts into a dataframe
    df = pd.DataFrame(all_posts)
    df.drop_duplicates(subset=['url'])

    # combine title and text first
    df['combined text'] = df['title'] + ' ' + df['text']
    print(f"Unprocessed output: {len(df)} posts.")

    # translate only for r/Polska
    print(f'Translating...')
    df['combined text en'] = df.apply(
        lambda row: translate_text(row['combined text'], row.name) if row['subreddit'] == 'Polska' 
        else row['combined text'],
        axis=1
    )

    # drop rows where Polish text failed to translate
    failed_translations = (df["combined text en"] == "fail").sum()
    print(f"{failed_translations} posts failed to translate and were dropped.")
    df = df[df['combined text en'] != "fail"]

    df[['sia sentiment', 'simple sentiment']] = df['combined text en'].apply(get_sentiment).apply(pd.Series)

    # save it in an excel
    df.to_excel(OUTPUT, index=False)
    print(f"Saved {len(df)} posts to {OUTPUT}")

if __name__ == '__main__':
    main()