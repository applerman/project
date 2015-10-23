import os
import datetime 
import urllib
import webapp2
import jinja2
import json
import random
from google.appengine.api import images
from google.appengine.api import search
from google.appengine.api import mail
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import ndb

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

HEAD = """\
<html>
  <head>
    %s
    <meta charset="utf-8">
    <link href="css/bootstrap.min.css" rel="stylesheet">
  </head>
  <body>
    <script src="js/bootstrap.min.js"></script>
    <h3>Connex.us</h3>
    Welcome, %s! (<a href="%s">sign out</a>)<br><br>
    <a class="btn btn-default" href="manage">Manage</a>
    <a class="btn btn-default" href="create">Create</a>
    <a class="btn btn-default" href="view">View</a>
    <a class="btn btn-default" href="search">Search</a>
    <a class="btn btn-default" href="trending">Trending</a>
    <a class="btn btn-default" href="social">Social</a>
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
  email = ndb.StringProperty()
  subscriptions = ndb.StringProperty(repeated=True)
  trending_report = ndb.StringProperty(indexed=True)

##############
# Handlers
##############

class Login(webapp2.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      self.redirect('/manage')
    else:
      greeting = '<h4>Welcome to Connexus!</h4>'
      greeting += '<a href="%s">Sign in or register</a>.' % users.create_login_url('/')
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
    user = users.get_current_user()
    if not user:
      self.redirect('/')
      return
    HEAD_CONTENT = ''
    PAGE = HEAD % (HEAD_CONTENT, user.nickname(), users.create_logout_url('/'))
    PAGE += "<h4><b>Streams I own</b></h4>"
    PAGE += "<form action=\"/manage\" method=\"post\">"
    PAGE += "<table class=\"table table-striped\">"
    PAGE += "<tr><th>Name</th><th>Last New Picture</th><th>Number of Pictures</th><th>Delete</th><tr>"
    streams_i_own = Stream.query(Stream.creator_id ==
                                 users.get_current_user().user_id()).order(-Stream.created_date)
    for stream in streams_i_own:
      PAGE += "<tr>"
      PAGE += "<td><a href=/view?%s>%s</a></td>" % (urllib.urlencode({'stream': stream.name}), stream.name)
      PAGE += "<td>" + str(stream.last_updated_date.date()) + "</td>"
      PAGE += "<td>" + str(stream.num_pictures) + "</td>"
      PAGE += "<td><input type=\"checkbox\" name=\"streams_deleted\" value=\"%s\"></td>" % stream.name
      PAGE += "</tr>"
    PAGE += "</table>"
    PAGE += "<input type=\"submit\" value=\"Delete\" class=\"btn btn-primary\" name=\"delete_own_streams\">"
    PAGE += "</form>"

    PAGE += "<br>"
    PAGE += "<h4><b>Streams I subscribe to</b></h4>"
    PAGE += "<form action=\"/manage\" method=\"post\">"
    PAGE += "<table class=\"table table-striped\">"
    PAGE += "<tr><th>Name</th><th>Last New Picture</th><th>Number of Pictures</th><th>Views</th><th>Unsubscribe</th>"
    cur_user = User.query(User.identity == users.get_current_user().user_id()).fetch(1)
    if cur_user:
      for stream_name in cur_user[0].subscriptions:
        stream = Stream.query(Stream.name == stream_name).fetch(1)
        if stream:
          stream = stream[0]
          PAGE += "<tr>"
          PAGE += "<td><a href=/view?%s>%s</a></td>" % (urllib.urlencode({'stream': stream.name}), stream.name)
          PAGE += "<td>" + str(stream.last_updated_date.date()) + '</td>'
          PAGE += "<td>" + str(stream.num_pictures) + '</td>'
          PAGE += "<td>" + str(stream.num_views) + '</td>'
          PAGE += "<td><input type=\"checkbox\" name=\"streams_unsubscribed\" value=\"%s\"></td>" % stream.name
          PAGE += "</tr>"
        else:
          pass
          #cur_user[0].subscriptions.remove(stream_name)
          # TODO delete entry, might occur bugs here

    PAGE += "</table>"
    PAGE += "<input type=\"submit\" value=\"Unsubscribe\" class=\"btn btn-primary\" name=\"unsubscribed_streams\">"
    PAGE += "</form>"
    PAGE += TAIL
    self.response.write(PAGE)


class Create(webapp2.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if not user:
      self.redirect('/')
      return
    HEAD_CONTENT = ''
    PAGE = HEAD % (HEAD_CONTENT, user.nickname(), users.create_logout_url('/'))
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
      <div><input value="" name="cover_img_url"></div><br>
      <div><input type="submit" value="Create Stream" class="btn btn-primary" name="create"></div>
    </form>
    """ + TAIL
    self.response.write(PAGE)

