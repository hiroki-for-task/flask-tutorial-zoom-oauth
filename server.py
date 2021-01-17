from flask import Flask
from flask import request, jsonify
import requests
import base64

app = Flask(__name__)

client_id = ''
client_secret = ''
base64_client = '{}:{}'.format(client_id, client_secret)


@app.route('/')
def redirect():
    code = request.args.get('code')

    print(code)
    # setting of url
    url = 'https://zoom.us/oauth/token?grant_type=authorization_code&code={}&redirect_uri=https://38e6b2e906d8.ngrok.io'.format(
        code)
    encoded = base64.b64encode(
        bytes(base64_client, 'utf-8')
    )
    headers = {"Authorization": "Basic {}".format(encoded.decode("utf-8"))}
    response = requests.post(url, headers=headers)

    return jsonify({'ready': 'ok'}), 200


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=4000)
