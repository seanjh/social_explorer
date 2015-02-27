import os
import json
from urlparse import urlparse, parse_qs, urlunparse
from random import randrange

import usaddress
from numpy import array
from geopy import Point, GoogleV3, exc

from dbscan import dbscan_cluster

# TODO: CITATION http://stackoverflow.com/a/7783326/825103
ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_PATH, 'data')

if not os.path.exists(DATA_DIR):
    os.mkdir(DATA_DIR)


class MissingTokenException(Exception):
    pass


class InvalidUserException(Exception):
    pass


class MalformedSocialExplorerException(Exception):
    pass


class Location(object):
    def __init__(self, latitude, longitude, label=None):
        self.latitude = latitude
        self.longitude = longitude
        self.label = label

    def to_JSON(self):
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "label": self.label if self.label else None
        }


class SocialData(object):
    def __init__(self, url=None, id=None, media=None, body=None, location=None):
        self.url = url
        self.id = id
        self.media = media
        self.body = body
        self.location = location

    def to_JSON(self):
        json = {
            "url": self.url if self.url else None,
            "id": self.id if self.id else None,
            "body": self.body.text if self.body and self.body.text else None,
            # "media": self.media if self.media else None,
            "location": self.location.to_JSON() if self.location else None
        }
        if self.media:
            media_json = {}
            for key, val in self.media.iteritems():
                media_json[key] = {}
                if val.height and val.width:
                    media_json[key]['height'] = val.height
                    media_json[key]['width'] = val.width
                if val.url:
                    media_json[key]['url'] = val.url
            json['media'] = media_json

        return json
        # return {
        #     "url": self.url if self.url else None,
        #     "id": self.id if self.id else None,
        #     "body": self.body.text if self.body and self.body.text else None,
        #     "media": self.media if self.media else None,
        #     "location": self.location.to_JSON() if self.location else None
        # }


