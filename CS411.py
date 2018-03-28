import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
from flask.ext.login import LoginManager
import flask_login
from datetime import datetime

import re, os
import os.path
from werkzeug.utils import secure_filename
import itertools


mysql = MySQL()
app = Flask(__name__)
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'Koda15'
app.config['MYSQL_DATABASE_DB'] = 'CS411'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'

mysql.init_app(app)

login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email FROM Users")
users = cursor.fetchall()

def getUserList():
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM Users")
    data = cursor.fetchall()
    return [row[0] for row in data]

class User(flask_login.UserMixin):
    pass

@login_manager.user_loader
def user_loader(email):
    users = getUserList()
    if not (email) or email not in users:
        return
    user = User()
    user.id = email
    cursor = mysql.connect().cursor()
    cursor.execute("SELECT id, email, fname, lname FROM Users WHERE email = '{0}'".format(email))
    data = cursor.fetchall()
    user.account = {"id": data[0][0], "email": data[0][1], "fname": data[0][2] + " " + data[0][3]}

    return user

@login_manager.request_loader
def request_loader(request):
    users = getUserList()
    email = request.form.get('email')
    if not (email) or email in str(users):
        return
    user = User()
    user.id = email
    cursor = mysql.connect().cursor()
    cursor.execute("SELECT password, id, email, fname, lname FROM Users WHERE email = '{0}'".format(email))
    data = cursor.fetchall()
    pwd = str(data[0][0])
    user.is_authenticated = request.form['password'] == pwd
    if user.is_authenticated:
        user.account = {"id": data[0][1], "email": data[0][2], "fname": data[0][3] + " " + data[0][4]}
    return user

@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('requirelogin.html')

@app.route("/")
def main():
    return render_template('index.html')

@app.route("/login")
def login():
    return render_template('login.html')

@app.route("/register")
def register():
    return render_template('register.html')

if __name__ == "__main__":
    app.run(debug=True)
