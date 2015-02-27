import os
# from instagram import client
from requests import Session, Request, Response
#
# INSTAGRAM_CONFIG = {
#     'client_id': os.getenv('INSTAGRAM-CLIENT-ID'),
#     'client_secret': os.getenv('INSTAGRAM-CLIENT-SECRET'),
#     'redirect_uri': os.getenv('INSTAGRAM-REDIRECT')
# }
#
# unauthenticated_api = client.InstagramAPI(**INSTAGRAM_CONFIG)
#
# # url = unauthenticated_api.get_authorize_url()
# url = unauthenticated_api.get_authorize_login_url()
#
# print url
#
# # s = Session()
# # req1 = Request('GET', url)
# # prepped = req1.prepare()
# # resp1 = s.send(prepped)
# # print resp1.url
# #
# # req2 = Request('GET', resp1.url)
# # prepped = req2.prepare()
# # resp2 = s.send(prepped)
# # print resp1.url
#
# print


url = 'https://api.twitter.com/oauth/authorize?oauth_consumer_key=%s&' % (
    os.getenv('TWITTER-CONSUMER-KEY')
    # oauth_consumer_key
    # oauth_signature_method
    # oauth_signature
    # oauth_timestamp
    # oauth_nonce
    # oauth_callback
)
print url

s = Session()
req = Request('GET', url)
prepped = req.prepare()
resp = s.send(prepped)

print