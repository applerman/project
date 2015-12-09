import cgi
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import webapp2

##############
# Data Model
##############
class Picture(ndb.Model):  
  stream_id = ndb.StringProperty(indexed=True)
  created_date = ndb.DateTimeProperty(auto_now_add=True)
  date = ndb.DateProperty(auto_now_add=True)
  image = ndb.BlobProperty()
  caption = ndb.StringProperty()
  geo = ndb.GeoPtProperty()

class Stream(ndb.Model):
  creator_id = ndb.StringProperty(indexed=True)
  name = ndb.StringProperty(indexed=True)
  last_updated_date = ndb.DateTimeProperty(auto_now_add=True)
  created_date = ndb.DateTimeProperty(auto_now_add=True)
  num_pictures = ndb.IntegerProperty()
  num_views = ndb.IntegerProperty()
  tag = ndb.StringProperty(repeated=True)
  cover_img_url = ndb.StringProperty()
  time_stamp = ndb.DateTimeProperty(repeated=True)

class User(ndb.Model):
  identity = ndb.StringProperty(indexed=True)
  email = ndb.StringProperty(indexed=True)
  subscriptions = ndb.StringProperty(repeated=True)
  trending_report = ndb.StringProperty(indexed=True)

##############
# Handlers
##############

app = webapp2.WSGIApplication([
  ('/', Login)
], debug=True)
