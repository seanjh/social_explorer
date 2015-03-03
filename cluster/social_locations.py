import os
import json
from random import randrange

import usaddress
from numpy import array
from geopy import Point, GoogleV3, exc

# TODO: CITATION http://stackoverflow.com/a/7783326/825103
ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_PATH, 'data')

if not os.path.exists(DATA_DIR):
    os.mkdir(DATA_DIR)


class SocialExplorer(object):
    ROWS_INDEX = 0
    LAT_INDEX = 0
    LONG_INDEX = 0
    LABEL_INDEX = 0

    def __init__(self, access_token, access_token_secret, username, debug=False):
        self._username = username
        self.user_id = None
        if not access_token:
            raise MissingTokenException()
        else:
            self._token = access_token
        self._token_secret = access_token_secret
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

    @property
    def data(self):
        return self._data

    @property
    def label_meta(self):
        return self._label_meta

    @property
    def json(self):
        return {
            "username": self.username if self.username else None,
            "user_id": self.user_id if self.user_id else None,
            "labels": self.label_meta if self.label_meta else None,
            "data": [d.json for d in self.data]
        }

    @staticmethod
    def _reverse_geocode(geocoder, tag_name, lat, long):
        point = Point(lat, long)
        try:
            point_location = geocoder.reverse(point, exactly_one=True)
            if point_location and point_location.address:
                raw_parse = usaddress.parse(point_location.address)
                parsed = SocialExplorer._process_usaddress_parsed(raw_parse, [tag_name])
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

    def save(self):
        if self._data:
            filename = os.path.join(DATA_DIR, '%s-%s.json' % (self.__class__.__name__, self.username))
            try:
                with open(filename, 'w') as outfile:
                    print 'Outputting location data to %s' % filename
                    json.dump(self.json, outfile, indent=2, sort_keys=True)
            except AssertionError as e:
                print 'Error processing location data %s' % e
        else:
            raise NotImplementedError()

    def __repr__(self):
        return "%s(username=%s)" % (self.__class__.__name__, self._username)


class MissingTokenException(Exception):
    pass


class InvalidUserException(Exception):
    pass


class MalformedSocialExplorerException(Exception):
    pass


class Media(object):
    def __init__(self, url=None, height=None, width=None):
        self.url = url
        self.height = height
        self.width = width

    @property
    def json(self):
        return {
            "url": self.url if self.url else None,
            "height": self.height if self.height else None,
            "width": self.width if self.width else None
        }


class Location(object):
    def __init__(self, latitude, longitude, label=None):
        self.latitude = latitude
        self.longitude = longitude
        self.label = label

    @property
    def json(self):
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "label": self.label if self.label is None else None
        }


class SocialData(object):
    def __init__(self, url=None, id=None, media=None, body=None, username=None, user_id=None, location=None):
        self.url = url
        self.id = id
        self.media = media
        self.body = body
        self.username = username
        self.user_id = user_id
        self.location = location

    @property
    def json(self):
        return {
            "url": self.url if self.url else None,
            "id": self.id if self.id else None,
            "body": self.body if self.body and self.body else None,
            "username": self.username if self.username else None,
            "user_id": self.user_id if self.user_id else None,
            "location": self.location.json if self.location else None,
            "media": {key: val.json for (key, val) in self.media.iteritems()} if self.media else None
        }