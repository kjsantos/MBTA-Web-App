from flask import Flask, render_template, request
from flask_oauthlib.client import OAuth
from flask_pymongo import PyMongo
import requests


app = Flask(__name__)
app.debug = True
app.secret_key = 'ThisSux'
app.config["MONGO_DBNAME"] = "MBTAData"
app.config["MONGO_URI"] = "mongodb://localhost/27017"

mongo = PyMongo(app)
oauth = OAuth.app

@app.route('/temperature', methods=['POST'])
def temperature():
    zipcode = request.form['zip']
    r = requests.get('http://api.openweathermap.org/data/2.5/weather?zip='+zipcode+',us&appid=b0e0bbe93793b39e76cc1b1a65e32369')
    json_object = r.json()
    temp_k = float(json_object['main']['temp'])
    temp_f = round(((temp_k - 273.15) * 1.8 + 32),1)
    #condition = (json_object(['weather']))
    humid = float(json_object['main']['humidity'])
    location = (json_object['name'])
    return render_template('temperature.html', temp=temp_f, humidity=humid,name=location)

@app.route

@app.route('/')
def index():
	return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
