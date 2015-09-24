import webapp2
from google.appengine.api import images
from google.appengine.api import users
from google.appengine.ext import ndb

HEAD = """\
<html>
  <body>
    <h3>Connexus</h3>
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
      self.redirect('/manage')
    else:
      self.redirect(users.create_login_url(self.request.uri))

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
      self.redirect('/manage')

  def get(self):
    PAGE = HEAD + "<b>Streams I own</b><br>"
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
    PAGE = HEAD + """\
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
    PAGE = HEAD + stream_name
    PAGE += "<form action=/view?stream=" + stream_name + """\
      "enctype="multipart/form-data" method="post">
        <div><textarea name="comment" rows="3" cols="60">comment</textarea></div>
        <div><label>image:</label></div>
        <div><input type="file" name="img"/></div>
        <div><input type="submit" value="Upload"></div>
      </form>
      """

    PAGE += TAIL

    self.response.write(PAGE)

class ViewAll(webapp2.RequestHandler):
  def get(self):
    PAGE = HEAD + "<b>View All Streams</b>" + TAIL

class Search(webapp2.RequestHandler):
  pass

class Trending(webapp2.RequestHandler):
  pass

class Error(webapp2.RequestHandler):
  pass



app = webapp2.WSGIApplication([
  ('/', Login),
  ('/manage', Manage),
  ('/create', Create),
  ('/view', View),
  ('/viewall', ViewAll),
  ('/search', Search),
  ('/trending', Trending),
  ('/error', Error)
], debug=True)
