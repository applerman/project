import datetime 
import urllib
import webapp2
from google.appengine.api import images
from google.appengine.api import search
from google.appengine.api import users
from google.appengine.ext import ndb


HEAD = """\
<html>
  <body>
    <h3>Connex.us</h3>
    Welcome, %s! (<a href="%s">sign out</a>)<br>
    <a href="manage">Manage</a> |
    <a href="create">Create</a> |
    <a href="view">View</a> |
    <a href="search">Search</a> |
    <a href="trending">Trending</a> |
    <a href="social">Social</a>
    <hr>
"""

TAIL = """\
  </body>
</html>
"""

showSearchResults = False

##############
# Data Model
##############
class Picture(ndb.Model):  
  stream_id = ndb.StringProperty(indexed=True)
  created_date = ndb.DateTimeProperty(auto_now_add=True)
  image = ndb.BlobProperty()
  comment = ndb.StringProperty()

class Stream(ndb.Model):
  creator_id = ndb.StringProperty(indexed=True)
  name = ndb.StringProperty(indexed=True)
  last_updated_date = ndb.DateTimeProperty(auto_now_add=True)
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
    if self.request.get('create'):
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
        index = search.Index(name='myIndex')
        index.put(currentDocument)
      except search.Error:
        pass #print "Fail in putting in the Index" #

      self.redirect('/manage')
  #TODO


  def get(self):
    # TODO make it a table?
    user = users.get_current_user()
    PAGE = HEAD % (user.nickname(), users.create_logout_url('/'))
    PAGE += "<b>Streams I own</b><br>Name | Last New Picture | Number of Pictures <br>"
    streams_i_own = Stream.query(Stream.creator_id ==
                                 users.get_current_user().user_id()).order(-Stream.created_date)
    for stream in streams_i_own:
      PAGE += "<a href=/view?%s>%s</a> |" % (urllib.urlencode({'stream': stream.name}), stream.name)
      PAGE += str(stream.last_updated_date.date()) + '|'
      PAGE += str(stream.num_pictures) + '<br>'

    PAGE += "<br>"
    PAGE += "<b>Streams I subscribe to</b><br>Name | Last New Picture | Number of Pictures | Views <br>"
    cur_user = User.query(User.identity == users.get_current_user().user_id()).fetch(1)
    if cur_user:
      for stream_name in cur_user[0].subscriptions:
        stream = Stream.query(Stream.name == stream_name).fetch(1)[0]
        PAGE += "<a href=/view?%s>%s</a> | " % (urllib.urlencode({'stream': stream.name}), stream.name)
        PAGE += str(stream.last_updated_date.date()) + ' | '
        PAGE += str(stream.num_pictures) + ' | '
        PAGE += str(stream.num_views) + '<br>'

    # TODO handle delete
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
      <div><input type="submit" name="create"></div>
    </form>
    """ + TAIL
    self.response.write(PAGE)

class View(webapp2.RequestHandler):
  def post(self):
    if self.request.get('upload'):
      # TODO store image, and update ...
      picture = Picture()
      stream_name = self.request.get('stream')
      picture.stream_id = stream_name
      picture.image = self.request.get('img')
      picture.comment = self.request.get('comment')
      picture.put()

      stream = Stream.query(Stream.name == stream_name).fetch(1)[0]
      stream.last_updated_date = datetime.datetime.now()
      stream.num_pictures += 1
      stream.put()

    if self.request.get('subscribe'):
      stream_name = self.request.get('stream')
      stream = Stream.query(Stream.name == stream_name).fetch(1)[0]
      cur_user = User.query(User.identity == users.get_current_user().user_id()).fetch(1)
      if not cur_user:
        cur_user = User()
        cur_user.identity = users.get_current_user().user_id()

      cur_user.subscriptions.append(stream.name)
      cur_user.put()

    self.redirect('/view?%s' % urllib.urlencode({'stream': stream_name}))


  def get(self):
    stream_name = self.request.get('stream')
    if stream_name:
      stream = Stream.query(Stream.name == stream_name).fetch(1)[0]
      stream.num_views += 1
      stream.put()

      user = users.get_current_user()
      PAGE = HEAD % (user.nickname(), users.create_logout_url('/'))

      PAGE += "<b>%s</b><br>" % stream_name

      pictures = Picture.query(Picture.stream_id == stream_name).order(Picture.created_date)
      for pic in pictures:
        PAGE += ('<img src="/img?img_id=%s"></img>' % pic.key.urlsafe())

      PAGE += """\
    <form action="/view?%s" enctype="multipart/form-data" method="post">
      <div><textarea name="comment" rows="3" cols="60">comment</textarea></div>
      <div><label>image:</label></div>
      <div><input type="file" name="img"/></div>
      <div><input type="submit" name="upload"></div>
    </form> """ % (urllib.urlencode({'stream': stream_name}))

      PAGE += """\
    <form action="/view?%s" enctype="multipart/form-data" method="post">
      Subscribe
      <div><input type="submit" name="subscribe"></div>
    </form> """ % (urllib.urlencode({'stream': stream_name}))
      PAGE += TAIL

      self.response.write(PAGE)

    else:
      user = users.get_current_user()
      PAGE = HEAD % (user.nickname(), users.create_logout_url('/'))
      PAGE += "<b>View All Streams</b><br>"
      streams = Stream.query()
      for stream in streams:
        PAGE += "<a href=/view?%s>%s</a><br>" % (urllib.urlencode({'stream': stream.name}), stream.name)
        PAGE += ('<img src="%s"></img><br>' % stream.cover_img_url)

      PAGE += TAIL
      self.response.write(PAGE)

class Search(webapp2.RequestHandler):
  def post(self):
    query_params = {'show': self.request.get('queryString')}
    self.redirect('/search?' + urllib.urlencode(query_params))

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
      queryString = self.request.get('show')
      PAGE += "<b>Show Search Results: %s</b>" % (queryString)

      index = search.Index(name="myIndex")
      try:
          results = index.search(queryString) 

          count = results.number_found
          PAGE += "<br><b>Results Count: %d</b>" % (count)

          # Iterate over the documents in the results
          for scored_document in results:
              # handle results
              PAGE += "<br><b>%s</b>" % (scored_document.fields[0].value)

      except search.Error:
          pass # print "Fail in searching in the Index"

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

class Image(webapp2.RequestHandler):
  def get(self):
    picture_key = ndb.Key(urlsafe=self.request.get('img_id'))
    picture = picture_key.get()
    if picture.image:
      self.response.headers['Content-Type'] = 'image/gif'
      self.response.out.write(images.resize(picture.image, height=64, allow_stretch=False))
    else:
      self.response.out.write('No image')


app = webapp2.WSGIApplication([
  ('/', Login),
  ('/manage', Manage),
  ('/create', Create),
  ('/view', View),
  ('/search', Search),
  ('/trending', Trending),
  ('/social', Social),
  ('/error', Error),
  ('/img', Image)
], debug=True)
