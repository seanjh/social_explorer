import json
import os

from dbscan import compute_dbscan, plot_dbscan
from instragram_explore import instagram_user_locations

ROWS_INDEX = 0
LAT_INDEX = 0
LONG_INDEX = 0

# CITATION http://stackoverflow.com/a/7783326/825103
ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_PATH, 'data')

if not os.path.exists(DATA_DIR):
    os.mkdir(DATA_DIR)


def make_location_dict(location, labels):
    rows = location.shape[ROWS_INDEX]
    assert location.shape[ROWS_INDEX] == labels.shape[ROWS_INDEX]
    return [{
        'latitude': location[i][LAT_INDEX],
        'longitude': location[i][LONG_INDEX],
        'label': labels[i]
    } for i in range(rows)]


def output_location_json(username, id, locations, labels):
    try:
        json_data = {
            'username': username,
            'user_id': id,
            'data': make_location_dict(locations, labels)
        }
        filename = os.path.join(DATA_DIR, 'instagram-%s-%s.json' % (username, id))
        with open(filename, 'w') as outfile:
            print 'Outputting location data to %s' % filename
            json.dump(json_data, outfile, indent=2, sort_keys=True)
    except AssertionError as e:
        print 'Error processing location data'
        pass


def main():
    username = 'seannnnnnnnnnnn'
    user_id, locations = instagram_user_locations(username)
    labels, core_samples_mask, n_clusters_, X = compute_dbscan(locations)
    output_location_json(username, user_id, locations, labels)
    print labels
    print locations

    plot_dbscan(labels, core_samples_mask, n_clusters_, X)

if __name__ == '__main__':
    main()
