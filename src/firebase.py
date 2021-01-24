import os
import logging
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ID = os.environ['PROJECT_ID']
BUCKET_NAME = os.environ['BUCKET_NAME']
BUCKET_NAME = os.environ['CREDENTIAL_FILE_PATH']
cred = credentials.Certificate(os.environ['CREDENTIAL_FILE_PATH'])
firebase_admin.initialize_app(cred, {
    "projectId": PROJECT_ID,
    'storageBucket': BUCKET_NAME
})

bucket_path = os.path.join(
    'https://storage.googleapis.com/', os.environ['BUCKET_NAME'])
gs_path = os.path.join('gs://', os.environ['BUCKET_NAME'])


def add_access_token_to_firestore(access_token):
    pass


def update_access_token_to_firestore():
    return (gs_path)
