from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    return "The basic index route for the orders app."


if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0')
