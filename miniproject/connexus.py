import datetime 
import urllib
import webapp2
from google.appengine.api import images
from google.appengine.api import search
from google.appengine.api import mail
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

# For Trend
class CountInHour(ndb.Model):

  stream_id = ndb.StringProperty(indexed=True)
  count = ndb.IntegerProperty(indexed=True, default=0)
  viewLogs = ndb.DateTimeProperty(repeated=True)

  def view(self):
    self.viewLogs.append(datetime.datetime.now())
    self.cleanOldViews()
    self.count = len(self.viewLogs)

  def cleanOldViews(self):
    
    now = datetime.datetime.now()
    deltaHour = datetime.timedelta(hours=1)
    newFront = 0

    for i in range(len(self.viewLogs)):
      if deltaHour < (now - self.viewLogs[i]):
        newFront = i + 1
      else:
        break

    self.viewLogs = self.viewLogs[newFront:]
    self.count = len(self.viewLogs)

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

class Manage(webapp2.RequestHandler):
  def post(self):
    if self.request.get('create'):
      stream_name = self.request.get('name')
      if Stream.query(Stream.name == stream_name).fetch(1):
        self.redirect('/error?%s' % (urllib.urlencode({'problem': 'already has stream name ' + stream_name})))
      else:
        stream = Stream()
        stream.creator_id = users.get_current_user().user_id()
        stream.name = stream_name
        stream.num_pictures = 0
        stream.num_views = 0
        # TODO Need to handle tag format
        stream.tag = self.request.get('tag').strip().split(',')
        stream.cover_img_url = self.request.get('cover_img_url')
        stream.put()

        subscribers = self.request.get('subscribers').strip().split(',')
        message = self.request.get('message')

        for subscriber in subscribers:
          if subscriber:
            mail.send_mail(sender=users.get_current_user().email(),
                           to=subscriber,
                           subject="Invite to the stream",
                           body=message
                          )

        # For Trend
        tempCountInHour = CountInHour()
        tempCountInHour.stream_id = stream_name
        tempCountInHour.put()

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

    elif self.request.get('delete_own_streams'):
      stream_names = self.request.get_all('streams_deleted')
      for stream_name in stream_names:
        stream = Stream.query(Stream.name == stream_name).fetch(1)
        if stream:
          index = search.Index(name="myIndex")
          try:
              results = index.search(stream_name) 

              # Iterate over the documents in the results
              for scored_document in results:
                # handle results
                if stream_name == scored_document.fields[0].value:
                  temp_doc_id = scored_document.doc_id
                  index.delete(temp_doc_id)
          except search.Error:
              pass # print "Fail in searching in the Index"

          # For Trend
          currentCountInHour = CountInHour.query(CountInHour.stream_id == stream_name).fetch(1)
          if currentCountInHour:
            currentCountInHour[0].key.delete()

          stream[0].key.delete()
        # Delete pictures in the stream
        pictures = Picture.query(Picture.stream_id == stream_name)
        for picture in pictures:
          picture.key.delete()
      self.redirect('/manage')

    elif self.request.get('unsubscribed_streams'):
      cur_user = User.query(User.identity == users.get_current_user().user_id()).fetch(1)
      if cur_user:
        stream_names = self.request.get_all('streams_unsubscribed')
        for stream_name in stream_names:
          cur_user[0].subscriptions.remove(stream_name)
        cur_user[0].put()
      self.redirect('/manage')


  def get(self):
    # TODO make it a table?
    user = users.get_current_user()
    PAGE = HEAD % (user.nickname(), users.create_logout_url('/'))
    PAGE += "<b>Streams I own</b><br>Name | Last New Picture | Number of Pictures | Delete<br>"
    streams_i_own = Stream.query(Stream.creator_id ==
                                 users.get_current_user().user_id()).order(-Stream.created_date)
    PAGE += "<form action=\"/manage\" method=\"post\">"
    for stream in streams_i_own:
      PAGE += "<a href=/view?%s>%s</a> | " % (urllib.urlencode({'stream': stream.name}), stream.name)
      PAGE += str(stream.last_updated_date.date()) + ' | '
      PAGE += str(stream.num_pictures) + ' | '
      PAGE += "<input type=\"checkbox\" name=\"streams_deleted\" value=\"%s\"><br>" % stream.name
    PAGE += "<input type=\"submit\" value=\"Delete\" name=\"delete_own_streams\">"
    PAGE += "</form>"

    PAGE += "<br>"
    PAGE += "<b>Streams I subscribe to</b><br>Name | Last New Picture | Number of Pictures | Views | Delete<br>"
    PAGE += "<form action=\"/manage\" method=\"post\">"
    cur_user = User.query(User.identity == users.get_current_user().user_id()).fetch(1)
    if cur_user:
      for stream_name in cur_user[0].subscriptions:
        stream = Stream.query(Stream.name == stream_name).fetch(1)
        if stream:
          stream = stream[0]
          PAGE += "<a href=/view?%s>%s</a> | " % (urllib.urlencode({'stream': stream.name}), stream.name)
          PAGE += str(stream.last_updated_date.date()) + ' | '
          PAGE += str(stream.num_pictures) + ' | '
          PAGE += str(stream.num_views) + ' | '
          PAGE += "<input type=\"checkbox\" name=\"streams_unsubscribed\" value=\"%s\"><br>" % stream.name
        else:
          pass
          #cur_user[0].subscriptions.remove(stream_name)
          # TODO delete entry, might occur bugs here

    PAGE += "<input type=\"submit\" value=\"Delete\" name=\"unsubscribed_streams\">"
    PAGE += "</form>"
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
    stream_name = self.request.get('stream')
    if self.request.get('upload'):
      # Store image
      stream = Stream.query(Stream.name == stream_name).fetch(1)
      if stream and self.request.get('img'):
        picture = Picture()
        picture.stream_id = stream_name
        picture.image = self.request.get('img')
        picture.comment = self.request.get('comment')
        picture.put()
        stream[0].last_updated_date = datetime.datetime.now()
        stream[0].num_pictures += 1
        stream[0].put()

    elif self.request.get('subscribe'):
      stream = Stream.query(Stream.name == stream_name).fetch(1)
      if stream:
        cur_user = User.query(User.identity == users.get_current_user().user_id()).fetch(1)
        if not cur_user:
          cur_user = User()
          cur_user.identity = users.get_current_user().user_id()
        else:
          cur_user = cur_user[0]
        if stream[0].name not in cur_user.subscriptions:
          cur_user.subscriptions.append(stream[0].name)
        cur_user.put()

    self.redirect('/view?%s' % urllib.urlencode({'stream': stream_name}))


  def get(self):
    stream_name = self.request.get('stream')
    if stream_name:
      stream = Stream.query(Stream.name == stream_name).fetch(1)
      if stream:
        stream = stream[0]
        stream.num_views += 1
        stream.put()

        # For Trend
        currentCountInHour = CountInHour.query(CountInHour.stream_id == stream_name).fetch(1)[0]
        currentCountInHour.view()
        currentCountInHour.put()


        user = users.get_current_user()
        PAGE = HEAD % (user.nickname(), users.create_logout_url('/'))

        PAGE += "<b>%s</b><br>" % stream_name

        pictures = Picture.query(Picture.stream_id == stream_name).order(-Picture.created_date)
        for pic in pictures:
          PAGE += ('<a href=/img?img_id=%s><img src="/img?img_id=%s"></img></a>' % (pic.key.urlsafe(),pic.key.urlsafe()))

        PAGE += """\
      <form action="/view?%s" enctype="multipart/form-data" method="post">
        <div><textarea name="comment" rows="3" cols="60">comment</textarea></div>
        <div><label>image:</label></div>
        <div><input type="file" name="img"/></div>
        <div><input type="submit" name="upload"></div>
      </form> """ % (urllib.urlencode({'stream': stream_name}))

        PAGE += """\
      <form action="/view?%s" method="post">
        <input type="submit" value="Subscribe" name="subscribe">
      </form> """ % (urllib.urlencode({'stream': stream_name}))
        PAGE += TAIL
        self.response.write(PAGE)
      else:
        self.redirect('/error?%s' % (urllib.urlencode({'problem': 'no such stream name ' + stream_name})))

    else:
      user = users.get_current_user()
      PAGE = HEAD % (user.nickname(), users.create_logout_url('/'))
      PAGE += "<b>View All Streams</b><br>"
      streams = Stream.query().order(Stream.created_date)
      for stream in streams:
        PAGE += "<a href=/view?%s>%s</a><br>" % (urllib.urlencode({'stream': stream.name}), stream.name)
        PAGE += ('<a href=/view?%s><img src="%s", width="64"></img><a><br>' % (urllib.urlencode({'stream': stream.name}), stream.cover_img_url))

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
          PAGE += "<br><b>%d Results Found (Showing only top 5)</b><br>" % (count)
          showCount = 0

          # Iterate over the documents in the results
          for scored_document in results:
              # handle results
              if Stream.query(Stream.name == scored_document.fields[0].value).fetch(1):
                stream = Stream.query(Stream.name == scored_document.fields[0].value).fetch(1)[0]
                PAGE += "<a href=/view?%s>%s</a><br>" % (urllib.urlencode({'stream': stream.name}), stream.name)
                PAGE += ('<a href=/view?%s><img src="%s", width="64"></img><a><br>' % (urllib.urlencode({'stream': stream.name}), stream.cover_img_url))

              showCount += 1
              if showCount == 5:
                break;

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
    problem = self.request.get('problem')
    PAGE += "<b>Error</b><br>" + problem + TAIL
    self.response.write(PAGE)

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

