import os

from instagram_locations import InstagramExplorer
from twitter_locations import TwitterExplorer

INSTAGRAM = True
TWITTER = True

if __name__ == '__main__':
    if INSTAGRAM:
        instagram_user = 'seannnnnnnnnnnn'
        instagram_token = os.getenv('INSTAGRAM_TOKEN')
        instagram = InstagramExplorer(instagram_token, instagram_user, debug=True)
        instagram.save()  # saves a JSON file to disk

    if TWITTER:
        twitter_user = 'seannnnnnnnnnnn'
        twitter_token = os.getenv('TWITTER_TOKEN')
        twitter_token_secret = os.getenv('TWITTER_TOKEN_SECRET')
        # latitude = 37.383888889
        # longitude = -5.991388889
        latitude = 40.7636791
        longitude = -73.9611658
        radius = 1
        twitter = TwitterExplorer(twitter_token, twitter_token_secret, twitter_user, debug=True)
        twitter.search_tweets(latitude, longitude, radius, 99)

        twitter.save()  # saves a JSON file to disk