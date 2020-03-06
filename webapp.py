from flask import Flask, redirect, url_for, session, request, jsonify
from flask_oauthlib.client import OAuth
from flask import render_template
import pymongo
import os
import sys
import pprint


app = Flask(__name__)

app.debug = True 

connection_string = os.environ["MONGO_CONNECTION_STRING"]
db_name = os.environ["MONGO_DBNAME"]
client = pymongo.MongoClient(connection_string)
db = client['testdb']
collection = db['testData']

app.secret_key = os.environ['SECRET_KEY'] 
oauth = OAuth(app)

github = oauth.remote_app(
    'github',
    consumer_key=os.environ['GITHUB_CLIENT_ID'], 
    consumer_secret=os.environ['GITHUB_CLIENT_SECRET'],
    request_token_params={'scope': 'user:email'}, #request read-only access to the user's email.  For a list of possible scopes, see developer.github.com/apps/building-oauth-apps/scopes-for-oauth-apps
    base_url='https://api.github.com/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://github.com/login/oauth/access_token',  
    authorize_url='https://github.com/login/oauth/authorize' #URL for github's OAuth login
)


@app.context_processor #sets logged_in variable for every page here instead of in render template
def inject_logged_in():
    return {"logged_in":('github_token' in session)}
    
@app.route('/')
def home():
    return render_template('home.html')
    
    
@app.route('/login')
def login():   
    return github.authorize(callback=url_for('authorized', _external=True, _scheme='https'))
    
@app.route('/logout')
def logout():
    session.clear()
    return render_template('home.html', message='You were logged out')

@github.tokengetter #runs automatically. needed to confirm logged in
def get_github_oauth_token():
    return session['github_token']


if __name__ == '__main__':
    app.run()
