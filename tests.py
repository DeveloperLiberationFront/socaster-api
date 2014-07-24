import requests
import httplib
httplib.HTTPConnection.debuglevel = 1

url = 'http://recommender.oscar.ncsu.edu/api/v2/'
headers = {'content-type': 'application/json'}

users = {
    'Test': {
        'name': 'Test User',
        'email': 'test@mailinator.com',
        'token': '123',
    },
    'Delete': {
        'name': 'Delete',
        'email': 'delete@mailinator.com',
        'token': '321',
    },
    'User1': {
        'name': 'User1',
        'email': 'user1@mailinator.com',
        'token': '123456',
    },
}

def auth(user):
    return requests.auth.HTTPBasicAuth("{email}|{name}".format(**users[user]), users[user]['token'])

def get_applications(auth=auth("Test")):
    return requests.get(url+'applications', auth=auth)

if __name__ == '__main__':
    print "running test"
    print get_applications().json()