# For Trend
class Cron(webapp2.RequestHandler):
  def get(self):
    
    tempsCountInHour = CountInHour.query()
    for tempCountInHour in tempsCountInHour:
      tempCountInHour.cleanOldViews()
      tempCountInHour.put()

    currentTop3Streams = []

    top3CountInHour = CountInHour.query().order(-CountInHour.count).fetch(3)
    for i in range(3):
      if top3CountInHour[i]:
        topItem = {
          "stream_id": top3CountInHour[i].stream_id,
          "count": top3CountInHour[i].count
        }
        currentTop3Streams.append(topItem)
    
    memcache.set('currentTop3Streams', currentTop3Streams)

    digestData = memcache.get('digest')
    if digestData is None:
      digestData = {"count": 0, "fequency": 0}
    if digestData.get("count") is None:
      digestData["count"] = 0
    if digestData.get("fequency") is None:
      digestData["fequency"] = 0
    
    count = digestData["count"]
    fequency = digestData["fequency"]

    if ( (count % fequency) == 0  and (fequency != 0) ):

      messageBody = "Digest:"
      for item in currentTop3Streams:
        messageBody += "\n" + item["stream_id"] + ": " + str(item["count"])
      messageBody += "\n"

      mail.send_mail(sender="eugenegx@gmail.com",
                     to="eugenegx@gmail.com",
                     subject="Digest",
                     body=messageBody
                    )
    
    digestData["count"] += 1
    memcache.set('digest', digestData)


app = webapp2.WSGIApplication([
  ('/', Login),
  ('/manage', Manage),
  ('/create', Create),
  ('/view', View),
  ('/search', Search),
  ('/trending', Trending),
  ('/social', Social),
  ('/error', Error),
  ('/img', Image),
  ('/cron', Cron)
], debug=True)
