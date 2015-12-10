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
      parkings = Parking.query(Parking.user_email == user_email).order(-Parking.created_time).fetch(16)

      parkingLat = []
      parkingLon = []
      parkingDone = []
      parkingTime = []

      for parking in parkings:
        parkingLat.append(parking.geo.lat)
        parkingLon.append(parking.geo.lon)
        parkingDone.append(parking.done_parking)
        parkingTime.append(parking.created_time)

      dictPassed = {'parkingLat':parkingLat, 'parkingLon':parkingLon,
                    'parkingDone':parkingDone, 'parkingTime':parkingTime}

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
      picture.image = images.resize(image, height=1080, allow_stretch=False)
      parking.description = self.request.get('description')
      parking.done_parking = False
      parking.put()

app = webapp2.WSGIApplication([
  ('/park', Park)
], debug=True)
