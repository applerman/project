import cgi
import json
import urllib
import webapp2

from google.appengine.api import images
from google.appengine.api import users
from google.appengine.ext import ndb

##############
# Data Model
##############
class Parking(ndb.Model):
  user_email = ndb.StringProperty(indexed=True)
  geo = ndb.GeoPtProperty()
  image = ndb.BlobProperty()
  description = ndb.StringProperty()
  created_time = ndb.DateTimeProperty(auto_now_add=True)
  done_parking = ndb.BooleanProperty()
  shared_parking = ndb.BooleanProperty()

class User(ndb.Model):
  user_email = ndb.StringProperty(indexed=True)
  car = ndb.StringProperty()

##############
# Handlers
##############
class Park(webapp2.RequestHandler):
  def get(self):
    if self.request.get('viewparking'):
      user_email = self.request.get('user_email')
      shared_parking = bool(self.request.get('shared_parking'))
      recent_one = bool(self.request.get('recent_one'))
      number = 16
      if recent_one:
         number = 1
      parkings = Parking.query(ndb.AND(Parking.user_email == user_email, Parking.shared_parking ==
                               shared_parking)).order(-Parking.created_time).fetch(number)

      parkingLat = []
      parkingLon = []
      parkingDone = []
      parkingImgURL = []

      for parking in parkings:
        parkingLat.append(parking.geo.lat)
        parkingLon.append(parking.geo.lon)
        parkingDone.append(parking.done_parking)
        if parking.image:
          parkingImgURL.append("http://parkingrighthere.appspot.com/img?img_id=%s" % parking.key.urlsafe())
        else:
          parkingImgURL.append("")

      dictPassed = {'parkingLat':parkingLat, 'parkingLon':parkingLon,
                    'parkingDone':parkingDone, 'parkingImgURL':parkingImgURL}

      jsonObj = json.dumps(dictPassed, sort_keys=True,indent=4, separators=(',', ': '))
      self.response.write(jsonObj)

    elif self.request.get('viewuser'):
      user_email = self.request.get('user_email')

  def post(self):
    lat = self.request.get('lat')
    lon = self.request.get('lon')

    if lat and lon:
      parking = Parking()
      parking.user_email = self.request.get('user_email')
      parking.geo = ndb.GeoPt(float(lat), float(lon))
      image = self.request.get('image')
      if image:
        parking.image = images.resize(image, height=1080, allow_stretch=False)
      parking.description = self.request.get('description')
      parking.done_parking = False
      parking.shared_parking = bool(self.request.get('shared_parking'))
      parking.put()

class Image(webapp2.RequestHandler):
  def get(self):
    park_key = ndb.Key(urlsafe=self.request.get('img_id'))
    park = park_key.get()
    if park.image:
      self.response.headers['Content-Type'] = 'image/gif'
      self.response.out.write(park.image)
    else:
      self.response.out.write('No image')


app = webapp2.WSGIApplication([
  ('/park', Park),
  ('/img', Image)
], debug=True)
