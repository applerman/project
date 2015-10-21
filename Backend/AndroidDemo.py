import webapp2
from google.appengine.api import users, files, images
from google.appengine.ext import blobstore
from google.appengine.ext import ndb
from google.appengine.ext.webapp import blobstore_handlers
import time
import json

class Image(ndb.Model):
    blob_key = ndb.BlobKeyProperty()
    dateCreated = ndb.DateTimeProperty(auto_now_add=True)
    caption = ndb.StringProperty(indexed=False)

class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Hello, World!')

class GetUploadURL(webapp2.RequestHandler):
	def get(self):
		upload_url = blobstore.create_upload_url('/uploadHandler')
		upload_url = str(upload_url)
		dictPassed = {'upload_url':upload_url}
		jsonObj = json.dumps(dictPassed, sort_keys=True,indent=4, separators=(',', ': '))
		self.response.write(jsonObj)

class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        upload = self.get_uploads()[0]
    	user_photo = Image(blob_key = upload.key(), caption=self.request.params['photoCaption'])
        user_photo.put()

class ViewAllPhotos(webapp2.RequestHandler):
    def get(self):
        imageQuery = Image.query()
        imageList = []
        imageURLList = []
        imageCaptionList = []
        for pic in imageQuery:
            imageList.append(pic)
            
        imageList = sorted(imageList, key=lambda k: k.dateCreated,reverse = True)
        
        for pic in imageList:
            picURL = images.get_serving_url(pic.blob_key)
            imageURLList.append(picURL)
            imageCaptionList.append(pic.caption)

        dictPassed = {'displayImages':imageURLList, 'imageCaptionList':imageCaptionList}
        jsonObj = json.dumps(dictPassed, sort_keys=True,indent=4, separators=(',', ': '))
        self.response.write(jsonObj)

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/getUploadURL',GetUploadURL),
    ('/uploadHandler', UploadHandler),
    ('/viewAllPhotos', ViewAllPhotos)
], debug=True)