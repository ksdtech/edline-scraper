from __future__ import print_function

import httplib2
import json
import os
import re
import sys
import webbrowser
from six.moves.urllib.parse import urlparse, urljoin

from oauth2client import client
from oauth2client.file import Storage
from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from apiclient import errors as apierrors

FILES_STORE = '/Users/pz/Projects/_active/edline-scraper/files'

"""
{
u'id': u'1xd_VZ1pt2pQTFFdce8Ha5q403D_XmpZwsYtuXNJ0Ua0', 
u'kind': u'drive#file', 
u'mimeType': u'application/vnd.google-apps.document', 
u'version': u'13426', 
u'etag': u'"c-g_a-1OtaH-kNQ4WBoXLp3Zv9s/MTQ1Njc4NTg3MzY1OQ"', 
u'title': u'Kentfield School District: Support Kentfield Schools', 
u'spaces': [u'drive'], 
u'parents': [{u'isRoot': True, u'kind': u'drive#parentReference', u'id': u'0AN3xtFAz_q1FUk9PVA', u'selfLink': u'https://www.googleapis.com/drive/v2/files/1xd_VZ1pt2pQTFFdce8Ha5q403D_XmpZwsYtuXNJ0Ua0/parents/0AN3xtFAz_q1FUk9PVA', u'parentLink': u'https://www.googleapis.com/drive/v2/files/0AN3xtFAz_q1FUk9PVA'}], 
u'quotaBytesUsed': u'0', 
u'shared': False, 
u'editable': True, 
u'copyable': True, 
u'writersCanShare': True, 
u'appDataContents': False, 
u'explicitlyTrashed': False, 
u'labels': {u'restricted': False, u'starred': False, u'viewed': True, u'hidden': False, u'trashed': False}, 
u'userPermission': {u'kind': u'drive#permission', u'etag': u'"c-g_a-1OtaH-kNQ4WBoXLp3Zv9s/TzzJ01XiRdJqMZwQpkwcg5B0iWw"', u'role': u'owner', u'type': u'user', u'id': u'me', u'selfLink': u'https://www.googleapis.com/drive/v2/files/1xd_VZ1pt2pQTFFdce8Ha5q403D_XmpZwsYtuXNJ0Ua0/permissions/me'}, 
u'owners': [{u'emailAddress': u'webmaster@kentfieldschools.org', u'kind': u'drive#user', u'isAuthenticatedUser': True, u'displayName': u'Kentfield Schools Webmaster', u'permissionId': u'16542660849317291223'}], 
u'ownerNames': [u'Kentfield Schools Webmaster'], 
u'lastModifyingUser': {u'emailAddress': u'webmaster@kentfieldschools.org', u'kind': u'drive#user', u'isAuthenticatedUser': True, u'displayName': u'Kentfield Schools Webmaster', u'permissionId': u'16542660849317291223'}, 
u'lastModifyingUserName': u'Kentfield Schools Webmaster', 
u'selfLink': u'https://www.googleapis.com/drive/v2/files/1xd_VZ1pt2pQTFFdce8Ha5q403D_XmpZwsYtuXNJ0Ua0'
u'iconLink': u'https://ssl.gstatic.com/docs/doclist/images/icon_11_document_list.png', 
u'embedLink': u'https://docs.google.com/a/kentfieldschools.org/document/d/1xd_VZ1pt2pQTFFdce8Ha5q403D_XmpZwsYtuXNJ0Ua0/preview', 
u'alternateLink': u'https://docs.google.com/a/kentfieldschools.org/document/d/1xd_VZ1pt2pQTFFdce8Ha5q403D_XmpZwsYtuXNJ0Ua0/edit?usp=drivesdk', 
u'exportLinks': {
  u'text/html': u'https://docs.google.com/feeds/download/documents/export/Export?id=1xd_VZ1pt2pQTFFdce8Ha5q403D_XmpZwsYtuXNJ0Ua0&exportFormat=html', 
  u'text/plain': u'https://docs.google.com/feeds/download/documents/export/Export?id=1xd_VZ1pt2pQTFFdce8Ha5q403D_XmpZwsYtuXNJ0Ua0&exportFormat=txt', 
  u'application/vnd.openxmlformats-officedocument.wordprocessingml.document': u'https://docs.google.com/feeds/download/documents/export/Export?id=1xd_VZ1pt2pQTFFdce8Ha5q403D_XmpZwsYtuXNJ0Ua0&exportFormat=docx',
  u'application/zip': u'https://docs.google.com/feeds/download/documents/export/Export?id=1xd_VZ1pt2pQTFFdce8Ha5q403D_XmpZwsYtuXNJ0Ua0&exportFormat=zip', 
  u'application/vnd.oasis.opendocument.text': u'https://docs.google.com/feeds/download/documents/export/Export?id=1xd_VZ1pt2pQTFFdce8Ha5q403D_XmpZwsYtuXNJ0Ua0&exportFormat=odt', 
  u'application/rtf': u'https://docs.google.com/feeds/download/documents/export/Export?id=1xd_VZ1pt2pQTFFdce8Ha5q403D_XmpZwsYtuXNJ0Ua0&exportFormat=rtf', 
  u'application/pdf': u'https://docs.google.com/feeds/download/documents/export/Export?id=1xd_VZ1pt2pQTFFdce8Ha5q403D_XmpZwsYtuXNJ0Ua0&exportFormat=pdf'
}, 
u'modifiedDate': u'2016-02-29T22:44:33.659Z', 
u'createdDate': u'2016-02-29T22:44:33.659Z', 
u'modifiedByMeDate': u'2016-02-29T22:44:33.659Z', 
u'lastViewedByMeDate': u'2016-02-29T22:44:33.659Z', 
u'markedViewedByMeDate': u'1970-01-01T00:00:00.000Z', 
}
"""