class SocialExplorer(object):
    ROWS_INDEX = 0
    LAT_INDEX = 0
    LONG_INDEX = 0
    LABEL_INDEX = 0

    def __init__(self, access_token, username, debug=False):
        self._username = username
        self.user_id = None
        if not access_token:
            raise MissingTokenException()
        else:
            self._token = access_token
        self._api = None
        self._data = None
        self._debug = debug
        self._locations_array = None
        self._label_meta = None
        self._num_clusters = 0

    @property
    def api(self):
        return self._api

    @property
    def username(self):
        return self._username

    @property
    def locations(self):
        if self._data and self._locations_array is None:
            self._locations_array = array([(post.location.latitude, post.location.longitude) for post in self._data])
        return self._locations_array

    # @property
    # def location_labels(self):
    #     raise NotImplementedError()

    @property
    def data(self):
        return self._data

    @property
    def cluster_count(self):
        raise NotImplementedError()

    @property
    def label_meta(self):
        if not self._label_meta:
            self._collect_label_meta()
        return self._label_meta

    # def _is_standardized(self):
    #     try:
    #         assert self.username
    #         assert self.data
    #         assert self.locations
    #         # assert self.location_labels
    #     except:
    #         raise AssertionError()

    def to_JSON(self):
        return {
            "username": self.username if self.username else None,
            "user_id": self.user_id if self.user_id else None,
            "labels": self.label_meta.items() if self.label_meta else None,
            "data": [d.to_JSON() for d in self.data]
        }

    @staticmethod
    def _reverse_geocode(geocoder, tag_name, lat, long):
        point = Point(lat, long)
        try:
            point_location = geocoder.reverse(point, exactly_one=True)
            if point_location and point_location.address:
                raw_parse = usaddress.parse(point_location.address)
                parsed = InstagramExplorer._process_usaddress_parsed(raw_parse, [tag_name])
                return parsed.get('PlaceName') if parsed.get('PlaceName') else None
        except exc.GeocoderQuotaExceeded as e:
            print e
            return
        except Exception as e:
            print e
            return

    @staticmethod
    def _process_usaddress_parsed(addr_list, tag_names):
        val_index = 0
        tag_index = 1

        result = {}

        for elem in addr_list:
            if elem[tag_index] in tag_names:
                result.setdefault(elem[tag_index], list()).append(elem[val_index])

        for tag in tag_names:
            if result.get(tag):
                result[tag] = ' '.join(result[tag]).replace(',', '')

        return result

    def _collect_label_meta(self):
        if (self._data and
                not (self.locations is None) and
                os.getenv('GOOGLE') and
                not self._label_meta):
            # Group locations into lists by label
            labels = {}
            for i, val in enumerate(self._data):
                if val.location.label == -1:
                    continue
                labels.setdefault(int(val.location.label), list()).append(val.location)

            # Randomly select 1-5 locations / label
            sample_labels = {}
            for key in labels.iterkeys():
                limit = min(5, len(labels[key]))
                indices = [randrange(0, len(labels[key])) for i in range(limit)]
                sample_labels[key] = [labels[key][j] for j in indices]

            # Get City/Place names for each label's locations
            geocoder = GoogleV3(api_key=os.getenv('GOOGLE'))
            name_lists = {}
            # i = 0
            for key in sample_labels.iterkeys():
                for location in sample_labels[key]:
                    # i += 1
                    # print '%d: Requesting reverse geocoding for %s, %s' % (i, location.latitude, location.longitude)
                    name_lists.setdefault(key, list()).append(
                        SocialExplorer._reverse_geocode(
                            geocoder,
                            'PlaceName',
                            location.latitude,
                            location.longitude
                        )
                    )

            # Associate the label with the most common name
            label_names = {}
            for key in labels.iterkeys():
                place_counts = {}
                max_count = 0
                max_name = None
                for name in name_lists[key]:
                    place_counts[name] = place_counts.setdefault(name, 0) + 1
                    if place_counts[name] > max_count:
                        max_count = place_counts[name]
                        max_name = name
                label_names[key] = max_name

            self._label_meta = {}
            for key, val in label_names.iteritems():
                self._label_meta[key] = {
                    "name": val,
                    "count": len(labels[key])
                }
        else:
            print 'Cannot get label names'

    # def _serialize_data(self):
    #     # rows = self.locations.shape[SocialExplorer.ROWS_INDEX]
    #     # assert (self.locations.shape[SocialExplorer.ROWS_INDEX] ==
    #     #         self.location_labels.shape[SocialExplorer.ROWS_INDEX])
    #     return [{
    #         'body': self.posts[i].get('body'),
    #         'url': self.posts[i].get('url'),
    #         'media': self.posts[i].get('media'),
    #         'latitude': self.locations[i].get('latitude'),
    #         'longitude': self.locations[i].get('longitude'),
    #         'label': self.location_labels[i].get('label')
    #     } for i in range(rows)]

    def save_JSON(self):
        # raise NotImplementedError()
        if self._data:
            # self._is_standardized()
            filename = os.path.join(DATA_DIR, 'instagram-%s.json' % self.username)
            try:
                # json_data = json.dumps(self, indent=2, sort_keys=True)
                with open(filename, 'w') as outfile:
                    print 'Outputting location data to %s' % filename
                    json.dump(self.to_JSON(), outfile, indent=2, sort_keys=True)
            except AssertionError as e:
                print 'Error processing location data'
        else:
            raise NotImplementedError()

    def __repr__(self):
        return "%s(username=%s)" % (self.__class__.__name__, self._username)


from instagram.client import InstagramAPI


class InstagramExplorer(SocialExplorer):
    def __init__(self, token_env_var, username, debug=False):
        super(InstagramExplorer, self).__init__(token_env_var, username, debug)
        self._api = InstagramAPI(access_token=self._token)
        self._load_data()

    def _load_data(self):
        if None:
            # TODO: load local data, if it exists
            pass
        else:
            self._load_api_data()

    def _load_api_data(self):
        user = self._match_username()
        self.user_id = user.id

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

    def _standardize_data(self, response_data):
        self._data = [
            SocialData(
                media.link,
                media.id,
                media.images if media.type == 'image' else media.videos,
                media.caption,
                Location(media.location.point.latitude, media.location.point.longitude)
            )
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


if __name__ == '__main__':
    token = os.getenv('INSTAGRAM_TOKEN')
    explorer = InstagramExplorer(token, 'seannnnnnnnnnnn', debug=True)
    explorer.save_JSON()