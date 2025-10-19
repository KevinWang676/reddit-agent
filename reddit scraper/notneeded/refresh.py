import praw

CLIENT_ID="upll51xZa99cATpfm6RTXw"
CLIENT_SECRET="zQaFd4ZMquMVMfimCUNvVh0bHX7-9A"
USER_AGENT="python:FashionDCCScrape:0.1 (by /u/DCCscraper)"

reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri="http://localhost:8080",
    user_agent=USER_AGENT,
)

# The scopes you need: "read" covers posts & comments
print("Go to this URL and authorize the app:\n")
print(reddit.auth.url(["read"], "uniqueKey", "permanent"))

# After authorizing, you'll be redirected to http://localhost:8080/?state=...&code=...
# Copy the 'code' parameter from the URL and paste below:
code = input("\nPaste the code parameter from the URL here: ")

refresh_token = reddit.auth.authorize(code)
print("\nYour refresh token is:\n", refresh_token)