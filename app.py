import requests
from flask import Flask, render_template, request


app = Flask(__name__)


base_url = "https://pokeapi.co/api/v2/"


@app.route("/")
def index():
    return render_template("index.html")
