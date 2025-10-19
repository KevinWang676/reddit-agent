import praw
import os
from dotenv import load_dotenv

load_dotenv()

reddit = praw.Reddit(
    client_id=os.getenv("CLIENT_ID"),
    client_secret=os.getenv("CLIENT_SECRET"),
    user_agent=os.getenv("USER_AGENT"),
)

print("Read-only mode, username is:", reddit.user.me())  # → None

for post in reddit.subreddit("malefashionadvice").hot(limit=5):
    print(post.title, post.score)