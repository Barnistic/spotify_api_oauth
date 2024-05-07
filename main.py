import urllib.parse
import requests
from datetime import datetime
from flask import Flask, redirect, request, jsonify, session, url_for, render_template
import json

app = Flask(__name__)   
app.secret_key = 'a27b89cc9ecc476ba75a6d939f0f115c'

CLIENT_ID = 'ac741c3507aa4edc81755b589eef91e4'
CLIENT_SECRET = 'a27b89cc9ecc476ba75a6d939f0f115c'
REDIRECT_URI = 'http://localhost:5000/callback'

AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'


@app.route('/')
def index():
    return "Welcome to my Spotify app <a href='/login'>Login with Spotify</a>"

@app.route('/login')
def login():
    scope = 'user-read-private user-read-email user-top-read'

    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri': REDIRECT_URI,
        'show_dialog': True
    }

    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    return redirect(auth_url)

@app.route('/callback')
def callback():
    if 'error' in request.args:
        return jsonify({'error': request.args['error']})
    
    if 'code' in request.args:
        req_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)
        token_info = response.json()

        session['access_token'] = token_info['access_token']
        session['refresh_token'] = token_info['refresh_token']
        session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']

        return redirect('/main')
    

@app.route('/main')
def main():
    return render_template('index.html')
    

@app.route('/playlists')
def get_playlists():
    if 'access_token' not in session:
        return redirect('/login')
    
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')
    
    headers = {
        'Authorization': f"Bearer {session['access_token']}",
    }

    response = requests.get(API_BASE_URL + 'me/playlists', headers=headers)

    playlist = response.json()

    return jsonify(playlist)

@app.route('/top_items', methods=["GET", "POST"])
def top_items():
    if 'access_token' not in session:
        return redirect('/login')
    
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')
    
    headers = {
        'Authorization': f"Bearer {session['access_token']}",
    }

    if request.method == "POST":
            type = request.form.get("type")
            time_range = request.form.get("time_range")
            response = requests.get(API_BASE_URL + f'me/top/{type}?time_range={time_range}', headers=headers)
            top_artists = response.json()

            return jsonify(top_artists)

    

    

@app.route('/refresh-token')
def refresh_token():
    if 'refresh-token' not in session:
        return redirect('/login')
    
    if datetime.now().timestamp() > session['expires_at']:
        req_body = {
            'grant-type': 'refresh_token',
            'refresh_token': session['refresh_token'],
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET   
        }

        response = requests.post(TOKEN_URL, data = req_body)
        new_token_info = response.json()

        session['access_token'] = new_token_info['access_token']
        session['expires_at'] = datetime.now().timestamp() + new_token_info['expries_in']

        return redirect('/top_artists')
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
