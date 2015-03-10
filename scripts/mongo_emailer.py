import pymongo, json, smtplib, datetime
from pymongo import MongoClient
from datetime import timedelta

passwords = {}

with open('passwordFile.json','r') as f:
    passwords = json.load(f)


client = MongoClient()
client.socaster.authenticate(passwords.mongo_user,passwords.mongo_pw)
db = client.socaster

reducer = Code("""
function(cur, result) {
    result.count = result.count + 1;
}
""")

msg = "Usages in the last 24 hours:\n"

yesterday = datetime.datetime.now().timedelta(days=-1)

for user in db.users.find():
    msg = msg+user.name+"\n"
    msg = msg+user.user_id+"\n"
    events = db.events.group(key={ "application": 1, "tool" : 1 }, condition={"user_id": user.user_id, "time":{"$gt": yesterday} }, reduce=reducer,initial={ "count": 0 })
    for event in events
        msg = msg + event


server = smtplib.SMTP('smtp.gmail.com:587')
server.ehlo()
server.starttls()
server.login(passwords.email_username,passwords.email_pw)
server.sendmail(passwords.email_username, passwords.my_email, msg)
server.quit()
