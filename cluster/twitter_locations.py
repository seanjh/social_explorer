import os

import tweepy

from social_locations import (
    SocialExplorer, SocialData, Location, Media, InvalidUserException, MissingTokenException
)


class TwitterExplorer(SocialExplorer):
    PAGE_LIMIT = 1
    COUNT_PER_PAGE = 100
    QUERY = "*"
    RESULT_TYPE = 'recent'  # recent, mixed, popular

    def __init__(self, access_token, access_secret, username, debug=False):
        super(TwitterExplorer, self).__init__(access_token, access_secret, username, debug)
        consumer_key = os.getenv('TWITTER_CONSUMER_KEY')
        consumer_secret = os.getenv('TWITTER_CONSUMER_SECRET')
        if not access_secret:
            raise MissingTokenException("Token secret must be provided")
        if not consumer_key:
            raise MissingTokenException("Missing TWITTER_CONSUMER_KEY env variable")
        if not consumer_key:
            raise MissingTokenException("Missing TWITTER_CONSUMER_SECRET env variable")
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_secret)
        self._api = tweepy.API(auth)
        self._label_meta = {}

        user = self._api.get_user(screen_name=username)
        if user:
            self.user_id = user.id
        else:
            raise InvalidUserException("User %s could not be identified by Twitter" % username)

    def search_tweets(self, latitude, longitude, radius_miles, location_label):
        tweets = self._load_content(latitude, longitude, radius_miles, location_label)
        self._standardize_data(tweets, location_label)
        self._collect_population_meta(tweets, location_label)

    def _check_rate_limit(self):
        rate_limit_status = self._api.rate_limit_status()
        searches = rate_limit_status.get('resources').get('search').get('/search/tweets')
        pct_remaining = float(searches.get('remaining')) / searches.get('limit')
        print "%d/%d remaining requests" % (searches.get('remaining'), searches.get('limit')) if self._debug else None
        if pct_remaining < 0.05:
            raise RateLimitException(
                "%d of %d requests remaining for Twitter endppoint /search/tweets" %
                (searches.get('remaining'), searches.get('limit'))
            )

    def _load_content(self, latitude, longitude, radius_miles, location_label):
        self._check_rate_limit()

        geocode_str = "%0.6f,%0.6f,%smi" % (latitude, longitude, radius_miles)
        return [datum for datum in
                tweepy.Cursor(
                    self._api.search,
                    q=TwitterExplorer.QUERY,
                    geocode=geocode_str,
                    count=TwitterExplorer.COUNT_PER_PAGE,
                    result_type=TwitterExplorer.RESULT_TYPE
                ).items(TwitterExplorer.PAGE_LIMIT * TwitterExplorer.COUNT_PER_PAGE)
                ]

    @staticmethod
    def _make_tweet_url(username, status_id):
        # e.g., https://twitter.com/nevesytrof/status/530385710180597760
        return "https://twitter.com/%s/status/%s" % (username, status_id)

    @staticmethod
    def _get_media_entity(entities):
        # Just get the last image (ignore the rest, just cuz)
        if entities.get('media'):
            image = entities.get('media').pop()
            return {
                key: Media(url=image.get('display_url'), height=val.get('h'), width=val.get('w'))
                for (key, val) in image.get('sizes').iteritems()
            }
        else:
            return None

    @staticmethod
    def _process_tweet(tweet, location_label):
        # Syntax via https://dev.twitter.com/overview/api/tweets
        id = tweet.id
        username = tweet.user.screen_name
        user_id = tweet.user.id
        url = TwitterExplorer._make_tweet_url(username, id)
        text = tweet.text
        media = TwitterExplorer._get_media_entity(tweet.entities) if tweet.entities else None
        # In GeoJSON format http://geojson.org
        location = Location(
            tweet.coordinates.get('coordinates')[0],
            tweet.coordinates.get('coordinates')[1],
            label=location_label
        ) if (
            hasattr(tweet, 'coordinates') and tweet.coordinates and tweet.coordinates.get('coordinates')
        ) else None
        return SocialData(url, id, media, text, username, user_id, location)

    def _standardize_data(self, tweets, location_label):
        self._data = [
            TwitterExplorer._process_tweet(tweet, location_label) for tweet in tweets
        ]

    def _set_population(self, tweets, label):
        friends_count_total = 0
        for tweet in tweets:
            friends_count_total += tweet.user.friends_count

        print 'Population of label %d is %d' % (label, friends_count_total)
        self.label_meta[label]['population'] = friends_count_total

    def _set_president(self, tweets, label):
        # Make the president the user with the largest number of followers
        first_tweet = tweets.pop()
        president = first_tweet.user
        for tweet in tweets:
            user = tweet.user
            if user.followers_count > president.followers_count:
                president = user

        tweets.append(first_tweet)

        print 'President of label %d is %s with %d total followers' % (
            label, president.screen_name, president.followers_count
        )
        self.label_meta[label]['president'] = president._json

    def _collect_population_meta(self, tweets, label):
        self.label_meta.setdefault(label, dict())
        self._set_population(tweets, label)
        self._set_president(tweets, label)


class RateLimitException(BaseException):
    pass