import flask
from flask import Flask, render_template, request, redirect, url_for, session, request, jsonify
from flask_pymongo import PyMongo
from flask_googlemaps import GoogleMaps
from flask_googlemaps import Map, icons
import requests
import flask_cache
from flask_oauthlib.client import OAuth



global user

app = Flask(__name__)

app.config['GOOGLE_ID'] = "330611779338-0s48on9c1o9q4lkmqsjn3999amhig7am.apps.googleusercontent.com"
app.config['GOOGLE_SECRET'] = "tcSSLyTOKA422cXEbknlTvpr"
app.debug = True
app.secret_key = 'ThisSux'
app.config["MONGO_DBNAME"] = "27017"
app.config["MONGO_URI"] = "mongodb://localhost/27017"
app.config["GOOGLE_MAPS_API_KEY"] = "AIzaSyCIwN3YqgnC36MtRsx5-RhZhoBSKeUn0gY"


mongo = PyMongo(app)
app.secret_key = 'development'
oauth = OAuth(app)

google = oauth.remote_app(
    'google',
    consumer_key=app.config.get('GOOGLE_ID'),
    consumer_secret=app.config.get('GOOGLE_SECRET'),
    request_token_params={
        'scope': 'email'
    },
    base_url='https://www.googleapis.com/oauth2/v1/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
)

@app.route('/temperature', methods=['POST'])
def temperature():
    zipcode = request.form['zip']
    r = requests.get('http://api.openweathermap.org/data/2.5/weather?zip='+zipcode+',us&appid=b0e0bbe93793b39e76cc1b1a65e32369')
    json_object = r.json()
    temp_k = float(json_object['main']['temp'])
    temp_f = round(((temp_k - 273.15) * 1.8 + 32),1)
    temp_highk = float(json_object['main']['temp_max'])
    temp_highf = round(((temp_highk - 273.15) * 1.8 + 32),1)
    temp_lowk = float(json_object['main']['temp_min'])
    temp_lowf = round(((temp_lowk - 273.15) * 1.8 + 32),1)
    humid = float(json_object['main']['humidity'])
    weather = (json_object['weather'][0]['description'])
    location = (json_object['name'])
    return render_template('temperature.html', temp=temp_f, humidity=humid,name=location, high=temp_highf, low=temp_lowf,description=weather)


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
    stops = mongo.db.stops
    if stops.find_one() is None:
        call_routes()
    if 'google_token' in session:
        me = google.get('userinfo')
        return jsonify({"data": me.data})
    return render_template('index.html')

@app.route('/login')
def login():
    google.authorize(callback=url_for('authorized', _external=True))
    return render_template('profile.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')



@app.route("/register", methods = ["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"] #this gets the email value from the html files
        password = request.form["password"]
        fname = request.form["fname"]
        lname = request.form["lname"]
        users = mongo.db.users      #mongo.db accesess the db we're currently using
                                    #.users specifies/creates the collection we'll be writing into

        exists = users.find_one({"email": email})       #finds an entry with "email" key equal to variable email
                                                        #otherwise returns None

        if exists is not None:
            error_msg = "User email already registered"
            return redirect(url_for("reg_error", err_msg = error_msg, redirect_url ="/register"))
        else:
            users.insert({"email": email, "password": password, "fname": fname, "lname": lname})
            return redirect(url_for("home"))
    else:
        return render_template('register.html')



@app.route("/error")
def reg_error():
    red_url = request.args["redirect_url"]
    error_msg = request.args["err_msg"]
    return render_template("error.html", e_msg = error_msg, redirect_url = red_url)


@app.route("/check_login", methods=["POST"])
def check_login():
    email = request.form["email"]
    password = request.form["password"]

    users = mongo.db.users
    exists = users.find_one({"email": email, "password": password})
    if exists is None:
        error_msg = "You have entered an incorrect username/password."
        return redirect(url_for("reg_error", err_msg=error_msg,redirect_url="/" ))
    else:
        global user
        user = email
        return redirect(url_for("profile"))


@google.authorized_handler
@app.route('/login/authorized')
def authorized():
  resp = google.authorized_response()
  if resp is None:
    return 'Access denied: reason=%s error=%s' % (
      request.args['error_reason'],
      request.args['error_description']
    )
  session['google_token'] = (resp['access_token'], '')
  me = google.get('userinfo')
  jsonify({"data": me.data})
  return render_template("profile.html")
  return jsonify({"data": me.data})

@google.tokengetter
def get_google_oauth_token():
    return session.get('google_token')

@app.route('/logout')
def logout():
    session.pop('google_token', None)
    return render_template('logout.html')


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
            users = mongo.db.users
            users.update({"email":user},{"$set":{"stop": stop_name,"id": stop_id}})
        else:
            arr_times = ["-", "-"]
    return render_template("time.html", arrival_times=arr_times)

@app.route("/home")
def home():
    global user
    users = mongo.db.users
    stop = users.find_one({"email":user, "stop":{"$exists":"true"}, "id":{"$exists":"true"}})

    if stop is not None:
        return render_template("home.html",stop = stop["stop"] )
    return render_template("home.html", stop = stop)

@app.route("/weather")
def weather():
    return render_template("weather.html")

@app.route("/enter_zip")
def enter_zip():
    return render_template("enter_zip.html")


@app.route('/destination', methods=["POST", "GET"])
def coords():
    return render_template('destination.html')


if __name__ == '__main__':
    app.run(debug=True)