import httplib2
import os
import webbrowser

from oauth2client import client
from oauth2client.file import Storage
from apiclient.discovery import build

class PageUploader():

  def __init__(self):
    fpath = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'credentials.json')
    self.storage = Storage(fpath)

  def createCredentials(self):
    flow = client.flow_from_clientsecrets(
      'client_secrets.json',
      scope='https://www.googleapis.com/auth/drive',
      redirect_uri='urn:ietf:wg:oauth:2.0:oob')

    auth_uri = flow.step1_get_authorize_url()
    webbrowser.open(auth_uri)
    auth_code = raw_input('Enter the auth code: ')
    credentials = flow.step2_exchange(auth_code)
    self.storage.put(credentials)

  def buildService(self):
    credentials = self.storage.get()
    http_auth = credentials.authorize(httplib2.Http())
    self.drive_service = build('drive', 'v2', http=http_auth)

  def uploadHtmlItem(self, item):
    file_metadata = {
      'name' : 'My Report',
      'mimeType' : 'application/vnd.google-apps.spreadsheet'
    }
    media = MediaFileUpload('files/report.csv', mimetype='text/csv', resumable=True)
    file = self.drive_service.files().create(
      body=file_metadata, media_body=media, fields='id').execute()
    print 'File ID: %s' % file.get('id')

if __name__ == '__main__':
  pu = PageUploader()
  pu.createCredentials()