class View(webapp2.RequestHandler):
  def post(self):
    stream_name = self.request.get('stream')
    if self.request.get('subscribe'):
      stream = Stream.query(Stream.name == stream_name).fetch(1)
      if stream:
        cur_user = User.query(User.identity == users.get_current_user().user_id()).fetch(1)
        if not cur_user:
          cur_user = User()
          cur_user.identity = users.get_current_user().user_id()
          cur_user.email = users.get_current_user().email()
        else:
          cur_user = cur_user[0]
        if stream[0].name not in cur_user.subscriptions:
          cur_user.subscriptions.append(stream[0].name)

        cur_user.put()
    else:
      # Store image
      stream = Stream.query(Stream.name == stream_name).fetch(1)
      if stream and self.request.get('file'):
        picture = Picture()
        picture.stream_id = stream_name
        picture.image = self.request.get('file')
        randomMonth = random.randint(1, 12)
        randomDay = random.randint(1, 28)
        picture.date = datetime.date(year=2015, month=randomMonth, day=randomDay)
        lat = random.uniform(-60, 60)
        lon = random.uniform(-179, 179)
        picture.geo = ndb.GeoPt(lat,lon)
        picture.put()
        stream[0].last_updated_date = datetime.datetime.now()
        stream[0].num_pictures += 1
        stream[0].put()
        stream[0].put()

    self.redirect('/view?%s' % urllib.urlencode({'stream': stream_name}))


  def get(self):
    user = users.get_current_user()
    if not user:
      self.redirect('/')
      return
    stream_name = self.request.get('stream')
    if stream_name:
      stream = Stream.query(Stream.name == stream_name).fetch(1)
      if stream:
        stream = stream[0]
        user = users.get_current_user()
        
        pictures = Picture.query(Picture.stream_id == stream_name).order(-Picture.created_date)
        for pic in pictures:
          image_id = pic.key.urlsafe()

        HEAD_CONTENT = '''
    <link rel="stylesheet" href="css/dropzone.css">
    <link rel="stylesheet" href="css/lightbox.css">
    <script src="js/dropzone.js"></script>
        '''
        PAGE = HEAD % (HEAD_CONTENT, user.nickname(), users.create_logout_url('/'))
        PAGE += '<script src="js/lightbox-plus-jquery.min.js"></script>'

        PAGE += "<h4><b>%s</b><h4>" % stream_name

        pictures = Picture.query(Picture.stream_id == stream_name).order(-Picture.created_date)
        max_line = 2
        max_line_str = self.request.get('max_line')
        if max_line_str:
          max_line = int(max_line_str)

        PAGE+='<a class="btn btn-primary" href="/view?%s">Geo View</a>' % (urllib.urlencode({'stream': stream_name, 'geo': 'true'}))
        PAGE+='<br><br>'
        count = 0
        for pic in pictures:
          if count / 4 >= max_line:
            PAGE += """\
              <a href="/view?%s" class="btn btn-default">More Pictures</a> 
            """ % (urllib.urlencode({'stream': stream_name, 'max_line': max_line + 2}))
            break
          PAGE += ('<a href=/img?img_id=%s data-lightbox="true"><img src="/img?img_id=%s&resize=true"></img></a>' % (pic.key.urlsafe(),pic.key.urlsafe()))
          count += 1
          if count % 4 == 0:
            PAGE += "<br>"

        PAGE += '<br><br>(Only stream owner can upload images.)'
        if stream.creator_id == user.user_id():
          PAGE += "<br><br>Please upload your files here."
          PAGE += '''<form action="/view?%s" class="dropzone"></form>''' % (urllib.urlencode({'stream': stream_name}))
        else:
          PAGE += """\
        <form action="/view?%s" method="post">
          <input type="submit" class="btn btn-primary" value="Subscribe" name="subscribe">
        </form> """ % (urllib.urlencode({'stream': stream_name}))

        PAGE += TAIL
        stream.num_views += 1
        stream.time_stamp.append(datetime.datetime.now())
        stream.put()

        if self.request.get('geo'):
          template_values = {
            'stream': stream,
            'user': user,
            'users': users,
            'stream_name': stream_name,
            'pictures': pictures,
            'urllib': urllib
          }
          template = JINJA_ENVIRONMENT.get_template('html/view.html')
          self.response.write(template.render(template_values))
        else:
          self.response.write(PAGE)
      else:
        self.redirect('/error?%s' % (urllib.urlencode({'problem': 'no such stream name ' + stream_name})))

    else:
      user = users.get_current_user()
      HEAD_CONTENT = ''
      PAGE = HEAD % (HEAD_CONTENT, user.nickname(), users.create_logout_url('/'))
      PAGE += "<b>View All Streams</b><br>"
      streams = Stream.query().order(Stream.created_date)
      count = 0
      PAGE += "<table class=\"table table-bordered\"><tr>"
      for stream in streams:
        PAGE += "<td>"
        PAGE += "<a href=/view?%s>%s</a>" % (urllib.urlencode({'stream': stream.name}), stream.name)
        PAGE += "<br>"
        PAGE += ('<a href=/view?%s><img src="%s", width="64"></img><a>' % (urllib.urlencode({'stream': stream.name}), stream.cover_img_url))
        PAGE += "</td>"
        count += 1
        if count % 4 == 0:
          PAGE += "</tr><tr>"
      PAGE += "</tr></table>"

      PAGE += TAIL
      self.response.write(PAGE)

