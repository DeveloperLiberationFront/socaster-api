import pymongo, json, smtplib
from pymongo import MongoClient
from datetime import datetime, timedelta
from bson.code import Code
from email.mime.text import MIMEText

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


yesterday = datetime.now() - timedelta(days=1)
msg = "Usages since "+str(yesterday)+"\n"

# from http://stackoverflow.com/a/11111177/1447621
epoch = datetime.utcfromtimestamp(0)
delta = yesterday - epoch
yesterday_millis = 1000 * (delta.days*86400+delta.seconds)
print yesterday_millis

for user in db.users.find():
    if ('user_id' in user.keys()):
        msg = msg+user.get('name','BLANK')+"\n"
        msg = msg+user.get('user_id')+"\n"
        events = db.events.group(key={ "application": 1, "tool" : 1 }, condition={"user_id": user['user_id'], "time":{"$gt": yesterday_millis} }, reduce=reducer,initial={ "count": 0 })
        for event in events:
            msg = msg + json.dumps(event) +"\n"
        msg = msg + "\n"

print msg

server = smtplib.SMTP('smtp.gmail.com:587')
server.ehlo()
server.starttls()
server.login(passwords['email_username'],passwords['email_pw'])

message = MIMEText(msg)
message['Subject'] = "Daily Socaster Update"
message['To'] = "Experiment Master"
message['From'] = "Automated Machine"

server.sendmail(passwords['email_username'], passwords['my_email'], message.as_string())
server.quit()
