from forum_scraper import login
import requests
from datetime import datetime
import emaildata
import json
import time

fetchURL = "https://artofproblemsolving.com/m/community/ajax.php"


def scrape():
    data = login()
    uid = data["uid"]
    sid = data["sid"]
    payload = {'category_id': '9',
               'log_visit': '0',
               'fetch_all': '1',
               'a': 'fetch_more_items',
               'aops_logged_in': 'true',
               'aops_user_id': uid,
               'aops_session_id': sid}
    files = []
    headers = {
        'Cookie': 'aopssid=' + sid + '; aopsuid=' + uid
    }

    response = requests.request("POST", fetchURL, headers=headers, data=payload, files=files)
    return response.json()['response']['items']


def publish():
    try:
        oldDataFile = open("forums.json", "x")
        oldDataFile.close()
    except:
        print("File exists")
    oldDataFile = open("forums.json", "r")
    oldData = oldDataFile.readlines()
    oldDataFile.close()
    if len(oldData) != 0:
        newData = json.loads(oldData[0])
    else:
        newData = {}
    newData[str(datetime.now())] = scrape()
    newJSON = json.dumps(newData)
    newDataFile = open("forums.json", "w")
    newDataFile.write(newJSON)
    newDataFile.close()
    emaildata.email(newJSON, "Forum scores at " + str(datetime.now()))


def get():
    dataFile = open("forums.json", "r")
    data = dataFile.readlines()
    if (len(data) == 0):
        return {}
    else:
        return json.loads(data[0])


def run():
    while True:
        publish()
        time.sleep(86400)
