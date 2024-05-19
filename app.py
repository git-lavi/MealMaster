from flask import Flask


# App
app = Flask(__name__)
app.secret_key = 'your secret key here'


# API
APP_ID = 'your application ID here'
API_KEY = 'your API key here'


if __name__ == "__main__":
    app.run(debug=True)


from routes import *