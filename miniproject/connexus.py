import urllib
import webapp2
from google.appengine.api import images
from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.api import search


HEAD = """\
<html>
  <body>
    <h3>Connexus.us Welcome, %s! (<a href="%s">sign out</a>)</h3>
    <a href="manage">Manage</a> |
    <a href="create">Create</a> |
    <a href="view">View</a> |
    <a href="search">Search</a> |
    <a href="trending">Trending</a> |
    <a href="social">Social</a>
    <hr>
"""

TAIL = """
  </body>
</html>
"""

showSearchResults = False

##############
# Data Model
##############
class Picture(ndb.Model):
  stream_id = ndb.StringProperty(indexed=True)
  image = ndb.BlobProperty()
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
      user = users.get_current_user()
      if user:
          self.redirect('/manage')
      else:
          greeting = ('<a href="%s">Sign in or register</a>.' % users.create_login_url('/'))
          self.response.out.write('<html><body> %s </body></html>' % greeting)

  #   if user:
  #     self.redirect('/manage')
  #   else:
  #     self.redirect(users.create_login_url(self.request.uri))

class Manage(webapp2.RequestHandler):
  def post(self):
      # When Create Page submits, executes the following code.
      stream = Stream()
      stream.creator_id = users.get_current_user().user_id()
      stream.name = self.request.get('name')
      stream.num_pictures = 0
      stream.num_views = 0
      # TODO Handle Tag Format
      stream.tag = self.request.get('tag').split(',')
      stream.cover_img_url = self.request.get('cover_img_url')
      stream.put()

      # Create the Document of current stream for search
      currentDocument = search.Document(
      fields=[
         search.TextField(name='name', value=self.request.get('name')),
         search.TextField(name='tag', value=self.request.get('tag')),
         ])

      # Put in Index
      try:
        index = search.Index(name="myIndex")
        index.put(currentDocument)
      except search.Error:
        print "Fail in putting in the Index" #logging.exception('Put failed')

      self.redirect('/manage')

  def get(self):
    user = users.get_current_user()
    PAGE = HEAD % (user.nickname(), users.create_logout_url('/'))
    PAGE += "<b>Streams I own</b><br>"
    streams_i_own = Stream.query(Stream.creator_id ==
                                 users.get_current_user().user_id()).order(-Stream.created_date)
    for stream in streams_i_own:
      PAGE += "|" + stream.name
    PAGE += "<br>"
    PAGE += "<b>Streams I subscribe to</b>"
    user = User.query(User.identity == users.get_current_user().user_id())
    # TODO handle subscription
      
    PAGE += "</body></html>"
    self.response.write(PAGE)


class Create(webapp2.RequestHandler):
  def get(self):

    user = users.get_current_user()
    PAGE = HEAD % (user.nickname(), users.create_logout_url('/'))
    PAGE += """\
    <form action="/manage" method="post">
      <div>Name your stream</div>
      <div><input value="" name="name"></div>
      <div>Add subscribers</div>
      <div><textarea name="subscribers" rows="3" cols="60"></textarea></div>
      <div><textarea name="message" rows="3" cols="60">Optional message for invite</textarea></div>
      <div>Tag your stream</div>
      <div><textarea name="tag" rows="3" cols="60"></textarea></div>
      <div>URL to cover image (Can be empty)</div>
      <div><input value="" name="cover_img_url"></div>
      <div><input type="submit" value="Create Streams"></div>
    </form>
    """ + TAIL
    self.response.write(PAGE)

class View(webapp2.RequestHandler):
  def post(self):
    # TODO store image, and update ...
    pass

  def get(self):
    stream_name = self.request.get('stream')
    # TODO find stream using stream_name, and print pictures
    user = users.get_current_user()
    PAGE = HEAD % (user.nickname(), users.create_logout_url('/'))
    PAGE += """
      <b>%s</b>
      <form action="/view?%s" enctype="multipart/form-data" method="post">
        <div><textarea name="comment" rows="3" cols="60">comment</textarea></div>
        <div><label>image:</label></div>
        <div><input type="file" name="img"/></div>
        <div><input type="submit" value="Upload"></div>
      </form>
      """ % (stream_name, urllib.urlencode({'stream': stream_name}))
    PAGE += TAIL

    self.response.write(PAGE)

class ViewAll(webapp2.RequestHandler):
  def get(self):
    user = users.get_current_user()
    PAGE = HEAD % (user.nickname(), users.create_logout_url('/'))
    PAGE += "<b>View All Streams</b>" + TAIL
    self.response.write(PAGE)

class Search(webapp2.RequestHandler):
  def post(self):
    self.redirect('/search?show==True')

  def get(self):
    user = users.get_current_user()
    PAGE = HEAD % (user.nickname(), users.create_logout_url('/'))
    PAGE += "<b>Search</b>"

    PAGE += """
      <form action="/search" enctype="multipart/form-data" method="post">
        <div><textarea name="queryString" rows="3" cols="60">Search name or tags</textarea></div>
        <div><input type="submit" value="Search"></div>
      </form>
      """ 

    if self.request.get("show"):
      PAGE += "<b>Show Search Results</b>"

    PAGE += TAIL
    self.response.write(PAGE)

class Trending(webapp2.RequestHandler):
  def get(self):
    user = users.get_current_user()
    PAGE = HEAD % (user.nickname(), users.create_logout_url('/'))
    PAGE += "<b>Trending</b>" + TAIL
    self.response.write(PAGE)
  # pass

class Error(webapp2.RequestHandler):
  def get(self):
    user = users.get_current_user()
    PAGE = HEAD % (user.nickname(), users.create_logout_url('/'))
    PAGE += "<b>Error</b>" + TAIL
    self.response.write(PAGE)
  # pass

class Social(webapp2.RequestHandler):
  def get(self):
    user = users.get_current_user()
    PAGE = HEAD % (user.nickname(), users.create_logout_url('/'))
    PAGE += "<b>Social</b>" + TAIL
    self.response.write(PAGE)


app = webapp2.WSGIApplication([
  ('/', Login),
  ('/manage', Manage),
  ('/create', Create),
  ('/view', ViewAll),
  ('/viewall', ViewAll),
  ('/search', Search),
  ('/trending', Trending),
  ('/social', Social),
  ('/error', Error)
], debug=True)