class Search(webapp2.RequestHandler):
  def post(self):
    query_params = {'show': self.request.get('queryString')}
    self.redirect('/search?' + urllib.urlencode(query_params))

  def get(self):
    user = users.get_current_user()
    if not user:
      self.redirect('/')
      return
    autolist = memcache.get('autolist')
    if not autolist:
      autolist = set()
    LIST = '"' + '","'.join(sorted(list(autolist))) + '"'

    HEAD_CONTENT = '''
  <link rel="stylesheet" href="http://code.jquery.com/ui/1.11.4/themes/smoothness/jquery-ui.css">
  <script src="http://code.jquery.com/jquery-1.10.2.js"></script>
  <script src="http://code.jquery.com/ui/1.11.4/jquery-ui.js"></script>
  <script>
  $(function() {
    var availableTags = [
      %s
    ];
    $( "#tags" ).autocomplete({
      source: function(request, response) {
        var results = $.ui.autocomplete.filter(availableTags, request.term);
        response(results.slice(0, 20));
      }
    });
  });
  </script>
    ''' % LIST
    PAGE = HEAD % (HEAD_CONTENT, user.nickname(), users.create_logout_url('/'))
    PAGE += '''
        <form action="/cron?rebuild=true" method="post">
          <input type="submit" class="btn btn-primary" value="Rebuild completion index">
        </form>
            '''
    PAGE += "<b>Search</b>"

    PAGE += """
      <form action="/search" enctype="multipart/form-data" method="post">
        <div><input id="tags" name="queryString"></div><br>
        <div><input type="submit" class="btn btn-primary" value="Search"></div>
      </form>
      """ 
    '''<div><textarea name="queryString" rows="3" cols="60">Search name or tags</textarea></div>'''

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
  def post(self):
    if self.request.get('change_rate'):
      change = self.request.get('change')
      cur_user = User.query(User.identity == users.get_current_user().user_id()).fetch(1)
      if cur_user:
        cur_user = cur_user[0]
      else:
        cur_user = User()
        cur_user.identity = users.get_current_user().user_id()
        cur_user.email = users.get_current_user().email()

      if change == 'no':
        cur_user.trending_report = 'no'
      elif change == '5mins':
        cur_user.trending_report = '5mins'
      elif change == '1hour':
        cur_user.trending_report = '1hour'
      elif change == '1day':
        cur_user.trending_report = '1day'
      cur_user.put()

    self.redirect('/trending')

  def get(self):
    user = users.get_current_user()
    if not user:
      self.redirect('/')
      return
    HEAD_CONTENT = ''
    PAGE = HEAD % (HEAD_CONTENT, user.nickname(), users.create_logout_url('/'))
    PAGE += "<b>Trending</b><br>"

    result = memcache.get('result')
   
    if result: 
      for item in result:
        stream_name = item[1]
        stream = Stream.query(Stream.name == stream_name).fetch(1)
        if stream:
          stream = stream[0]
          PAGE += "<a href=/view?%s>%s</a><br>" % (urllib.urlencode({'stream': stream.name}), stream.name)
          PAGE += ('<a href=/view?%s><img src="%s", width="64"></img></a>' % (urllib.urlencode({'stream': stream.name}), stream.cover_img_url))
          PAGE += " <b> %d views in past hour </b>" % item[0]
          PAGE += "<br>"
      PAGE += '<hr>'


    checked = ('checked', '', '', '')
    cur_user = User.query(User.identity == users.get_current_user().user_id()).fetch(1)
    if cur_user:
      if cur_user[0].trending_report == '5mins':
        checked = ('', 'checked', '', '')
      elif cur_user[0].trending_report == '1hour':
        checked = ('', '', 'checked', '')
      elif cur_user[0].trending_report == '1day':
        checked = ('', '', '', 'checked')

    PAGE += """\
      <form action="/trending"  method="post">
        <div><input type=\"radio\" name=\"change\" value=\"no\" %s> No reports</div>
        <div><input type=\"radio\" name=\"change\" value=\"5mins\" %s> Every 5 minutes</div>
        <div><input type=\"radio\" name=\"change\" value=\"1hour\" %s> Every 1 hour</div>
        <div><input type=\"radio\" name=\"change\" value=\"1day\" %s> Every day</div>
        <div>Email trending report</div>
        <div><input type="submit" value="Update rate" class="btn btn-primary" name="change_rate"></div>
      </form>
    """ % checked
    PAGE += TAIL
    self.response.write(PAGE)

