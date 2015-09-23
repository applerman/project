import webapp2
from google.appengine.api import images
from google.appengine.api import users
from google.appengine.ext import ndb

##############
# Data Model
##############
class Picture(ndb.Model):
  stream_id = ndb.StringProperty(indexed=True)
  blob_key = ndb.BlobKeyProperty()
  comment = ndb.StringProperty()

class Stream(ndb.Model):
  creator_id = ndb.StringProperty(indexed=True)
  name = ndb.StringProperty(indexed=True)
  last_updated_date = ndb.DateTimeProperty()
  created_date = ndb.DateTimeProperty(auto_now_add=True)
  num_pictures = ndb.IntegerProperty()
  num_views = ndb.IntegerProperty()
  tag = ndb.StringProperty(repeated=True)
  cover_img_url = ndb.StringProperty()

class User(ndb.Model):
  identity = ndb.StringProperty(indexed=True)
  subscriptions = ndb.StringProperty(repeated=True)

##############
# Handlers
##############

class Login(webapp2.RequestHandler):
  def get(self):
    # Checks for active Google account session
    user = users.get_current_user()

    if user:
      self.redirect('/management')
    else:
      self.redirect(users.create_login_url(self.request.uri))

class Management(webapp2.RequestHandler):
  def get(self):
    self.response.write('<html><body>You wrote:<pre>')
    self.response.write('Hi!')
    self.response.write('</pre></body></html>')

class Create(webapp2.RequestHandler):
  pass

class View(webapp2.RequestHandler):
  pass

class ViewAll(webapp2.RequestHandler):
  pass

class Search(webapp2.RequestHandler):
  pass

class Trending(webapp2.RequestHandler):
  pass

class Error(webapp2.RequestHandler):
  pass



app = webapp2.WSGIApplication([
  ('/', Login),
  ('/management', Management),
  ('/create', Create),
  ('/view', View),
  ('/viewall', ViewAll),
  ('/search', Search),
  ('/trending', Trending),
  ('/error', Error)
], debug=True)
