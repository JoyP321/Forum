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
    if 'logged_in' not in session:
        session['logged_in']= False
    session[activeThread]= "none"
    return render_template('home.html', threads = get_threads())

@app.route('/threadAdded', methods=['GET','POST']) 
def threadAdded():
    if session['logged_in']: 
        db.data.insert_one(
            { "type": "thread", "thread": request.form['newThread']}
            
        )
        
        #potential message prompting login
        
    return render_template('home.html', threads = get_threads())

@app.route('/postAdded', methods=['GET','POST'])
def postAdded():
    number = len(db.data.find_one({"thread" : session[activeThread]})) -2
    name = "post" + str(number)
    if session['logged_in']: 
        query = {"thread": session[activeThread]} #add active thread to the session so we can access from here and render thread
        changes = {'$set': {name : request.form['newPost']}}
        data.update_one(query, changes)

        '''db.data.insert_one(
            { "type": "post", "value": request.form['newPost'], "parentThread } #working here
            
        )'''
        
        #potential message prompting login'''
        
    return render_template('/thread')
    
@app.route('/login')
def login():   
    return github.authorize(callback=url_for('authorized', _external=True, _scheme='https'))
    
@app.route('/logout')
def logout():
    session.clear()
    session['logged_in']= False
    return render_template('home.html', threads = get_threads())

    
@app.route('/login/authorized')#the route should match the callback URL registered with the OAuth provider
def authorized():
    resp = github.authorized_response()
    if resp is None:
        session.clear()
        session['logged_in'] = False     
    else:
        try:
            session['github_token'] = (resp['access_token'], '')
            session['user_data'] = github.get('user').data
            session['logged_in'] = True
        except Exception as inst:
            session.clear()
            session['logged_in'] = False
    return render_template('home.html', threads = get_threads())

@app.route('/thread',methods=['GET','POST'])
def render_thread():
    toReturn = ''
    if request.form.get('threadName') != None:
        session[activeThread] = request.args['threadName']
    doc = db.data.find_one({"thread": session[activeThread]})
    for myField in doc:
        if myField != "_id" and myField != "type" and myField != "thread":
            toReturn += Markup("<p>" + doc[myField] + "</p>")
    return render_template('thread.html', threadName = session[activeThread], posts = toReturn) 


def get_threads():
    toReturn = ''
    myList = []
    for doc in db.data.find({"type": "thread"}):
        myList.append(doc['thread']) 
    
    for thread in myList:
        toReturn += Markup("<input type='radio' onclick='myFunction()' name = 'threadName' value='" + thread + "'>" + thread + "<br>")
    return toReturn
                          

@github.tokengetter #runs automatically. needed to confirm logged in
def get_github_oauth_token():
    return session['github_token']


if __name__ == '__main__':
    app.run()
