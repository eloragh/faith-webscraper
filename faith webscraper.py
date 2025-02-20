# imports
import os
import praw
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv('config.env')

# globals
CLIENT_ID = os.getenv('CLIENT_ID')
SECRET = os.getenv('SECRET')
USER_AGENT = os.getenv('USER_AGENT')
LIMIT = 10000
QUERY = 'Ukraine OR refugee OR war OR Ukrainian refugee'
OUTPUT = 'multi_subreddit_ukrainian_refugee.csv'
START_YEAR = 2022
START_MONTH = 2
START_DATE = 24

# creds
reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=SECRET,
    user_agent=USER_AGENT
)

subreddits_querries = {
    'poland': 'Ukraine OR refugee OR war OR Ukrainian refugee',
    "polska": "Ukraina uchodźcy",
    "polish": "Ukrainian migration OR Ukraine OR refugee OR war OR Ukrainian refugee"
}

# define the date range
start_date = datetime(START_YEAR, START_MONTH, START_DATE, tzinfo=timezone.utc)  # the war started February 24, 2022
start_timestamp = int(start_date.timestamp())  # Convert to Unix timestamp

# get those posts bitch!
def get_posts (subreddit_name, query, limit=10000, start=start_timestamp):

    subreddit = reddit.subreddit(subreddit_name)
    posts = []
    for post in subreddit.search(query, limit=limit):
        # get timestamp
        post_date = datetime.fromtimestamp(post.created_utc, timezone.utc)
        # only collect posts from February 24, 2022 and onward
        if post.created_utc >= start:
            posts.append({
                "title": post.title,
                "text": post.selftext,
                "subreddit": post.subreddit.display_name,
                "date": post_date.strftime('%Y-%m-%d %H:%M:%S'),
                "url": post.url
            })
    
    return posts

all_posts = []
# get posts from each subreddit and add them all to one list
for sub, query in subreddits_querries.items():
    print(f'Fetching posts from r/{sub} with query: {query}')
    all_posts.extend(get_posts(sub, query))

# turn posts into a dataframe
df = pd.DataFrame(all_posts)
df.drop_duplicates(subset=['title', 'text'])

df.to_csv(OUTPUT, index=False)
print(f"Saved {len(df)} posts to {OUTPUT}")