class Error(webapp2.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if not user:
      self.redirect('/')
      return
    HEAD_CONTENT = ''
    PAGE = HEAD % (HEAD_CONTENT, user.nickname(), users.create_logout_url('/'))
    problem = self.request.get('problem')
    PAGE += "<b>Error</b><br>" + problem + TAIL
    self.response.write(PAGE)

class Social(webapp2.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if not user:
      self.redirect('/')
      return
    HEAD_CONTENT = ''
    PAGE = HEAD % (HEAD_CONTENT, user.nickname(), users.create_logout_url('/'))
    PAGE += "<b>Social</b>" + TAIL
    self.response.write(PAGE)

class Image(webapp2.RequestHandler):
  def get(self):
    picture_key = ndb.Key(urlsafe=self.request.get('img_id'))
    picture = picture_key.get()
    if picture.image:
      self.response.headers['Content-Type'] = 'image/gif'
      if self.request.get('resize'):
        self.response.out.write(images.resize(picture.image, height=96, allow_stretch=False))
      else:
        self.response.out.write(picture.image)
    else:
      self.response.out.write('No image')

class Cron(webapp2.RequestHandler):
  def make_auto_list(self):
    autolist = set()
    streams = Stream.query()
    for stream in streams:
      autolist.add(stream.name.strip().lower())
      for tag in stream.tag:
        autolist.add(tag.strip(' #').lower())
    memcache.set(key="autolist", value=autolist)

  def post(self):
    if self.request.get('rebuild'):
      self.make_auto_list()
      self.redirect('/search')

  def get(self):
    send = self.request.get('send')
    if send:
      user_to_send = User.query(User.trending_report == send).fetch()
      message = str(memcache.get('result'))
      for each_user in user_to_send:
        if each_user.email:
          mail.send_mail(sender="chunheng.huang@gmail.com",
                         to=each_user.email,
                         subject="Digest",
                         body=message
                        )

    if self.request.get('topstream'):
      streams = Stream.query().fetch()
      now = datetime.datetime.now()
      deltaHour = datetime.timedelta(hours=1)
      result = []
      for stream in streams:
        while len(stream.time_stamp) != 0 and now - stream.time_stamp[0] > deltaHour:
          stream.time_stamp.pop(0)
        stream.put()
        result.append((len(stream.time_stamp), stream.name))
      result.sort(reverse=True)
      memcache.set(key="result", value=result[0:3])

    if self.request.get('rebuild'):
      self.make_auto_list()

class Android(webapp2.RequestHandler):
  def get(self):
    if self.request.get('viewstreams'):
      streams = Stream.query().order(-Stream.last_updated_date).fetch(16)
      streamCover = []
      streamName = []
      for stream in streams:
        streamCover.append(stream.cover_img_url)
        streamName.append(stream.name)
      
      dictPassed = {'streamCover':streamCover, 'streamName':streamName}
      jsonObj = json.dumps(dictPassed, sort_keys=True,indent=4, separators=(',', ': '))
      self.response.write(jsonObj)

    elif self.request.get('subscriptions'):
      user_id = self.request.get('user_id')
      cur_user = User.query(User.identity == user_id).fetch(1)
      pictureURL = []
      pictureStream = []
      pictureCaption = []
      if cur_user:
        pictures = Picture.query(Picture.stream_id.IN(cur_user[0].subscriptions)).order(-Picture.created_date).fetch(16)
        for picture in pictures:
          pictureURL.append("http://connexus0.appspot.com/img?img_id=%s" % picture.key.urlsafe())
          pictureStream.append(picture.stream_id)
          pictureCaption.append(picture.caption)
      
      dictPassed = {'pictureURL':pictureURL, 'pictureStream':pictureStream, 'pictureCaption':pictureCaption}
      jsonObj = json.dumps(dictPassed, sort_keys=True,indent=4, separators=(',', ': '))
      self.response.write(jsonObj)
      
    elif self.request.get('viewpictures'):
      stream_name = self.request.get('stream')
      pictureURL = []
      pictureCaption = []
      if stream_name:
        pictures = Picture.query(Picture.stream_id == stream_name).order(-Picture.created_date)
        for picture in pictures:
          pictureURL.append("http://connexus0.appspot.com/img?img_id=%s" % picture.key.urlsafe())
          pictureCaption.append(picture.caption)

        streams = Stream.query(Stream.name == stream_name).fetch(1)
        if streams:
          stream = streams[0]
          stream.num_views += 1
          stream.time_stamp.append(datetime.datetime.now())
          stream.put()

      dictPassed = {'pictureURL':pictureURL, 'pictureCaption':pictureCaption}
      jsonObj = json.dumps(dictPassed, sort_keys=True,indent=4, separators=(',', ': '))
      self.response.write(jsonObj)

    elif self.request.get('search'):
      streamCover = []
      streamName = []
      count = 0
      queryString = self.request.get('show')

      if queryString:
        index = search.Index(name="myIndex")
        try:
          results = index.search(queryString) 
          count = results.number_found

          for scored_document in results:
              # handle results
              if Stream.query(Stream.name == scored_document.fields[0].value).fetch(1):
                stream = Stream.query(Stream.name == scored_document.fields[0].value).fetch(1)[0]
                streamCover.append(stream.cover_img_url)
                streamName.append(stream.name)

        except search.Error:
          pass # print "Fail in searching in the Index"

      dictPassed = {'streamCover':streamCover, 'streamName':streamName, 'count':count}
      jsonObj = json.dumps(dictPassed, sort_keys=True,indent=4, separators=(',', ': '))
      self.response.write(jsonObj)
      
    elif self.request.get('nearby'):
      lat = self.request.get('lat')
      lon = self.request.get('lon')

      pictureURL = []
      pictureStream = []
      pictureCaption = []
      pictureDis = []

      if lat and lon:
        cur_pos = ndb.GeoPt(lat, lon)
        print "OK"
        pictures = Picture.query()
        picList = []
        for pic in pictures:
          picList.append(pic)
        picList = sorted(picList, key=lambda k: abs(k.geo.lat - cur_pos.lat) + abs(k.geo.lon - cur_pos.lon))
        for picture in picList:
          pictureURL.append("http://connexus0.appspot.com/img?img_id=%s" % picture.key.urlsafe())
          pictureStream.append(picture.stream_id)
          pictureCaption.append(picture.caption)
          pictureDis.append(abs(picture.geo.lat - cur_pos.lat) + abs(picture.geo.lon - cur_pos.lon))
      
      dictPassed = {'pictureURL':pictureURL, 'pictureStream':pictureStream,
                    'pictureCaption':pictureCaption, 'pictureDis':pictureDis}
      jsonObj = json.dumps(dictPassed, sort_keys=True,indent=4, separators=(',', ': '))
      self.response.write(jsonObj)

  def post(self):
    stream_name = self.request.get('stream')
    lat = self.request.get('lat')
    lon = self.request.get('lon')
    uploaded = self.request.get('file') 

    if stream_name and lat and lon and uploaded:
      stream = Stream.query(Stream.name == stream_name).fetch(1)
      if stream:
        picture = Picture()
        picture.stream_id = stream_name
        picture.image = uploaded
        #picture.date, auto added
        picture.geo = ndb.GeoPt(float(lat),float(lon))
        picture.caption = self.request.get('caption')
        picture.put()
        stream[0].last_updated_date = datetime.datetime.now()
        stream[0].num_pictures += 1
        stream[0].put()
        stream[0].put()

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
  ('/cron', Cron),
  ('/android', Android)
], debug=True)
