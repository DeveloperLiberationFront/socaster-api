DEBUG=True

MONGO_HOST = 'localhost'
MONGO_PORT = 27017
MONGO_USERNAME = 'eve'
MONGO_PASSWORD = 'api service access'
MONGO_DBNAME = 'socaster'

RESOURCE_METHODS = ['GET', 'POST', 'DELETE']
ITEM_METHODS = ['GET', 'PATCH', 'PUT', 'DELETE']

EMBEDDING = True
XML = False

users = {
    'additional_lookup': { #allow alternate lookup by email
        'url': 'regex("[\w@.+]+")',
        'field': 'email'
    },
    'resource_methods': ['GET'],
    'embedding': True,
    'datasource': {
        'projection': {'auth_hash': 0, 'roles': 0}
    },
    'restrict_update': 'email',
    'schema': {
        'name': { 'type': 'string' },
        'email': {
            'type':'string',
            'unique': True,
            'required': True
        },
        'roles': {
            'type':'list',
            'items': [{'type': 'string', 'allowed': ['admin', 'user']}]
        },
        'auth_hash': { 'type': 'string' }
    }
}

applications = {
    'additional_lookup': {
        'url': 'regex("[\w]+")',
        'field': 'name'
    },
    'embedding': True,

    'schema': {
        'name': {
            'type': 'string',
            'unique': True
        }
    }
}

tools = {
    'embedding': True,
    'schema': {
        'name': {'type': 'string'},
        'application': {
            'type': 'objectid',
            'data_relation': {
                'resource': 'applications',
                'field': 'name',
            },
        }
    }
}

usages = {
    'restrict_update':'user',
    'creator': 'user',
    'schema': {
        'tool': {
            'type': 'objectid',
            'data_relation': {
                'resource': 'tools',
                'field': '_id',
            }
        },
        'user': {
            'type': 'string',
            'data_relation': {
                'resource': 'users',
                'field': 'email',
            }
        },
        'details': {'type': 'dict'}
    }
}

notifications = {
    'item_title': 'notification',
    'restrict_update': ['recipient', 'sender'],
    'restrict_read': ['recipient', 'sender'],
    'creator': 'sender',
    'schema': {
        'recipient': {
            'type': 'string',
            'data_relation': {
                'resource': 'users',
                'field': 'email',
            }
        },
        'sender': {
            'type': 'string',
            'data_relation': {
                'resource': 'users',
                'field': 'email',
            }
        },
        'message': { 'type': 'string' },
        'application': {
            'type': 'string',
            'data_relation': {
                'resource': 'applications',
                'field': 'name',
            }
        },
        'tool': {
            'type': 'objectid',
            'data_relation': {
                'resource': 'tools',
                'field': '_id',
            }
        },
        'type': { 'type': 'string' },
        'status': { 'type': 'string' }
    }
}

clips = {
    'creator': 'user', #store the creating user's email in the 'user' field
    'restrict_update': 'user', #only the creator can update/delete the clip
    'schema': {
        'name': {'type': 'string'},
        'user': {
            'type': 'string',
            'data_relation': {
                'resource': 'users',
                'field': 'email',
            }
        },
        'tool': {
            'type': 'objectid',
            'data_relation': {
                'resource': 'tools',
                'field': '_id',
            }
        },
        'share': {
            'type': 'list',
            'schema': {
                'type': 'string',
                'or': [{
                    'data_relation': {
                        'resource': 'users',
                        'field': 'email'
                    },
                }, {
                    'allowed': ['public']
                }]
            }
        },
        'type': {
            'type': 'string',
            'allowed': ['mouse', 'keyboard']
        },
        'event_frames': {
            'type': 'list',
            'items': [{'type': 'integer'}],
            'default': [25]
        },
    }
}

ratings = {
    'restrict_update': 'user',
    'creator': 'user',
    'unique': ['user', 'clip'],
    'schema': {
        'clip': {
            'type': 'objectid',
            'data_relation': {
                'resource': 'clips',
                'field': '_id',
            },
        },
        'user': {
            'type': 'string',
            'data_relation': {
                'resource': 'users',
                'field': 'email',
            }
        },
        'value': {'type': 'integer'}
    }
}

images = {
    'url': 'clips/<regex("[a-f0-9]{24}"):clip>/images',
    'additional_lookup': {
        'url': 'regex("[\w@.+]+")',
        'field': 'name'
    },
    'restrict_update': 'user',
    'creator': 'user',
    'schema': {
        'name': {'type': 'string'},
        'data': {'type': 'media'},
        'clip': {
            'type': 'objectid',
            'data_relation': {
                'resource': 'clips',
                'field': '_id',
            },
        },
        'user': {
            'type': 'string',
            'data_relation': {
                'resource': 'users',
                'field': 'email',
            }
        },
    }
}

DOMAIN = {
    'users': users,
    'applications': applications,
    'tools': tools,
    'usages': usages,
    'notifications': notifications,
    'clips': clips,
    'ratings': ratings,
    'images': images,
}
