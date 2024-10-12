import praw
import csv
from datetime import datetime, timedelta
import time

# You will have to create a script app on your Reddit account and fill in
# your CLIENT_ID and CLIENT_SECRET
# Authentication
reddit = praw.Reddit(
    client_id="MY_CLIENT_ID",  # MY_CLIENT_ID
    client_secret="MY_CLIENT_SECRET",  # MY_CLIENT_SECRET
    user_agent="wsb_scraper v1.0 by u/<my_reddit_username>" # MY_USER_AGENT
)

# Specify the subreddit
subreddit = reddit.subreddit("wallstreetbets")


# Function to find the "What are your moves tomorrow?" post more flexibly
def find_daily_post(subreddit):
    requests_made = 0
    # Search for posts with "moves" or "your moves" in the title from the current day
    for submission in subreddit.search("moves", sort="new", time_filter="day"):

        if "your moves" in submission.title.lower():
            return submission
    return None


# Get the daily post
daily_post = find_daily_post(subreddit)
try:
    if daily_post:
        print(f"Found post: {daily_post.title}")

        # Collect comments
        daily_post.comments.replace_more(limit=None)  # Load all comments
        comments = daily_post.comments.list()

        # Create a CSV file to store the comments
        filename = f"wsb_comments_{datetime.now().strftime('%Y-%m-%d')}.csv"

        # Initialize a list to store collected comments
        collected_comments = []

        with open(filename, "w", newline='', encoding="utf-8") as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(["Comment ID", "Username", "Comment Body", "Upvotes", "Date"])

            requests_made = 0  # Reset the request counter for comments
            start_time = datetime.now()
            max_runtime = timedelta(minutes=15)  # Set max runtime to x minutes
            max_comments = 2500  # Optional: limit number of comments to process

            for index, comment in enumerate(comments, start=1):
                # Stop if the maximum runtime has been exceeded
                if datetime.now() - start_time > max_runtime:
                    print("Max runtime exceeded. Stopping the script.")
                    break

                # Stop if the maximum number of comments has been processed
                if index > max_comments:
                    print("Max number of comments processed. Stopping the script.")
                    break

                # Check if the comment has an author (not deleted)
                author_name = comment.author.name if comment.author else "[deleted]"
                collected_comments.append([
                    comment.id,
                    author_name,
                    comment.body,
                    comment.score,
                    datetime.utcfromtimestamp(comment.created_utc).strftime('%Y-%m-%d %H:%M:%S')
                ])

                # Increment the request counter for each comment written (if necessary)
                requests_made += 1

                # If nearing the limit, pause to avoid hitting the rate limit
                if requests_made >= 55:
                    print("Rate limit approaching while processing comments, sleeping for 60 seconds...")
                    time.sleep(60)
                    requests_made = 0  # Reset the counter

                # Print progress every 100 comments processed
                if index % 100 == 0:
                    print(f"Processed {index} comments so far...")

            # Write all collected comments to the CSV after processing
            for comment in collected_comments:
                csvwriter.writerow(comment)

        print(f"Comments saved to {filename}")
    else:
        print("Daily post not found!")

except KeyboardInterrupt:
    print("\nScript interrupted. Writing collected data to CSV file...")

    # Write the collected comments to the CSV file if interrupted
    if collected_comments:
        with open(filename, "w", newline='', encoding="utf-8") as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(["Comment ID", "Username", "Comment Body", "Upvotes", "Date"])
            for comment in collected_comments:
                csvwriter.writerow(comment)

    print(f"Partial data saved to {filename}. Exiting the script.")
