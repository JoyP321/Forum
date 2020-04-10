from flask import Flask, redirect, url_for, session, request, jsonify, Markup
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
db = client[db_name]

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
    
@app.route('/',methods=['GET','POST'])
def home():
    return render_template('home.html', threads = get_threads())

@app.route('/threadAdded', methods=['GET','POST'])
def threadAdded():
    db.createCollection('hellllo')#request.form['newThread']) 
    return render_template('home.html', threads = get_threads())
    
@app.route('/login')
def login():   
    return github.authorize(callback=url_for('authorized', _external=True, _scheme='https'))
    
@app.route('/logout')
def logout():
    session.clear()
    return render_template('home.html', threads = get_threads())

    
@app.route('/login/authorized')#the route should match the callback URL registered with the OAuth provider
def authorized():
    resp = github.authorized_response()
    if resp is None:
        session.clear()
        message = 'Access denied: reason=' + request.args['error'] + ' error=' + request.args['error_description'] + ' full=' + pprint.pformat(request.args)      
    else:
        try:
            session['github_token'] = (resp['access_token'], '')
            session['user_data'] = github.get('user').data
            print(session['user_data']['login'])
            if session['user_data']['public_repos'] >10:
                message = 'you were successfully logged in as ' + session['user_data']['login'] +'.'
            else:
                message = 'you are not qualified to view the very secret data, but you may log in'
        except Exception as inst:
            session.clear()
            message = "So sorry, an error has occured. You have not logged in."
    print(get_threads())
    return render_template('home.html', threads = get_threads())

@app.route('/thread',methods=['GET','POST'])
def render_thread():
    toReturn = ''
    for doc in db[request.args['threadName']].find():
        print(doc)
        for val in doc:
            if val != '_id':
                toReturn += doc[val]
    return render_template('thread.html', threadName = request.args['threadName'], posts= toReturn) 


def get_threads():
    toReturn = ''
    myList = []
    for thread in db.data.find({"type": "thread"}):
        myList.append(thread['value']) 
    
    for thread in myList:
        toReturn += Markup("<input type='radio' onclick='myFunction()' name = 'threadName' value='" + thread + "'>" + thread + "<br>")
    return toReturn
                          

@github.tokengetter #runs automatically. needed to confirm logged in
def get_github_oauth_token():
    return session['github_token']


if __name__ == '__main__':
    app.run()
