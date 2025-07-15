from flask import Flask
from flask import request

from explotest import explore, Mode

app = Flask(__name__)


@app.route("/")
@explore(mode=Mode.PICKLE)
def hello_world():
    if request.method == "GET":
        return "<p>Hello, World!</p>"
    else:
        return "<p>Goodbye, World!</p>"
