import os
from flask import Flask, render_template, redirect, session, url_for, request
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler
from wordcloud import WordCloud
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

client_id = os.getenv('SPOTIFY_CLIENT_ID')
client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
redirect_uri = 'http://127.0.0.1:5000/callback'
scope = 'user-top-read'

cache_handler=FlaskSessionCacheHandler(session)
sp_oauth = SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope=scope,
    cache_handler=cache_handler,
    show_dialog=True
)

@app.route('/')
def home():
    return render_template('home.html')

#route to get user login token
@app.route('/login')
def login():
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)
    return redirect('word-cloud')

#callback to refresh user access token so user doesnt need to login in multiple times
@app.route('/callback')
def callback():
    sp_oauth.get_access_token(request.args['code'])
    return redirect(url_for('word_cloud'))

@app.route('/word-cloud')
def word_cloud():
    #get time range and type from query parameters, defaulting to 'medium_term' and 'tracks'
    time_range = request.args.get('time_range', 'medium_term')
    selected_type = request.args.get('type', 'tracks')

    token_info = cache_handler.get_cached_token()
    if not token_info:
        return redirect(url_for('login'))
        
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])

    sp = Spotify(auth=token_info['access_token'])

    #fetch data based on the selected type
    if selected_type == 'artists':
        results = sp.current_user_top_artists(limit=50, time_range=time_range)
        names = [artist['name'] for artist in results['items']]
    else:
        results = sp.current_user_top_tracks(limit=50, time_range=time_range)
        names = [track['name'] for track in results['items']]

    #create frequency dictionary for word cloud
    frequencies = {name: 1 for name in names}

    #generate wordcloud
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(frequencies)
    wordcloud.to_file('static/wordcloud.png')

    
    return render_template('word-cloud.html', track_image='wordcloud.png', type=selected_type, time_range=time_range)


if __name__ == '__main__':
    app.run()



