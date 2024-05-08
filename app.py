from flask import Flask, flash, request, redirect, session, render_template, abort, url_for, jsonify
from functools import wraps


# App
app = Flask(__name__)
app.secret_key = 'my super secret key'


# API
APP_ID = 'b1fa76db'
API_KEY = '53125e7fe9fd59ceb0f1c2dc4b04ab8f'


if __name__ == "__main__":
    app.run(debug=True)

from routes import *