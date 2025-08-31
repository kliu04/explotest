from flask import Flask
from flask import request


app = Flask(__name__)


@app.route("/")
def hello_world():
    print(request.__doc__)
    if request.method == "GET":
        return "<p>Hello, World!</p>"
    else:
        return "<p>Goodbye, World!</p>"
