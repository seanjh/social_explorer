from urlparse import urlparse, parse_qs, urlunparse

from instagram.client import InstagramAPI
from numpy import array

try:
    from secrets import INSTAGRAM
except ImportError as e:
    print e
    exit(1)

# from dbscan import compute_dbscan


def get_instragram_api(access_token):
    return InstagramAPI(access_token=access_token)


def instagram_next_url(url, media_feed):
    if media_feed and url:
        max_media_id = media_feed[-1].id
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        query_str = "access_token=%s&max_id=%s" % (query.get('access_token')[-1], max_media_id)
        new_url = urlunparse([parsed.scheme, parsed.netloc, parsed.path, '', query_str, None])
        return new_url, max_media_id
    else:
        return None, None


def instagram_find_user(api, username):
    return api.user_search(username)


def instagram_match_username(users, username):
    match = [user for user in users if user.username == username]
    return match[0] if match else None


def instagram_user_feed(api):
    feed_media = []
    feed, next_ = api.user_media_feed()
    feed_media.extend(feed)
    next_feed_url = instagram_next_url(next_, feed)

    while next_feed_url:
        print 'Requesting %s' % next_feed_url
        feed, next_ = api.user_media_feed(next_feed_url)
        feed_media.extend(feed)
        next_feed_url = instagram_next_url(next_, feed[-1].get('id'))


def instagram_user_uploads(api, user_id):
    post_results = []
    visited = {}
    posts, next_ = api.user_recent_media(user_id=user_id)
    post_results.extend(posts)
    next_url, max_id = instagram_next_url(next_, posts)
    # visited[max_id] = True

    while not visited.get(max_id):
        posts, next_ = api.user_recent_media(user_id=user_id, max_id=max_id)
        visited[max_id] = True
        post_results.extend(posts)
        next_url, max_id = instagram_next_url(next_, posts)

    return post_results


def instagram_print_user_search_results(users):
    for u in users:
        keys = [k for k in dir(u) if '__' not in k]
        for k in keys:
            print "%s=%s " % (k, getattr(u, k))
        print


def instagram_print_posts_results(posts):
    keys = [key for key in dir(posts[-1]) if '__' not in key]
    for post in posts:
        for k in keys:
            if getattr(post, k):
                print "%s=%s " % (k, getattr(post, k))
        print


def instagram_get_locations_array(posts):
    locations = [
        (media.location.point.latitude, media.location.point.longitude)
        for media in posts
        if hasattr(media, 'location') and
        hasattr(media.location, 'point') and
        hasattr(media.location.point, 'latitude') and
        hasattr(media.location.point, 'longitude')
    ]
    print
    return array(locations)


def instagram_user_locations(username):
    instagram_api = get_instragram_api(INSTAGRAM.get('token')[0])
    username = username
    users = instagram_find_user(instagram_api, username)
    user_match = instagram_match_username(users, username)

    if user_match:
        print 'Matched user %s to userid %s' % (username, user_match.id)
        posts = instagram_user_uploads(instagram_api, user_match.id)
        print 'User %s has %d total instagram updates' % (username, len(posts))
        # instagram_print_posts_results(posts)

        # http://datasyndrome.com/post/69514893525/yelp-dataset-challenge-part-0-geographic
        locations = instagram_get_locations_array(posts)
        print '%s has %s instagram updates with a location' % (username, locations.size)

        return user_match.id, locations


    else:
        return None, None


if __name__ == '__main__':
    instagram_user_locations('seannnnnnnnnnnn')