class PageUploader():

  def __init__(self):
    fpath = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'credentials.json')
    self.storage = Storage(fpath)
    self.folders = { }

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
    about = self.drive_service.about().get().execute()
    root_folder_id = about['rootFolderId']
    self.folders['/'] = { 'parent': None, 'drive_id': root_folder_id }

  def searchFolder(self, name, parent_id):
    query = 'mimeType=\'application/vnd.google-apps.folder\' and trashed=false and title=\'%s\'' % name
    if parent_id:
      query += ' and \'%s\' in parents' % parent_id

    param = {
      'q': query,
      'fields': 'items(id,kind,mimeType,modifiedDate,title)'
    }
    result = []
    page_token = None
    while True:
      try:
        if page_token:
          param['pageToken'] = page_token
        files = self.drive_service.files().list(**param).execute()
        result.extend(files['items'])
        page_token = files.get('nextPageToken')
        if not page_token:
          break
      except apierrors.HttpError as error:
        print('An error occurred: %s' % error)

    file = None
    if result:
      file = result[0]
    return file

  def createFolder(self, name, parent_id):
    file_metadata = {
      'title': name,
      'parents': [ { 'id': parent_id } ],
      'mimeType': 'application/vnd.google-apps.folder'
    }

    file = None
    try:
      file = self.drive_service.files().insert(body=file_metadata).execute()
    except apierrors.HttpError as error:
      print('An error occurred: %s' % error)
    return file
 
  def findOrCreateFolder(self, name, parent_id):
    created = False
    file = self.searchFolder(name, parent_id)
    if file is None:
      file = self.createFolder(name, parent_id)
      created = True
    return (file, created)

  def createFile(self, title, description, parent_id, filename, mime_type, to_mime_type=None):
    """Insert new file.

    Args:
      service: Drive API service instance.
      title: Title of the file to insert, including the extension.
      description: Description of the file to insert.
      parent_id: Parent folder's ID.
      mime_type: MIME type of the file to insert.
      filename: Filename of the file to insert.
    Returns:
      Inserted file metadata if successful, None otherwise.
    """
    media_body = MediaFileUpload(filename, mimetype=mime_type, resumable=True)
    if to_mime_type is None:
      to_mime_type = mime_type

    file_metadata = {
      'title': title,
      'mimeType': to_mime_type
    }
    if description:
      file_metadata['description'] = description
    if parent_id:
      file_metadata['parents'] = [ { 'id': parent_id } ]

    file = None
    try:
      file = self.drive_service.files().insert(
        body=file_metadata, media_body=media_body).execute()
    except apierrors.HttpError as error:
      print('An error occurred: %s' % error)
    return file
 
  def getFolderId(self, folder):
    folder_stack = [ ]
    tmpf = folder
    while not (tmpf == '/' or tmpf in self.folders):
      folder_stack.append(tmpf)
      tmpf = os.path.dirname(tmpf)

    while folder_stack:
      tmpf = folder_stack.pop()
      parent, child = os.path.split(tmpf)

      f = self.folders.get(parent)
      if not f:
        raise Exception('Bad stack - folder %s' % tmpf)
      parent_id = f.get('drive_id')
      if not parent_id:
        raise Exception('No id for %s' % parent)

      file, created = self.findOrCreateFolder(child, parent_id)
      if not file:
        raise Exception('Failed to locate Drive folder %s in %s (%s)' % (child, parent, parent_id))
      tid = file['id']
      self.folders[tmpf] = { 'parent': parent, 'drive_id': tid }

    folder_id = self.folders[folder]['drive_id']
    return folder_id

  def getFolderPathFromUrl(self, url):
    u = urlparse(url)
    folder = None
    if u.hostname == 'www.kentfieldschools.org':
      parts = os.path.dirname(u.path).split('/')
      if len(parts) > 1:
        # parts[0] == '/'
        if parts[1] == 'pages':
          folder = '/Sites/District/Pages'
          if len(parts) > 2:
            if parts[2] == 'News':
              folder = '/Sites/District/Articles'
            else:
              parts = parts[2:]
              if parts[0] == 'Kentfield_School_District':
                parts = parts[1:]
              folder = folder + '/' + '/'.join([re.sub(r'[_]+', ' ', p).strip() for p in parts])
        elif parts[1] == 'files':
          folder = '/Sites/District/Files'
    elif u.hostname == 'www.edlinesites.net':
      parts = os.path.dirname(u.path).split('/')
      if len(parts) > 2:
        # parts[0] == '/'
        if parts[1] == 'pages':
          school, rest = parts[2].split('_', 1)
          folder = '/Sites/' + school + '/Pages'
          if len(parts) > 3:
            if parts[3] == 'News':
              folder = '/Sites/' + school + '/Articles'
            else:
              parts = parts[3:]
              folder = folder + '/' + '/'.join([re.sub(r'[_]+', ' ', p).strip() for p in parts])
        elif parts[1] == 'files':
          folder = '/Sites/District/Files'
    else:
      print('foreign host %s' % u.hostname)
    return folder

  def uploadFilesForItem(self, item):
      for i in range(len(item['files'])):
        file  = item['files'][i]
        meta  = item['file_metas'][i]
        title = meta['title']
        file_type = PageItem.get_file_type(item['content_type'])
        path = os.path.join(FILES_STORE, file['path'])
        folder = self.getFolderPathFromUrl(item['location'])
        folder_id = None
        if folder is None:
          print('cannot upload - no folder for %s' % item['location'])
        else:
          folder_id = self.getFolderId(folder)
          if folder_id is None:
            print('cannot upload - no folder id for %s' % folder)
        if folder_id:
          if file_type == 'html':
            self.createFile(title, None, folder_id, path, 'text/html', 
              'application/vnd.google-apps.document')
          elif file_type == 'pdf':
            self.createFile(title, None, folder_id, path, 'application/pdf')
          else:
            print('cannot upload - no mime type for %s' % item['location'])

  def uploadAllItems(self, fname):
    with open(fname) as data_file:    
      items = json.load(data_file)
      for item in items:
        if item['files']:
          self.uploadFilesForItem(item)

if __name__ == '__main__':
  pu = PageUploader()
  # pu.createCredentials()
  pu.buildService()
  pu.uploadAllItems('/Users/pz/Projects/_active/edline-scraper/items.json')
