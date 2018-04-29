import flask
from flask import Flask, render_template
from flask_pymongo import PyMongo
from flask_googlemaps import GoogleMaps
from flask_googlemaps import Map, icons
import requests
import flask_cache


app = Flask(__name__)
app.debug = True
app.secret_key = 'ThisSux'
app.config["MONGO_DBNAME"] = "MBTAData"
app.config["MONGO_URI"] = "mongodb://localhost/27017"
app.config["GOOGLE_MAPS_API_KEY"] = "AIzaSyCIwN3YqgnC36MtRsx5-RhZhoBSKeUn0gY"

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
def register():
    return render_template('register.html')

from flask_cache import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})


@cache.cached(timeout=50, key_prefix='api_call')
def call_routes():
    r = requests.get('https://api-v3.mbta.com/stops')
    stops = r.json()['data']
    i = 0
    stops_db = mongo.db.stops
    for stop in stops:
        i += 1
        stops_db.insert({"name": stop["attributes"]["name"], "id": stop["id"]})


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')


@app.route("/time", methods=["GET", "POST"])
def time():
    if request.method == "POST":
        stop_name = request.form["stop_name"]
        stops = mongo.db.stops
        stop_id = stops.find_one({"name": stop_name})
        if stop_id is not None:
            r = requests.get("https://api-v3.mbta.com//predictions?filter[stop]=" + stop_id["id"])
            arrival_times = r.json()
            n = 0
            arr_times = []
            for time in arrival_times["data"]:
                exact_time = time["attributes"]["arrival_time"]
                if exact_time is not None:
                    exact_time = str(exact_time)
                    print(exact_time[11:19])
                    n += 1
                    arr_times.append(exact_time[11:19])
                if n == 2:
                    break
        else:
            arr_times = ["-", "-"]
    return render_template("time.html", arrival_times=arr_times)

@app.route("/enter_zip")
def enter_zip():
    return render_template("enter_zip.html")

@app.route("/weather")
def weather():
    return render_template("weather.html")

@app.route('/test_coordinates', methods=["POST", "GET"])
def coords():
    return render_template('test_coordinates.html')


if __name__ == '__main__':
    app.run(debug=True)
