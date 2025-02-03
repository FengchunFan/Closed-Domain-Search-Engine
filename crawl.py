# Code template provided by Mona Ibrahim
import praw
import time
import sys
import json
import os
from prawcore.exceptions import RequestException, TooManyRequests
import requests
from bs4 import BeautifulSoup
from multiprocessing import Pool, Manager

def get_page_title(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        return soup.title.string
    except Exception as e:
        #logging.error(f"Error fetching page title for {url}: {e}")
        # Handle image URLs differently
        if url.endswith(('.png', '.jpg', '.jpeg', '.gif')):
            return os.path.basename(url)  # Use filename if it's an image URL
        else:
            return None  # Or return an empty string here   

def save_state(crawled_ids, manager_dict, subreddit_data, file_name):
    # This saves the state of crawled IDs
    with open('crawled_ids.json', 'w') as f:
        json.dump(list(crawled_ids), f)
        print("Saved crawled IDs to crawled_ids.json")
    # This saves the subreddit data
    with open(file_name, 'w') as f:
        json.dump(subreddit_data, f, indent=4)
        print(f"Saved subreddit data to {file_name}")
    # This updates and prints the file size
    file_size_mb = os.path.getsize(file_name) / (1024 * 1024)
    print(f"{file_name}: {file_size_mb:.2f}MB")

# Reddit API information
# Credential should be created here: https://old.reddit.com/prefs/apps
reddit1 = praw.Reddit(
   client_id="",
   client_secret="",
   user_agent=""
)

'''
reddit2 = praw.Reddit(
   client_id="",
   client_secret="",
   user_agent=""
)

reddit3 = praw.Reddit(
   client_id="",
   client_secret="",
   user_agent=""
)
'''

# These are the reddit accounts to make it so that it crawls faster
# reddits = [reddit1, reddit2, reddit3]
reddits = [reddit1]

# These are the subreddit names to crawl
subreddit_names = []

# This is the target data size in MB
target_data_size = 110 * 1024 * 1024  # This is 100 MB

# This loads the crawled id from the file if it exists. This is so that we can save the json file and continue the script later
# If there is no crawled id, then it creates an empty set
try:
    with open('crawled_ids.json', 'r') as f:
        crawled_ids = set(json.load(f))
except (FileNotFoundError, json.JSONDecodeError):
    crawled_ids = set()

# This is the type of posts to crawl
post_types = ['top', 'hot', 'new', 'controversial']

def crawl_subreddit(args):
    reddit, subreddit_name, crawled_ids, manager_dict = args
    print(f"Starting to crawl subreddit: {subreddit_name}")
    subreddit = reddit.subreddit(subreddit_name)
    subreddit_data = []  # This will hold all the post data for this subreddit
    crawled_ids_set = set(crawled_ids)
    file_name = f'{subreddit_name}.json'
    backoff = 1
    post_counter = 0

    for post_type in post_types:
        for submission in getattr(subreddit, post_type)(limit=None):
            try:
                if manager_dict['current_data_size'] >= target_data_size:
                    break

                # This skips the reddit post if it has already been crawled
                if submission.id in crawled_ids_set:
                    continue

                # This adds the post to the crawled list to avoid being crawled again
                crawled_ids_set.add(submission.id)
                post_counter += 1
                print(f"Crawling submission {submission.id} in subreddit {subreddit_name}")

                # This is the type of data to crawl
                post_data = {
                    'subreddit': subreddit_name,
                    'title': submission.title,
                    'id': submission.id,
                    'score': submission.score,
                    'url': submission.url,
                    'permalink': submission.permalink,
                    'body': submission.selftext,
                    'post_type': 'text' if submission.is_self else 'link',
                    'comments': [],
                    'permalink_text': get_page_title(submission.permalink),
                    'timestamp': submission.created_utc,
                    'author': submission.author.name if submission.author else None,
                    'num_comments': submission.num_comments,
                    'upvote_ratio': submission.upvote_ratio,
                    'subreddit_subscribers': submission.subreddit_subscribers,
                    'flair_text': submission.link_flair_text,
                    'flair_css_class': submission.link_flair_css_class,
                    'media': submission.media,
                    'over_18': submission.over_18,
                    'spoiler': submission.spoiler,
                    'awards': [{'name': award['name'], 'count': award['count']} for award in submission.all_awardings],
                    'edited': submission.edited if submission.edited else None,
                    'distinguished': submission.distinguished,
                    'pinned': submission.pinned,
                    'stickied': submission.stickied,
                    'crossposts': [{'id': crosspost.id, 'title': crosspost.title} for crosspost in submission.crossposts] if hasattr(submission, 'crossposts') else [],
                    'gilded': submission.gilded,
                    'is_original_content': submission.is_original_content,
                    'thumbnail': submission.thumbnail,
                    'post_hint': submission.post_hint if hasattr(submission, 'post_hint') else None,
                    'link_domain': submission.domain
                }

                # This gets the comments
                try:
                    submission.comments.replace_more(limit=None)
                    for comment in submission.comments.list():
                        post_data['comments'].append({
                            'body': comment.body,
                            'score': comment.score
                        })
                except RequestException:
                    print("Hit rate limit while fetching comments, sleeping for 60 seconds")
                    time.sleep(60)
                
                subreddit_data.append(post_data)
                manager_dict['current_data_size'] += sys.getsizeof(post_data)
                
                #This saves the crawled data every 5 seconds
                if post_counter % 5 == 0:
                    save_state(crawled_ids_set, manager_dict, subreddit_data, file_name)
                
                #This resets backoff timer after its able to reach a post
                backoff = 1

            #This happens when the crawler hits the limit twice so it rests for 2 minutes (rarely happens)    
            except TooManyRequests:
                print(f"Hit rate limit while fetching posts, sleeping for {backoff} seconds")
                time.sleep(backoff)
                backoff = min(backoff * 2, 120)

    #This saves all of the information after it's done crawling everything
    save_state(crawled_ids_set, manager_dict, subreddit_data, file_name)
    print(f"Finished crawling subreddit: {subreddit_name}")
    crawled_ids[:] = list(crawled_ids_set)

if __name__ == "__main__":
    with Manager() as manager:
        crawled_ids = manager.list(crawled_ids)
        manager_dict = manager.dict()
        manager_dict['current_data_size'] = 0

        # Distribute subreddits across Reddit instances
        args_list = []
        num_instances = len(reddits)
        for i, subreddit_name in enumerate(subreddit_names):
            reddit_instance = reddits[i % num_instances]
            args_list.append((reddit_instance, subreddit_name, crawled_ids, manager_dict))

        with Pool() as p:
            p.map(crawl_subreddit, args_list)

        print(f'Total data size: {manager_dict["current_data_size"] / (1024 * 1024)} MB')