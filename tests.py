import requests
import httplib
import unittest
import simplejson as json
httplib.HTTPConnection.debuglevel = 1

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

#url = 'http://recommender.oscar.ncsu.edu/api/v2/'
url = 'http://localhost:5000'
s = requests.Session()
s.headers.update({'Content-Type': 'application/json'})
s.auth = auth("Test")

def get_collection(col, auth=None):
    
    return s.get(url+'/'+col, auth=auth).json()

def get_item(col, id):
    return s.get(url+'/'+col+'/'+id).json()

def create_item(collection, data):
    result = s.post(url+'/'+collection,
                    data=json.dumps(data))
    try:
        return result.json()
    except Exception:
        return result

def update_item(item, data, auth=None):
    return s.patch(url+item['_links']['self']['href'],
                   headers={"If-Match": item['_etag']},
                   data=json.dumps(data),
                   auth=auth).json()

def delete_item(item, data, auth=None):
    return s.delete(url+item['_links']['self']['href'],
                    headers={"If-Match": item['_etag']},
                    auth=auth).json()

def replace_item(item, data, auth=None):
    return s.put(url+item['_links']['self']['href'],
                 headers={"If-Match": item['_etag']},
                 data=json.dumps(data),
                 auth=auth).json()

class TestBasicEndpoints(unittest.TestCase):
    def runTest(self): pass

    @classmethod
    def setUpClass(cls):
        get_collection('applications', auth=auth("Test"))
        get_collection('applications', auth=auth("Delete"))
        get_collection('applications', auth=auth("User1"))
    
    def setUp(self):
        print "\n\n"

    def test_applications(self):
        self.assertTrue(len(get_collection('applications')) > 0)

    def test_users(self):
        self.assertTrue(len(get_collection('users')) > 0)

    def test_update_user(self):
        u = get_item('users', 'test@mailinator.com')
        result = update_item(u, {'name': 'Test User'})
        print result
        self.assertIsNotNone(result)
        self.assertIsNotNone(result['_status'])
        self.assertEquals(result['_status'], 'OK')

    def test_user_escalation(self):
        u = get_item('users', 'test@mailinator.com')
        result = update_item(u, {'roles': ['admin']})
        print result
        self.assertIsNotNone(result)
        self.assertIsNotNone(result['_status'])
        self.assertEquals(result['_status'], 'ERR')
        self.assertEquals(result['_error']['code'], 403)

    def test_admin_privileges(self):
        u = get_item('users', 'test@mailinator.com')
        result = update_item(u, {'roles': ['user']}, auth=auth('Admin'))
        print result
        self.assertIsNotNone(result)
        self.assertIsNotNone(result['_status'])
        self.assertEquals(result['_status'], 'OK')

    def test_update_other_user(self):
        u = get_item('users', users['User1']['email'])
        result = update_item(u, {'name': 'Test User'})
        print result
        self.assertIsNotNone(result)
        self.assertIsNotNone(result['_status'])
        self.assertEquals(result['_status'], 'ERR')
        self.assertEquals(result['_error']['code'], 403)

    def test_create_user(self):
        result = create_item('users', {'name': 'Test User', 'email': 'test2@mailinator.com'})
        print result
        assert result.status_code == 405

    def test_delete_user(self):
        u = get_item('users', 'test@mailinator.com')
        result = delete_item(u, {'name': 'Test User'})
        print result
        self.assertEquals(result, {})

    def test_delete_other_user(self):
        u = get_item('users', users['Delete']['email'])
        result = delete_item(u, {'name': 'Test User'})
        print result
        self.assertIsNotNone(result)
        self.assertIsNotNone(result['_status'])
        self.assertEquals(result['_status'], 'ERR')
        self.assertEquals(result['_error']['code'], 403)

    def test_send_notification(self):
        tool = get_collection('tools?where={"application":"Eclipse"}')['_items'][0]
        result = create_item('notifications', {
            'recipient':'user1@mailinator.com', 
            'message': 'Test Message',
            'application': "Eclipse",
            'type': 'message',
            'status': 'new'
        })
        self.assertIsNotNone(result)
        self.assertIsNotNone(result['_status'])
        self.assertEquals(result['_status'], 'OK')

    def test_update_notification(self):
        notes = get_collection('notifications')['_items']
        self.assertGreater(len(notes), 0)
        note = notes[0]
        result = update_item(note, {
            'status': 'updated'
        })
        self.assertIsNotNone(result)
        self.assertIsNotNone(result['_status'])
        self.assertEquals(result['_status'], 'OK')

    def test_update_other_notification(self):
        notes = get_collection('notifications')['_items']
        self.assertGreater(len(notes), 0)
        note = notes[0]
        result = update_item(note, {
            'status': 'tampered'
        }, auth('Delete'))
        self.assertIsNotNone(result)
        self.assertIsNotNone(result['_status'])
        self.assertEquals(result['_status'], 'ERR')
        self.assertEquals(result['_error']['code'], 403)

    

test = TestBasicEndpoints()            

if __name__ == '__main__':
    unittest.main()
