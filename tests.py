import requests
import httplib
import unittest
import simplejson as json
import logging
import random
from run import *
logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())

users = {
    'Test': {
        'name': 'Test User',
        'email': 'test@mailinator.com',
        'token': '123',
    },
    'Admin': {
        'name': 'Admin User',
        'email': 'admin@mailinator.com',
        'token': '191191134509801459801',
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

def email(user):
    return users[user]['email']

#url = 'http://recommender.oscar.ncsu.edu/api/v2'
url = 'http://localhost:5000'
s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.auth = auth("Test")

def get_collection(col, where=None, auth=None):
    params={'where': json.dumps(where)} if where else None
    return s.get(url+'/'+col, params=params, auth=auth).json().get('_items', [])

def delete_collection(col, where=None, auth=None):
    return s.delete(url+'/'+col,
                    params={'where': json.dumps(where)} if where else {},
                    auth=auth).json()

def get_item(col, id):
    return s.get(url + '/' + col + '/' + id).json()

def create_item(collection, data, auth=None):
    result = s.post(url+'/'+collection,
                    data=json.dumps(data),
                    auth=auth)
    try:
        return result.json()
    except Exception:
        return result

def upload_item(collection, files, auth=None):
    result = s.post(url+'/'+collection,
                    files=files,
                    headers={'Content-Type': 'multipart/form-data'},
                    auth=auth)
    try:
        return result.json()
    except Exception:
        return result

def update_item(item, data, auth=None):
    return s.patch(url+item['_links']['self']['href'],
                   headers={"If-Match": item['_etag']},
                   data=json.dumps(data),
                   auth=auth).json()

def delete_item(item, auth=None):
    return s.delete(url+item['_links']['self']['href'],
                    headers={"If-Match": item['_etag']},
                    auth=auth).json()

def replace_item(item, data, auth=None):
    return s.put(url+item['_links']['self']['href'],
                 headers={"If-Match": item['_etag']},
                 data=json.dumps(data),
                 auth=auth).json()

def ensure_users(*users):
    for user in users:
        get_collection('applications', auth=auth(user))

def ensure_item(col, item, auth=None):
    items = get_collection(col, where=item)
    if len(items) == 0:
        return create_item(col, item, auth=auth)
    return items[0]

def ensure_items(col, *items, **kwargs):
    auth = kwargs.get('auth')
    return map(lambda item: ensure_item(col, item, auth=auth),
               items)

class TestBasicEndpoints(unittest.TestCase):
    #pass so instance doesn't automatically run tests
    def runTest(self): pass 

    @classmethod
    def setUpClass(cls):
        #ensure 3 users
        ensure_users("Test", "Delete", "User1")
        tools = ensure_items('tools', {'name': 'Save', 'application': 'Eclipse'})
        usages = ensure_items('usages', {'tool': tools[0]['_id'], 'keyboard': 5})
        clips = ensure_items('clips', {
            'name': 'TestClip', 
            'tool': tools[0]['_id'],
            'share': ['public'],
        })
        print ensure_items('ratings', {
            'clip': clips[0]['_id'], 'value': 3, 'user': email('Test')
        })
        print ensure_items('ratings', {'clip': clips[0]['_id'], 'value': 3, 'user': email('User1')},
                     auth=auth('User1'))

    def assert_success(self, result):
        print result
        self.assertIsNotNone(result)
        self.assertIsNotNone(result['_status'])
        self.assertEquals(result['_status'], 'OK')

    def assert_failure(self, result, code=403):
        print result
        self.assertIsNotNone(result)
        self.assertIsNotNone(result['_status'])
        self.assertEquals(result['_status'], 'ERR')
        self.assertEquals(result['_error']['code'], code)

    def test_applications(self):
        self.assertTrue(len(get_collection('applications')) > 0)

    def test_users(self):
        self.assertTrue(len(get_collection('users')) > 0)

    def test_update_user(self):
        u = get_item('users', 'test@mailinator.com')
        result = update_item(u, {'name': 'Test User'})
        self.assert_success(result)

    def test_user_escalation(self):
        u = get_item('users', 'test@mailinator.com')
        result = update_item(u, {'roles': ['admin']})
        self.assert_failure(result)

    def test_admin_privileges(self):
        u = get_item('users', 'test@mailinator.com')
        result = update_item(u, {'roles': ['user']}, auth=auth('Admin'))
        self.assert_success(result)

    def test_update_other_user(self):
        u = get_item('users', email('User1'))
        result = update_item(u, {'name': 'Test User'})
        self.assert_failure(result)

    def test_create_user(self):
        result = create_item('users', {'name': 'Test User', 'email': 'test2@mailinator.com'})
        assert result.status_code == 405

    def test_delete_user(self):
        u = get_item('users', email('Delete'))
        result = delete_item(u, auth=auth('Delete'))
        self.assertEquals(result, {})

    def test_delete_other_user(self):
        u = get_item('users', email('Test'))
        result = delete_item(u, auth=auth('Delete'))
        self.assert_failure(result)

    def test_send_notification(self):
        tool = get_collection('tools', where={"application":"Eclipse"})[0]
        result = create_item('notifications', {
            'recipient':'user1@mailinator.com', 
            'message': 'Test Message',
            'application': "Eclipse",
            'type': 'message',
            'status': 'new'
        })
        self.assert_success(result)

    def test_update_notification(self):
        notes = get_collection('notifications')
        self.assertGreater(len(notes), 0)
        note = notes[0]
        result = update_item(note, {
            'status': 'updated'
        })
        self.assert_success(result)

    def test_update_other_notification(self):
        notes = get_collection('notifications')
        self.assertGreater(len(notes), 0)
        note = notes[0]
        result = update_item(note, {
            'status': 'tampered'
        }, auth('Delete'))
        self.assert_failure(result)

    def test_create_public_clip(self):
        tool = get_collection('tools', where={"application":"Eclipse"})[0]
        result = create_item('clips', {
            'name': 'TestClip',
            'tool': tool['_id'],
            'share': ['public'],
            'type': 'keyboard',
        })
        self.assert_success(result)

    def test_create_clip_bad_share(self):
        tool = get_collection('tools', where={"application":"Eclipse"})[0]
        result = create_item('clips', {
            'name': 'TestClip',
            'tool': tool['_id'],
            'share': ['blah'],
            'type': 'keyboard',
        })
        self.assert_failure(result, code=400)

    def test_create_clip_share_user(self):
        tool = get_collection('tools', where={"application":"Eclipse"})[0]
        result = create_item('clips', {
            'name': 'TestClip',
            'tool': tool['_id'],
            'share': [email('User1')],
            'type': 'keyboard',
        })
        self.assert_success(result)

    def test_new_rating(self):
        clip = get_collection('clips')[0]
        result = create_item('ratings', {
            'clip': clip['_id'],
            'value': 3
        })
        self.assert_success(result)

    def test_update_rating(self):
        rating = get_collection('ratings', where={"user": email('Test')})[0]
        result = update_item(rating, {
            'value': 3
        })
        self.assert_success(result)

    def test_new_duplicate_rating(self):
        rating = get_collection('ratings', where={"user": email('Test')})[0]
        result = create_item('ratings', {
            'clip': rating['clip'],
            'value': 4
        })
        self.assert_failure(result, 400)

    def test_new_duplicate_rating_other_user(self):
        rating = get_collection('ratings', where={"user":{"$ne": email('User1')}})[0]
        result = create_item('ratings', {
            'clip': rating['clip'],
            'value': 4
        }, auth=auth('User1'))
        self.assert_success(result)

    def test_admin_delete_collection(self):
        result = delete_collection('ratings', auth=auth('Admin'))
        self.assertEquals(result, {})

    def test_user_delete_collection(self):
        result = delete_collection('ratings')
        self.assert_failure(result)

    def test_upload_image(self):
        clip = get_collection('clips', where={"user": email('Test')})[0]
        result = requests.post(url+'/clips/%s/images' % clip['_id'],
                               files={"data": open("frame000.jpg", 'rb')},
                               data={'name': 'TestFrame'},
                               auth=auth('Test'))
        self.assertEqual(result.status_code, 201)

    def test_create_usage(self):
        tool = get_collection('tools', where={"application":"Eclipse"})[0]
        result = create_item('usages', {
            'tool': tool['_id'],
        })
        self.assert_success(result)
    
    def test_update_usage(self):
        usage = get_collection('usages', where={"user": email('Test')})[0]
        result = update_item(usage, {
            'keyboard': 3
        })
        self.assert_success(result)

    # Doesn't seem to work...
    # def test_admin_delete_filtered_collection(self):
    #     result = delete_collection('ratings', where={"user": email('Test')},
    #                                auth=auth('Admin'))
    #     self.assertEquals(result, {})

    def test_bulk_usage(self):
        usages = [{
            'app_name': 'Eclipse',
            'tool_name': 'Save',
            'keyboard': 5,
        }, {
            'app_name': 'Excel',
            'tool_name': 'SUM',
            'keyboard': 3,
        }]
        response = s.post(url+'/report-usage', data=json.dumps(usages))
        self.assert_success(response.json())

test = TestBasicEndpoints() #useful for manual testing

if __name__ == '__main__':
    logger.setLevel(logging.ERROR)
    unittest.main()
else:
    httplib.HTTPConnection.debuglevel = 1
    logger.setLevel(logging.DEBUG)
