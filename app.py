
import flask
from flask import Flask, render_template, request, redirect, url_for
from flask_pymongo import PyMongo
import requests

global user
app = Flask(__name__)
app.debug = True
app.secret_key = 'ThisSux'
app.config["MONGO_DBNAME"] = "27107"
app.config["MONGO_URI"] = "mongodb://localhost:27017"

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
    return render_template('login.html')

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

@app.route("/logout")
def logout():
    return render_template("logout.html")


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


if __name__ == '__main__':
    app.run(debug=True)