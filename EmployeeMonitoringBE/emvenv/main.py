from flask import Flask

app = Flask(__name__)
# flask --app ./main.py run --debug

@app.route("/")
def hello():
    return "Hello World!"