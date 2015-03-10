import pymongo, json, smtplib
from pymongo import MongoClient
from datetime import datetime, timedelta
from bson.code import Code

passwords = {}

with open('passwordFile.json','r') as f:
    passwords = json.load(f)


client = MongoClient()
client.socaster.authenticate(passwords['mongo_user'],passwords['mongo_pw'])
db = client.socaster

reducer = Code("""
function(cur, result) {
    result.count = result.count + 1;
}
""")

msg = "Usages in the last 24 hours:\n"

yesterday = datetime.now() - timedelta(days=1)
print yesterday

for user in db.users.find():
    if ('user_id' in user.keys()):
        msg = msg+user.get('name','BLANK')+"\n"
        msg = msg+user.get('user_id')+"\n"
        events = db.events.group(key={ "application": 1, "tool" : 1 }, condition={"user_id": user['user_id'], "time":{"$gt": yesterday} }, reduce=reducer,initial={ "count": 0 })
        for event in events:
            msg = msg + event

print msg

server = smtplib.SMTP('smtp.gmail.com:587')
server.ehlo()
server.starttls()
server.login(passwords['email_username'],passwords['email_pw'])
server.sendmail(passwords['email_username'], passwords['my_email'], msg)
server.quit()
