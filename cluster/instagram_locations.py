from urlparse import urlparse, parse_qs, urlunparse

from instagram.client import InstagramAPI

from social_locations import (
    SocialExplorer, SocialData, Location, Media, InvalidUserException, MalformedSocialExplorerException
)
from dbscan import dbscan_cluster


class InstagramExplorer(SocialExplorer):
    def __init__(self, access_token, username, debug=False):
        super(InstagramExplorer, self).__init__(access_token, None, username, debug)
        self._api = InstagramAPI(access_token=self._token)
        self._load_data()

    def _load_data(self):
        if None:
            # TODO: load local data, if it exists
            raise NotImplementedError("TODO: load local data, if it exists")
            pass
        else:
            self._load_api_data()

    def _load_api_data(self):
        user = self._match_username()
        self.user_id = int(user.id)

        if user:
            print 'Matched Instagram username %s to user id %s' % (self.username, user.id) if self._debug else None
            posts = self._load_content(user.id)
            self._standardize_data(posts)

            labels, core_samples_mask, clusters, X = dbscan_cluster(self.locations)
            self._add_labels(labels)
            self._collect_label_meta()
            print 'Location Clusters: %s' % self._label_meta if self._label_meta else None
        else:
            raise InvalidUserException()

    def _match_username(self):
        users = self._api.user_search(self._username)
        match = [user for user in users if user.username == self._username]
        return match[0] if match else None

    def _load_content(self, user_id):
        post_results = []
        visited = {}
        posts, next_ = self._api.user_recent_media(user_id=user_id)
        post_results.extend(posts)
        next_url, max_id = self._next_url(next_, posts)

        while not visited.get(max_id):
            posts, next_ = self._api.user_recent_media(user_id=user_id, max_id=max_id)
            visited[max_id] = True
            post_results.extend(posts)
            next_url, max_id = self._next_url(next_, posts)

        return post_results


    @staticmethod
    def _process_instagram_datum(datum):
        url = datum.link
        id = datum.id
        text = datum.caption.text if datum.caption is not None else None
        location = Location(datum.location.point.latitude, datum.location.point.longitude)
        media_data = datum.images if datum.type == 'image' else datum.videos
        media = {key: Media(url=val.url, height=val.height, width=val.width)
                 for (key, val) in media_data.iteritems()}
        username = datum.user.username
        user_id = datum.user.id

        return SocialData(url, id, media, text, username, user_id, location)

    def _standardize_data(self, response_data):
        # Filter or limit results to location-tagged updates
        self._data = [
            InstagramExplorer._process_instagram_datum(media)
            for media in response_data
            if hasattr(media, 'location') and
            hasattr(media.location, 'point') and
            hasattr(media.location.point, 'latitude') and
            hasattr(media.location.point, 'longitude')
        ]

    def _add_labels(self, labels):
        if len(labels) != len(self._data):
            raise MalformedSocialExplorerException("The number of labels must match the number of posts")
        for i in range(len(labels)):
            self._data[i].location.label = labels[i]

    @staticmethod
    def _next_url(url, media_list):
        if media_list and url:
            max_media_id = media_list[-1].id
            parsed = urlparse(url)
            query = parse_qs(parsed.query)
            query_str = "access_token=%s&max_id=%s" % (query.get('access_token')[-1], max_media_id)
            new_url = urlunparse([parsed.scheme, parsed.netloc, parsed.path, '', query_str, None])
            return new_url, max_media_id
        else:
            return None, None