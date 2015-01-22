DEBUG=True

MONGO_HOST = 'localhost'
MONGO_PORT = 27017
MONGO_USERNAME = 'eve'
MONGO_PASSWORD = 'api service access'
MONGO_DBNAME = 'socaster'

X_DOMAINS = "*"
X_HEADERS = ['Authorization', 'Content-Type', 'If-Match']

RESOURCE_METHODS = ['GET', 'POST', 'DELETE']
ITEM_METHODS = ['GET', 'PATCH', 'PUT', 'DELETE']

EMBEDDING = True
PAGINATION = False
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
            'schema': {
                'type': 'string',
                'allowed': ['admin', 'user']
            }
        },
        'auth_hash': { 'type': 'string' }
    }
}

applications = {
    'additional_lookup': {
        'url': 'regex("[\w]+")',
        'field': 'name'
    },

    'schema': {
        'name': {
            'type': 'string',
            'unique': True
        },
        'icon': {'type': 'media'},
    }
}

tools = {
    'schema': {
        'name': {'type': 'string'},
        'users': {
            'type': 'list',
            'schema': {
                'type': 'string',
                'data_relation': {
                    'resource': 'users',
                    'field': 'email',
                }
            }
        },
        'application': {
            'type': 'string',
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
    'unique': ['tool', 'user'],
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
        'keyboard': {
            'type': 'integer',
            'default': 0
        },
        'mouse': {
            'type': 'integer',
            'default': 0
        }
    }
}

notifications = {
    'item_title': 'notification',
    'restrict_update': ['recipient', 'sender'],
    'restrict_access': ['recipient', 'sender'],
    'creator': 'sender',
    'schema': {
        'recipient': {
            'type': 'objectid',
            'data_relation': {
                'resource': 'users',
                'field': '_id',
                'embeddable': True,
            },
        },
        'sender': {
            'type': 'objectid',
            'data_relation': {
                'resource': 'users',
                'field': '_id',
                'embeddable': True,
            },
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
                'embeddable': True,
            },
        },
        'type': { 'type': 'string' },
        'notification_status': { 'type': 'string', 'default': "new" }
    }
}

clips = {
    'creator': 'user', #store the creating user's email in the 'user' field
    'restrict_update': 'user', #only the creator can update/delete the clip
    'restrict_access': ['share'],
    'additional_lookup': { #allow alternate lookup by email
        'url': 'regex("[\w@.+]+")',
        'field': 'name'
    },
    'embedded_fields': ['thumbnail'],
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
                'embeddable': True
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
        'frames': {
            'type': 'list',
            'schema': {'type': 'string'}
        },
        'event_frames': {
            'type': 'list',
            'schema': {
                'type': 'integer',
            },
        },
        'thumbnail': { 
            'type': 'objectid',
            'data_relation': {
                'resource': 'images',
                'field': '_id',
                'embeddable': True,
            },
        }
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
                'embeddable' : 'true'
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
    'embeddable': True,
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

events = {
    'schema': {
        'application': { 'type': 'string', 'required' :'True' },
        'tool': { 'type': 'string', 'required' :'True' },
		'other': {'type' : 'string', 'default': ''},
        #Remaining fields match UBC Recommender requirements
        "user_id" : {
            'type': 'string',
            'data_relation': {
                'resource': 'users',
                'field': 'email',
            }
        },
        "what" : {'type': 'string', 'default': 'executed'},
        "kind" : {'type': 'string', 'default': 'command'},
        "description" : {'type': 'objectid'}, #submitted as application and tool, but translated in hook
        "bindingUsed" : {'type': 'boolean', 'default': False},
        "time" : {'type': 'integer', 'default': 0},
        "bundleVersion" : {'type': 'string', 'default': 'faked'}
    }
}

user_tools = {
    'restrict_access': ['user'],
    'resource_methods': ['GET'],
    'item_methods': ['GET'],
    'schema': {
        #matches tool schema, plus tool_id for reference
        'tool_id': {
            'type': 'objectid',
            'data_relation': {
                'resource': 'tools',
                'field': '_id',
                'embeddable': True
            }
        },
        'application': { 'type': 'string' },
        'name': { 'type': 'string' },
        'users': {
            'type': 'list',
            'schema': {
                'type': 'string',
                'data_relation': {
                    'resource': 'users',
                    'field': 'email',
                }
            }
        },

        #belongs to a specific user, for recommendations
        'user' : {
            'type': 'string',
            'data_relation': {
                'resource': 'users',
                'field': 'email',
            }
        },
        'recommendations': {
            'type': 'dict'
        }
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
    'events': events,
    'user_tools': user_tools,
}
