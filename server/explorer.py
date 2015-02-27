import os
from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_oauth import OAuth, OAuthException
from instagram.client import InstagramAPI

app = Flask(__name__)

# Load default config
app.config.update(dict(
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))

oauth = OAuth()

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
    raise OAuthException("WTF")

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

    else:
        flash(u'Missing Instagram code.')

    # redirect back to main page
    return redirect('/')


@app.route('/')
def index():
    return render_template('index.html')