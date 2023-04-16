# this python script is used to capture the reddit posts for the given subreddit
# the script returns the posts as title and url
# only the most recent 5 posts are returned
# the request url is https://www.reddit.com/r/<subreddit_name>/new.json?limit=5


import os
import time
import requests
import json
from src.commons import send_to_slack

def get_reddit_posts(subreddit, limit):
    # get the most recent 5 posts for the given subreddit
    # return the posts as a list of tuples (title, url)
    url = 'https://www.reddit.com/r/' + subreddit + '/new.json?limit=' + str(limit)
    response = requests.get(url, headers = {'User-agent': 'my bot'})
    if response.status_code == 200:
        #print(response.text)
        data = json.loads(response.text)
        posts = []
        for child in data['data']['children']:
            posts.append((child['data']['title'], child['data']['url']))
        return posts
    else:
        return 'Error code: ' + str(response.status_code)


def job_reddit(client, channel_id, subreddit, limit, is_request):
    posts = get_reddit_posts(subreddit, limit)
    now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    # if is_request is True and posts, send the posts to Slack
    message = now + ':\n'

    # if post contrain "Error code", send the error message to Slack
    if 'Error code' in posts:
        message += posts
        send_to_slack(client, channel_id, message)
        return


    if is_request:
        for post in posts:
            message += post[0] + ':\n' + post[1] + '\n'
        send_to_slack(client, channel_id, message)
        return
    
    # if request is successful
    # the previous two conditions are not met
    # this condition should be met
    if posts:
        # check if a folder named 'reddit_data' exists
        # if not, create the folder
        if not os.path.exists('reddit_data'):
            os.makedirs('reddit_data')

        # read the old posts from the file
        # the file is from the reddit_data folder
        
        # if the file does not exist
        if not os.path.exists('reddit_data/' + subreddit + '.txt'):
            # create the file
            with open('reddit_data/' + subreddit + '.txt', 'w') as f:
                pass
        # read the file
        with open('reddit_data/' + subreddit + '.txt', 'r') as f:
            old_posts = f.read()


        # compare the new posts with the old posts
        new_posts = ''
        for post in posts:
            if post[0] + '\n' not in old_posts:
                new_posts += post[0] + ':' + post[1] + '\n'
        
        # if there is a new post, send the new post to Slack
        # format: <current time> <new post>
        if new_posts:
            message += new_posts
            send_to_slack(client, channel_id, message)
        
        # overwrite the old posts with the posts from the current request
        with open('reddit_data/' + subreddit + '.txt', 'w') as f:
            for post in posts:
                f.write(post[0] + '\n')

