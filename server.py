from flask import Flask
from flask import request, jsonify
import requests
import base64
import json
import urllib.request
import sys

app = Flask(__name__)

global access_token
access_token = 'eyJhbGciOiJIUzUxMiIsInYiOiIyLjAiLCJraWQiOiIyOGFlMzRlYy04YzVmLTRlMjQtYmRiNi1lZjEyNzE5Y2UzZjgifQ.eyJ2ZXIiOjcsImF1aWQiOiJiNzM5ZjM4YThhOGQ2NzYwOTUzYTUzZWIwOWM4ZmZiNiIsImNvZGUiOiJJeXVyQjNmWEJPX3ZZTVhvUXM3UUxtTUNEa0Ryd19YTUEiLCJpc3MiOiJ6bTpjaWQ6MkZVSVBveDZSZHVIN2x2dUtyb3M0USIsImdubyI6MCwidHlwZSI6MCwidGlkIjowLCJhdWQiOiJodHRwczovL29hdXRoLnpvb20udXMiLCJ1aWQiOiJ2WU1Yb1FzN1FMbU1DRGtEcndfWE1BIiwibmJmIjoxNjExMDMyNzE3LCJleHAiOjE2MTEwMzYzMTcsImlhdCI6MTYxMTAzMjcxNywiYWlkIjoiaXN1MnpmODlTNktTUTFZUkppUENIQSIsImp0aSI6IjdjMTdiMWI1LTliM2UtNGFiOS05OGFlLTI4OTQzOTFlMTE4NSJ9.fEW1JC_L18qL99mFhmuqxusgNWEgxePmz9xVEXcPn1jtdDjCHupqchNm2p8QtjoNFYebbqHgvW79SP7YA1_JNA'
client_id = '2FUIPox6RduH7lvuKros4Q'
client_secret = 'ZW4poSE6QsqgtnnOgdjl9KuJTuBLicYN'
base64_client = '{}:{}'.format(client_id, client_secret)


@app.route('/')
def redirect():
    code = request.args.get('code')

    print(code)
    # setting of url
    url = 'https://zoom.us/oauth/token?grant_type=authorization_code&code={}&redirect_uri=https://b313b6290fd4.ngrok.io'.format(
        code)
    encoded = base64.b64encode(
        bytes(base64_client, 'utf-8')
    )
    headers = {"Authorization": "Basic {}".format(encoded.decode("utf-8"))}
    response = requests.post(url, headers=headers)
    print('hello')
    global access_token
    access_token = json.dumps(response.json())
    return response.json()

@app.route('/get_user_list')
def get_user_list():
    api = 'https://api.zoom.us/v2/users'
    headers = {"Authorization": "Bearer {}".format(access_token)}
    response = requests.get(api,headers=headers)
    return response.text

@app.route('/get_recording_list')
def get_recording_list():
    api = 'https://api.zoom.us/v2/users/vYMXoQs7QLmMCDkDrw_XMA/recordings'
    headers = {"Authorization": "Bearer {}".format(access_token)}
    response = requests.get(api,headers=headers)
    return response.json()

@app.route('/get_timeline')
def get_timeline():
    api = 'https://api.zoom.us/v2/meetings/99316982904/recordings'
    headers = {"Authorization": "Bearer {}".format(access_token)}
    response = requests.get(api,headers=headers)
    data = response.json()
    timeline_url = (json.dumps(data["recording_files"][2]['download_url'], indent=4))[1:-1]
    print(timeline_url)
    get_url = '{downloadpath}?access_token={access_token}'.format(downloadpath=timeline_url,access_token=access_token)
    response = requests.get(get_url)
    return response.text

@app.route('/get_recording')
def get_recording():
    api = 'https://api.zoom.us/v2/meetings/99316982904/recordings'
    headers = {"Authorization": "Bearer {}".format(access_token)}
    response = requests.get(api,headers=headers)
    data = response.json()
    timeline_url = (json.dumps(data["recording_files"][0]['download_url'], indent=4))[1:-1]
    print(timeline_url)
    get_url = '{downloadpath}?access_token={access_token}'.format(downloadpath=timeline_url,access_token=access_token)
    response = requests.get(get_url)
    with open('tmp.mp4', 'wb') as saveFile:
        saveFile.write(response.content)
    return 'success'

@app.route('/post_meeting')
def post_meeting():
    api = 'https://api.zoom.us/v2/users/tf112022524277@gmail.com/meetings'
    headers = {"Authorization": "Bearer {}".format(access_token)}
    body = {
    "topic": "test for recoding separated audio and discussion",
    "type": "2",
    "start_time": "2021-01-19T15:30:00",
    "timezone": "Asia/Tokyo",
    "settings": {
    "auto_recording": "cloud",
    "use_pmi": "false"
        }
    }
    requests.post(api, headers=headers, json=body)
    return body

@app.route('/get_meeting')
def get_meeting():
    api = 'https://api.zoom.us/v2/meetings/97712111589'
    headers = {"Authorization": "Bearer {}".format(access_token)}
    response = requests.get(api,headers=headers)
    data = response.json()
    return data

@app.route('/test')
def test():
    api = 'https://api.zoom.us/v2/meetings/99316982904/recordings'
    headers = {"Authorization": "Bearer {}".format(access_token)}
    response = requests.get(api,headers=headers)
    data = response.json()
    timeline_url = (json.dumps(data["recording_files"][2]['download_url'], indent=4))[1:-2]
    print(timeline_url)
    response = requests.get(timeline_url)
    return response.json()

@app.route('/test2')
def test2():
    api = 'https://api.zoom.us/v2/meetings/99316982904/recordings'
    headers = {"Authorization": "Bearer {}".format(access_token)}
    response = requests.get(api,headers=headers)
    data = response.json()
    timeline_url = (json.dumps(data["recording_files"][2]['download_url'], indent=4))[1:-2]
    print(timeline_url)
    get_url = '{downloadpath}?access_token={access_token}'.format(downloadpath=timeline_url,access_token=access_token)
    response = requests.get(get_url)
    return response.text
    


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=80)
