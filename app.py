import flask
from flask import Flask, render_template, request
from flask_pymongo import PyMongo
import requests


app = Flask(__name__)
app.debug = True
app.secret_key = 'ThisSux'
app.config["MONGO_DBNAME"] = "MBTAData"
app.config["MONGO_URI"] = "mongodb://localhost/27017"

mongo = PyMongo(app)
#oauth = OAuth.app

@app.route('/temperature', methods=['POST'])
def temperature():
    zipcode = request.form['zip']
    r = requests.get('http://api.openweathermap.org/data/2.5/weather?zip='+zipcode+',us&appid=b0e0bbe93793b39e76cc1b1a65e32369')
    json_object = r.json()
    temp_k = float(json_object['main']['temp'])
    temp_f = round(((temp_k - 273.15) * 1.8 + 32),1)
    #condition = (json_object(['weather']))
    temp_highk = float(json_object['main']['temp_max'])
    temp_highf = round(((temp_highk - 273.15) * 1.8 + 32),1)
    temp_lowk = float(json_object['main']['temp_min'])
    temp_lowf = round(((temp_lowk - 273.15) * 1.8 + 32),1)
    humid = float(json_object['main']['humidity'])
    weather = (json_object['weather'][0]['description'])
    location = (json_object['name'])
    return render_template('temperature.html', temp=temp_f, humidity=humid,name=location, high=temp_highf, low=temp_lowf,description=weather)

@app.route('/register', methods=['POST', 'GET'])
def register_user():
    try:
        email=request.form.get('email')
        password=request.form.get('password')
        firstname=request.form.get('fname')
        lastname=request.form.get('lname')
    except:
        print ("couldn't find all tokens")
        #this prints to shell, end users will not see this (all print statements go to shell)
        return flask.redirect(flask.url_for('register'))

    cursor = conn.cursor()
    test =  isEmailUnique(email)
    if test:
        print (cursor.execute("INSERT INTO Users (email, password, firstname, lastname) VALUES ('{0}', '{1}', '{2}', '{3}',)".format(email, password, firstname, lastname)))
        conn.commit()
        #log user in
        user = User()
        user.id = email
        flask_login.login_user(user)
        return render_template('index.html')
    else:
        print ("couldn't find all tokens")
        return flask.redirect(flask.url_for('register'))

from flask.ext.cache import Cache
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@cache.cached(timeout=50, key_prefix='api_call')
def call_routes():
    r = requests.get('https://api-v3.mbta.com/stops')
    stops = r.json()['data']
    for i in stops:
        data = i['attributes']

@app.route('/')
def index():
	return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
