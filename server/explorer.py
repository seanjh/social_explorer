import os
import logging
import sys
from logging import Formatter

from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
from flask_oauth import OAuth, OAuthException
from flask_bootstrap import Bootstrap
from instagram.client import InstagramAPI

from cluster.instagram_locations import InstagramExplorer
from cluster.twitter_locations import TwitterExplorer

app = Flask(__name__)

# Load default config
app.config.update(dict(
    SECRET_KEY=os.getenv('FLASK_SECRET_KEY'),
    USERNAME=os.getenv('FLASK_USERNAME'),
    PASSWORD=os.getenv('FLASK_PASSWORD')
))

Bootstrap(app)
oauth = OAuth()


def log_to_stderr(app):
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(Formatter(
    '%(asctime)s %(levelname)s: %(message)s '
    '[in %(pathname)s:%(lineno)d]'
    ))
    handler.setLevel(logging.WARNING)
    app.logger.addHandler(handler)

log_to_stderr(app)

if not os.getenv('FLASK_SECRET_KEY'):
    raise Exception("Missing FLASK_SECRET_KEY env variable")
if not os.getenv('FLASK_PASSWORD'):
    raise Exception("Missing FLASK_PASSWORD env variable")
if not os.getenv('FLASK_USERNAME'):
    raise Exception("Missing FLASK_USERNAME env variable")


twitter_consumer_key = os.getenv('TWITTER_CONSUMER_KEY')
twitter_consumer_secret = os.getenv('TWITTER_CONSUMER_SECRET')

if not twitter_consumer_key or not twitter_consumer_secret:
    raise OAuthException("Invalid TWITTER_CONSUMER_KEY and TWITTER_CONSUMER_SECRET env variables")

twitter = oauth.remote_app(
    'twitter',
    base_url='https://api.twitter.com/1/',
    request_token_url='https://api.twitter.com/oauth/request_token',
    access_token_url='https://api.twitter.com/oauth/access_token',
    authorize_url='https://api.twitter.com/oauth/authenticate',
    consumer_key=twitter_consumer_key,
    consumer_secret=twitter_consumer_secret
)


@twitter.tokengetter
def get_twitter_token(token=None):
    return session.get('twitter_token')


@app.route('/clear')
def clear():
    session.clear()
    return redirect(url_for('index'))


@app.route('/authorize-twitter')
def authorize_twitter():
    return twitter.authorize(
        callback=url_for(
            'oauth_authorized_twitter',
            next=request.args.get('next') or request.referrer or None
        )
    )


@app.route('/oauth-authorized-twitter')
@twitter.authorized_handler
def oauth_authorized_twitter(resp):
    next_url = request.args.get('next') or url_for('index')
    if resp is None:
        flash(u'You denied the request to sign in.')
        return redirect(next_url)

    session['twitter_token'] = (
        resp['oauth_token'],
        resp['oauth_token_secret']
    )
    print "Twitter oauth_token is %s " % session['twitter_token'][0]
    print "Twitter oauth_token_secret is %s " % session['twitter_token'][1]
    session['twitter_user'] = resp['screen_name']

    flash('Successfully authorized with Twitter as %s' % session['twitter_user'])
    return redirect(next_url)


instagram_consumer_key = os.getenv('INSTAGRAM_CONSUMER_KEY')
instagram_consumer_secret = os.getenv('INSTAGRAM_CONSUMER_SECRET')
if not instagram_consumer_key or not instagram_consumer_secret:
    raise OAuthException("Invalid INSTAGRAM_CONSUMER_KEY and INSTAGRAM_CONSUMER_SECRET env variables")

# redirect_uri should point to url_for('oauth_authorized_instagram') on the server
if os.getenv('FLASK_ENV', None) != 'PRODUCTION':
    instagram_redirect = 'http://127.0.0.1:5000/oauth-authorized-instagram'
elif not os.getenv('INSTAGRAM_REDIRECT_URI'):
    raise OAuthException("Invalid INSTAGRAM_REDIRECT_URI env variable")
else:
    instagram_redirect = os.getenv('INSTAGRAM_REDIRECT_URI')

instagram = InstagramAPI(
    client_id=instagram_consumer_key,
    client_secret=instagram_consumer_secret,
    redirect_uri=instagram_redirect
)


# TODO: CITATION https://github.com/johnschimmel/Instagram---Python-Flask-example
@app.route('/authorize-instagram')
def authorize_instagram():
    return redirect(instagram.get_authorize_url())


@app.route('/oauth-authorized-instagram')
def oauth_authorized_instagram():
    code = request.args.get('code')
    if code:
        access_token, user = instagram.exchange_code_for_access_token(code)
        if not access_token:
            flash(u'Could not acquire access token.')
            return redirect(url_for('/'))

        session['instagram_token'] = access_token
        session['instagram_user'] = user
        print 'Instagram token is %s' % session['instagram_token']

    else:
        flash(u'Missing Instagram code.')

    # redirect back to main page
    return redirect('/')


@app.route('/instagram')
def instagram_explore():
    # if not session.get('instagram_data'):
    instagram_token = session['instagram_token']
    instagram_user = session['instagram_user'].get('username')
    print 'InstagramExplorer for user %s with token %s' % (
        instagram_user, instagram_token
    )
    instagram_explorer = InstagramExplorer(instagram_token, instagram_user)

    # session['instagram_data'] = instagram_explorer.json
    return jsonify(instagram_explorer.json)

    # print 'Responding with %s' % session['instagram_data']
    # return jsonify(session['instagram_data'])

@app.route('/twitter')
def twitter_explore():
    # if not session.get('twitter_data'):
    #     session['twitter_data'] = {}
    # Get data from request
    latitude = request.args.get('latitude', None)
    longitude = request.args.get('longitude', None)
    radius = request.args.get('radius', 1)
    label = request.args.get('label', 99)

    # if not session['twitter_data'].get('label'):
    twitter_token = session['twitter_token'][0]
    twitter_token_secret = session['twitter_token'][1]
    twitter_username = session['twitter_user']

    print ('TwitterExplorer for user %s with token %s, '
           'lat=%s lon=%s radius=%dmi') % (
        twitter_username, twitter_token, latitude, longitude, radius
    )

    if latitude is None:
        return jsonify({"error": "Bad request. Missing latitude"}), 400
    if longitude is None:
        return jsonify({"error": "Bad request. Missing longitude"}), 400
    else:
        twitter_explorer = TwitterExplorer(
            twitter_token, twitter_token_secret, twitter_username
            )
        twitter_explorer.search_tweets(latitude, longitude, radius, label)

        # session['twitter_data'][label] = twitter_explorer.json

        return jsonify(twitter_explorer.json)

    # print 'Responding with %s' % session['twitter_data'][label]
    # return jsonify(session['twitter_data'][label]), 200

@app.route('/explore')
def explore():
    return render_template('explore.html')


@app.route('/')
def index():
    return render_template('index.html')
