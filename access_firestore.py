from firebase_admin import firestore
from firebase_admin import credentials
import firebase_admin
import os
from flask import Flask, request, jsonify, redirect
import settings
import requests
import base64
import json
import logging
from datetime import datetime, timezone

# logging setting
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# setting of environements
FLASK_SEVER_PORT = os.environ.get("FLASK_SEVER_PORT")
FLASK_SEVER_URL = os.environ.get("FLASK_SEVER_URL")
REDIRECT_TO_REACT_APP_URL = os.environ.get("REDIRECT_TO_REACT_APP_URL")
ZOOM_APP_CLIENT_ID = os.environ.get("ZOOM_APP_CLIENT_ID")
ZOOM_APP_CLIENT_SECRET = os.environ.get("ZOOM_APP_CLIENT_SECRET")
BASE64_CLIENT = '{}:{}'.format(ZOOM_APP_CLIENT_ID, ZOOM_APP_CLIENT_SECRET)

# authorize firebase
PROJECT_ID = os.environ['PROJECT_ID']
BUCKET_NAME = os.environ['BUCKET_NAME']
BUCKET_NAME = os.environ['CREDENTIAL_FILE_PATH']
cred = credentials.Certificate(os.environ['CREDENTIAL_FILE_PATH'])
firebase_admin.initialize_app(cred, {
    "projectId": PROJECT_ID,
    'storageBucket': BUCKET_NAME
})
db = firestore.client()

app = Flask(__name__)
