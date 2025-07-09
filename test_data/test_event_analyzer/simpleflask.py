from flask import Flask
from flask import request

import explotest as et

app = Flask(__name__)


@app.route("/")
@et.explore
def hello_world():
    if request.method == "GET":
        return "<p>Hello, World!</p>"
    else:
        return "<p>Goodbye, World!</p>"
