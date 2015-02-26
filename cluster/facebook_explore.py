import facebook

try:
    from secrets import FACEBOOK
except ImportError as e:
    print e
    exit(1)


def get_me_feed(graph):
    return graph.get_connections(id="me", connection_name="feed")


def get_graph(access_token):
    return facebook.GraphAPI(access_token=access_token)