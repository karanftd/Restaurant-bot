''''from google.appengine.ext import ndb

class Booking(ndb.model):
    
    name = ndb.StringProperty()
    person = ndb.IntegerProperty()
    user_id = ndb.StringProperty()
    chat_id = ndb.StringProperty()
    table = ndb.StringProperty()
    email = ndb.StringProperty()
    time = ndb.StringProperty()
'''
class Booking():
    
    name = None
    person = None
    user_id = None
    chat_id = None
    table = None
    email = None
    time = None
