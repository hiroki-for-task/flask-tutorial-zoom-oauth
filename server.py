from firebase_admin import firestore
from firebase_admin import credentials
from firebase_admin import storage
import firebase_admin
import os
from flask import Flask, request, jsonify, redirect
import settings
import requests
import base64
import json
import logging
from datetime import datetime, timezone
import re


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
CREDENTIAL_FILE_PATH = os.environ['CREDENTIAL_FILE_PATH']
cred = credentials.Certificate(os.environ['CREDENTIAL_FILE_PATH'])
firebase_admin.initialize_app(cred, {
    "projectId": PROJECT_ID,
    'storageBucket': BUCKET_NAME
})
db = firestore.client()


app = Flask(__name__)


@app.route('/initialize_zoom_access_token')
def initialize_zoom_access_token_debag():
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """

    try:
        # リクエストパラメータの取得
        request_json = request.get_json(silent=True)
        request_args = request.args
        code = request.args.get('code')
        state = request.args.get('state')

        # stateで支持された認証鍵を探す
        doc_ref = db.collection('temporalKeys').document(
            'zoom').collection('keys').document(state)
        doc = doc_ref.get()

        # firestoreに認証鍵が存在しているかチェック
        # もし存在していなかった invalid pageにリダイレクト
        if doc.exists:
            # 認証鍵の情報を取得
            tmpKey = doc.to_dict()
            enterpriseId, expired_date, enterprise_id = tmpKey[
                'enterpriseId'], tmpKey['expiredDate'], tmpKey['enterpriseId']
            # firestoreに保存されたexpired時刻 と 現在時刻を比較
            # もし現在時刻がexpired時刻を過ぎていたら invalid pageにリダイレクト
            if datetime.now(timezone.utc) > expired_date:
                logger.info('the key was expired')
                return redirect(REDIRECT_TO_REACT_APP_URL, code=301)
            # enteriseId が存在しなかった場合の処理
            elif not enterpriseId:
                logger.info('there is no enterprise Id')
                return redirect(REDIRECT_TO_REACT_APP_URL, code=301)
        else:
            logger.info('there is no document')
            return redirect(REDIRECT_TO_REACT_APP_URL, code=301)

        # request the access token
        url = 'https://zoom.us/oauth/token?grant_type=authorization_code&code={}&redirect_uri={}'.format(
            code,
            format(os.path.join(FLASK_SEVER_URL, 'initialize_zoom_access_token'))
        )

        logger.info('url : {}'.format(url))
        encoded = base64.b64encode(bytes(BASE64_CLIENT, 'utf-8'))
        headers = {"Authorization": "Basic {}".format(encoded.decode("utf-8"))}
        response = requests.post(url, headers=headers)
        access_token = response.json()

        # access tokens の加工
        access_token.update({
            'created_date': datetime.now(timezone.utc),
            'is_expored': False
        })

        # save the access token to GCS
        doc_ref = db.collection('enterprises').document(
            enterprise_id).collection('accessTokens').document('zoom')
        doc_ref.delete()  # 既にAccess Tokenが存在した場合, 削除
        doc_ref.set(access_token)

        # 正常に終了した場合、正常ページにリダイレクト
        return redirect(REDIRECT_TO_REACT_APP_URL, code=301)
    except Exception as e:
        # 何かしらの問題が起こったら invalid pageへリダイレクト
        return redirect(REDIRECT_TO_REACT_APP_URL, code=301)


@app.route('/testing')
def testing():
    #userのEmailは与えられているとする
    user_email = 'tf112022524277@gmail.com'
    #emaiからenterprise_idとuser_idを取得する
    eachEmails = db.collection('allEmails').document(user_email).get()
    enterprise_id = eachEmails.to_dict()['enterpriseId']
    user_id = eachEmails.to_dict()['userId']
    #すでに取得してあるvideoのidリストを取得する
    existed_recording_id = db.collection('enterprises').document(enterprise_id).collection('recordings').stream()
    existed_recording_id_list = []
    for ids in existed_recording_id:
        existed_recording_id_list.append(ids.id)
    #アクセストークンの取得
    access_token = db.collection('enterprises').document(enterprise_id).collection('accessTokens').document('zoom').get().to_dict()['access_token']
    #recordingリストを取得する
    api_get_all_recordings = 'https://api.zoom.us/v2/users/{}/recordings'.format(user_email)
    headers = {"Authorization": "Bearer {}".format(access_token)}
    recordings = requests.get(api_get_all_recordings,headers=headers).json()
    return recordings

@app.route('/getExistedRecording')
def getExistedRecording():
    #userのEmailは与えられているとする
    user_email = 'tf112022524277@gmail.com'
    #emaiからenterprise_idとuser_idを取得する
    eachEmails = db.collection('allEmails').document(user_email).get()
    enterprise_id = eachEmails.to_dict()['enterpriseId']
    user_id = eachEmails.to_dict()['userId']
    #すでに取得してあるvideoのidリストを取得する
    existed_recording_id = db.collection('enterprises').document(enterprise_id).collection('recordings').stream()
    existed_recording_id_list = []
    for ids in existed_recording_id:
        existed_recording_id_list.append(ids.id)
    #アクセストークンの取得
    access_token = db.collection('enterprises').document(enterprise_id).collection('accessTokens').document('zoom').get().to_dict()['access_token']
    #recordingリストを取得する
    api_get_all_recordings = 'https://api.zoom.us/v2/users/{}/recordings'.format(user_email)
    headers = {"Authorization": "Bearer {}".format(access_token)}
    recordings = requests.get(api_get_all_recordings,headers=headers).json()['meetings']
    for recording in recordings:
        recording_id = str(recording['id'])
        #レコーディングリストの中から、まだ取得していないもののみを抽出する
        if recording_id not in existed_recording_id_list:
            #ミーティングについての情報を取得
            api_get_past_meeting_info = 'https://api.zoom.us/v2/past_meetings/{}'.format(recording_id)
            try:
                meeting_info = requests.get(api_get_past_meeting_info ,headers=headers).json()
                #firestoreのrecordingsの情報を書き換える
                recording_collection = db.collection('enterprises').document(enterprise_id).collection('recordings').document(recording_id)
                #start_timeをdatetime型に
                start_time_str_list = re.split ( '[-,T,:,Z]', recording['start_time'] )
                year = int(start_time_str_list[0])
                month = int(start_time_str_list[1])
                day = int(start_time_str_list[2])
                hour = int(start_time_str_list[3])
                minute = int(start_time_str_list[4])
                second = int(start_time_str_list[5])
                start_time = datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)
                #end_timeをdatetime型に
                end_time_str_list = re.split ( '[-,T,:,Z]', meeting_info['end_time'] )
                year = int(end_time_str_list[0])
                month = int(end_time_str_list[1])
                day = int(end_time_str_list[2])
                hour = int(end_time_str_list[3])
                minute = int(end_time_str_list[4])
                second = int(end_time_str_list[5])
                end_time = datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)
                recording_info = {
                    'type' : 'video',
                    'app' : 'zoom',
                    'recordingId' : recording_id,
                    'recordingIdentifer' : recording['uuid'],
                    'startTime' : start_time,
                    'duration' : recording['duration'],
                    'accountId' : recording['account_id'],
                    'hostId' : recording['host_id'],
                    'topic' : recording['topic'],
                    'totalSize' : recording['total_size'],
                    'MeetingType' : recording['type'],
                    'recordingCount' : recording['recording_count'],
                    'shareUrl' : recording['share_url'],
                    'userName' : meeting_info['user_name'],
                    'userEmail' : meeting_info['user_email'],
                    'endTime' : end_time
                }
                print(recording_info)
                recording_collection.set(recording_info,merge=True)
                for recording_file in recording['recording_files']:
                    recording_file_id = recording_file['id']
                    recording_file_collection = db.collection('enterprises').document(enterprise_id).collection('recordings').document(recording_id).collection('recordingFile').document(recording_file_id)
                    recording_file_info = {
                        'recordingFileId' : recording_file_id,
                        'meetingId' : recording_id,
                        'fileType' : recording_file['file_type'],
                        'fileSize' : recording_file['file_size'],
                        'downloadUrl' : recording_file['download_url'],
                        'recordingType' : recording_file['recording_type'],
                    }
                    recording_file_collection.set(recording_file_info,merge=True)
                    #ファイルを保存
                    file_type = recording_file['file_type']
                    if recording_file['file_type'] == 'TIMELINE':
                        file_type = 'json'
                    get_url = '{downloadpath}?access_token={access_token}'.format(downloadpath=recording_file['download_url'],access_token=access_token)
                    response = requests.get(get_url)
                    with open('tmp.{}'.format(file_type), 'wb') as saveFile:
                        saveFile.write(response.content)
                    local_file_name = './tmp.{}'.format(file_type)
                    remote_blob_name = 'enterprises/{enterprise_id}/recordings/{recording_id}/{recording_file_id}.{file_type}'.format(enterprise_id=enterprise_id,recording_id=recording_id,recording_file_id=recording_file_id, file_type=file_type)
                    blob = storage.bucket().blob(remote_blob_name)
                    blob.upload_from_filename(local_file_name)
                    

                    #if recording_file['file_type'] == 'TIMELINE':
                        #print('Yes')
                        #get_url = '{downloadpath}?access_token={access_token}'.format(downloadpath=recording_file['download_url'],access_token=access_token)
                        #timeline = requests.get(get_url).json()
                        #recording_collection.set(timeline,merge=True)
                #参加者についての情報を取得
                api_get_past_meeting_participants_info = 'https://api.zoom.us/v2/past_meetings/{}/participants'.format(recording_id)
                participants_info = requests.get(api_get_past_meeting_participants_info ,headers=headers).json()['participants']
                recording_collection.set({'participants':participants_info},merge=True)
                #firestoreのreflectedRecordingsの情報を書き換える
                reflected_recordings_collection = db.collection('enterprises').document(enterprise_id).collection('reflectedRecordings').document()
                reflected_recording_info = {
                    'type' : 'video',
                    'app' : 'zoom',
                    'visible' : True,
                    'permissons' : 'inhouse',
                    'contentId' : recording_id,
                    'createdDate' : datetime.now(),
                    'startTime' : start_time,
                    'hostEmail' : meeting_info['user_email'],
                    'topic' : recording['topic']
                }
                reflected_recordings_collection.set(reflected_recording_info,merge=True)
                reflected_recordings_collection.set({'participants':participants_info},merge=True)

            except Exception as e:
                logger.info('error:{}'.format(str(e)))
                pass

    return 'success'


@app.route('/test')
def test():
    print('line1')
    #userのEmailは与えられているとする
    user_email = 'tf112022524277@gmail.com'
    #emaiからenterprise_idとuser_idを取得する
    eachEmails = db.collection('allEmails').document(user_email).get()
    enterprise_id = eachEmails.to_dict()['enterpriseId']
    user_id = eachEmails.to_dict()['userId']
    recording_id = str(274294328)
    print(enterprise_id)
    recording_collection = db.collection('enterprises').document(enterprise_id).collection('recordings').document(recording_id)
    recording_info = {'type' : 'video', 'app' : 'zoom'}
    recording_collection.set(recording_info,merge=True)
    return 'success'

@app.route('/test2', methods=['GET','POST'])
def test2():
    print('recording post is coming')
    print(request.get_data())
    return 'recording post is coming'

@app.route('/reserveZoomMeeting')
def reserveZoomMeeting():
    #入力情報
    user_email = 'tf112022524277@gmail.com'
    meeting_type = 2
    topic = 'Hiroki_Shimizuのテスト'
    start_time = datetime(year=2021,month=1,day=28,hour=13,minute=0,second=0)
    timezone = 'Asia/Tokyo'
    password = 'password'
    auto_recording = True
    join_before_host = True
    jbh_time = 0

    #ここから予約投稿
    #userのEmailは与えられているとする
    user_email = 'tf112022524277@gmail.com'
    #emaiからenterprise_idとuser_idを取得する
    eachEmails = db.collection('allEmails').document(user_email).get()
    enterprise_id = eachEmails.to_dict()['enterpriseId']
    user_id = eachEmails.to_dict()['userId']
    #accesss token取得
    access_token = db.collection('enterprises').document(enterprise_id).collection('accessTokens').document('zoom').get().to_dict()['access_token']
    start_time = '{year}-{month}-{day}T{hour}:{minute}:{second}'.format(year=start_time.year, month=(str(start_time.month)).zfill(2), day=(str(start_time.day)).zfill(2), hour=(str(start_time.hour)).zfill(2), minute=(str(start_time.minute)).zfill(2), second=(str(start_time.second)).zfill(2))
    if auto_recording:
        auto_recording = 'cloud'
    else:
        auto_recording = 'none'
    
    body = {
        'topic' : topic,
        'type' : meeting_type,
        'start_time' : start_time,
        'timezone' : timezone,
        'password' : password,
        'settings' : {
            'join_before_host' : join_before_host,
            'jbh_time' : jbh_time,
            'auto_recording' : auto_recording
        }
    }
    api_creat_meeting = 'https://api.zoom.us/v2/users/{}/meetings'.format(user_email)
    headers = {"Authorization": "Bearer {}".format(access_token),'Content-Type': 'application/json'}
    response = requests.post(api_creat_meeting ,data=json.dumps(body), headers=headers).json()
    reserved_id = str(json.dumps(response['id']))
    reserve_meeting_collection = db.collection('enterprises').document(enterprise_id).collection('users').document(user_id).collection('reservedMeetings').document(reserved_id)
    reserved_info = {
        'type' : 'video',
        'app' : 'zoom',
        'meetingInfo' : response
    }
    reserve_meeting_collection.set(reserved_info,merge=True)
    return 'success'


@app.route('/updateReservedZoomMeeting')
def updateReservedZoomMeeting():
    #入力情報
    user_email = 'tf112022524277@gmail.com'
    meeting_type = 2
    topic = 'Hiroki_Shimizuのテスト'
    start_time = datetime(year=2021,month=1,day=28,hour=13,minute=0,second=0)
    timezone = 'Asia/Tokyo'
    password = 'password'
    auto_recording = False
    join_before_host = True
    jbh_time = 0
    meeting_id = 91600058805

    #ここから予約投稿
    #userのEmailは与えられているとする
    user_email = 'tf112022524277@gmail.com'
    #emaiからenterprise_idとuser_idを取得する
    eachEmails = db.collection('allEmails').document(user_email).get()
    enterprise_id = eachEmails.to_dict()['enterpriseId']
    user_id = eachEmails.to_dict()['userId']
    #accesss token取得
    access_token = db.collection('enterprises').document(enterprise_id).collection('accessTokens').document('zoom').get().to_dict()['access_token']
    start_time = '{year}-{month}-{day}T{hour}:{minute}:{second}'.format(year=start_time.year, month=(str(start_time.month)).zfill(2), day=(str(start_time.day)).zfill(2), hour=(str(start_time.hour)).zfill(2), minute=(str(start_time.minute)).zfill(2), second=(str(start_time.second)).zfill(2))
    if auto_recording:
        auto_recording = 'cloud'
    else:
        auto_recording = 'none'
    
    body = {
        'topic' : topic,
        'type' : meeting_type,
        'start_time' : start_time,
        'timezone' : timezone,
        'password' : password,
        'settings' : {
            'join_before_host' : join_before_host,
            'jbh_time' : jbh_time,
            'auto_recording' : auto_recording
        }
    }
    api_update_meeting = 'https://api.zoom.us/v2/meetings/{}'.format(meeting_id)
    headers = {"Authorization": "Bearer {}".format(access_token),'Content-Type': 'application/json'}
    requests.patch(api_update_meeting ,data=json.dumps(body), headers=headers)
    return 'success'


@app.route('/deleteZoomMeeting')
def deleteZoomMeeting():
    #入力情報
    reserved_id = 99414062621
    #userのEmailは与えられているとする
    user_email = 'tf112022524277@gmail.com'
    #emaiからenterprise_idとuser_idを取得する
    eachEmails = db.collection('allEmails').document(user_email).get()
    enterprise_id = eachEmails.to_dict()['enterpriseId']
    user_id = eachEmails.to_dict()['userId']
    #accesss token取得
    access_token = db.collection('enterprises').document(enterprise_id).collection('accessTokens').document('zoom').get().to_dict()['access_token']
    api_delete_meeting = 'https://api.zoom.us/v2/meetings/{}'.format(reserved_id)
    headers = {"Authorization": "Bearer {}".format(access_token)}
    requests.delete(api_delete_meeting, headers=headers)
    reserved_id = str(reserved_id)
    db.collection('enterprises').document(enterprise_id).collection('users').document(user_id).collection('reservedMeetings').document(reserved_id).delete()
    return 'success'


@app.route('/getReservedZoomMeetings')
def getReservedZoomMeetings():
    #userのEmailは与えられているとする
    user_email = 'tf112022524277@gmail.com'
    #emaiからenterprise_idとuser_idを取得する
    eachEmails = db.collection('allEmails').document(user_email).get()
    enterprise_id = eachEmails.to_dict()['enterpriseId']
    user_id = eachEmails.to_dict()['userId']
    #accesss token取得
    access_token = db.collection('enterprises').document(enterprise_id).collection('accessTokens').document('zoom').get().to_dict()['access_token']
    api_get_reserved_meeting_list = 'https://api.zoom.us/v2/users/{}/meetings'.format(user_email)
    headers = {"Authorization": "Bearer {}".format(access_token)}
    meetings = requests.get(api_get_reserved_meeting_list, headers=headers).json()['meetings']
    for meeting in meetings:
        reserved_id = meeting['id']
        meeting_collection = db.collection('enterprises').document(enterprise_id).collection('users').document(user_id).collection('reservedMeetings').document(str(reserved_id))
        meeting_info = {
            'type' : 'video',
            'app' : 'zoom',
            'meetingInfo' : meeting
        }
        meeting_collection.set(meeting_info,merge=True)
    return 'success'


if __name__ == "__main__":
    logger.info('[log] start server')
    app.run(debug=True, host="0.0.0.0", port=int(
        FLASK_SEVER_PORT if FLASK_SEVER_PORT is not None else 8080))
