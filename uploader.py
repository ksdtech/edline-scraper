from __future__ import print_function

import httplib2
import json
import os
import re
import sys
import uuid
import webbrowser

from six.moves.urllib.parse import urljoin, urlparse, urlunparse

from oauth2client import client
from oauth2client.file import Storage
from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from apiclient import errors as apierrors

from edline.items import get_file_type
from edline.settings import FILES_STORE, IMAGES_STORE
from edline.sanitizer import make_cleaned_path, sanitize_html_file

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

    def __init__(self, mock):
        fpath = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'credentials.json')
        self.mock = mock
        self.storage = Storage(fpath)
        self.folders = { }
        self.links = { }

    def mockFolder(self):
        folder_id = uuid.uuid4().hex
        return { 'id': folder_id }

    def mockFile(self):
        file_id = uuid.uuid4().hex
        link = 'https://docs.google.com/a/kentfieldschools.org/document/d/%s/edit?usp=drivesdk' % file_id
        return { 'id': file_id, 'alternateLink': link }

    def addLink(self, link_url, file):
        u = urlparse(link_url)
        link = urlunparse((u.scheme, u.netloc, u.path, None, None, None)).lower()
        self.links[link] = { 'href': file['alternateLink'], 'id': file['id'] }

    def dumpLinks(self):
        for url in sorted(self.links.keys()):
            print('%s\t%s' % (url, self.links[url]['href']))

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
        file = None
        if self.mock:
            file = self.mockFolder()
        else:
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
        file = None
        if self.mock:
            file = self.mockFile()
        else:
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
        # Remove empty '' 
        parts = u.path.split('/')[1:]
        if u.hostname == 'www.kentfieldschools.org':
            if len(parts) > 0:
                if parts[0] == 'pages':
                    folder = '/Sites/District/Pages'
                    if len(parts) > 1:
                        if parts[1] == 'News':
                            folder = '/Sites/District/Articles'
                        else:
                            if parts[1] == 'Kentfield_School_District':
                                parts = parts[2:-1]
                            else:
                                parts = parts[1:-1]
                            folder = folder + '/' + '/'.join([re.sub(r'[_]+', ' ', p).strip() for p in parts])
                elif parts[0] == 'files':
                    folder = '/Sites/District/Files'
        elif u.hostname == 'www.edlinesites.net':
            if len(parts) > 0:
                if parts[0] == 'pages':
                    if len(parts) > 1:
                        school = parts[1]
                        folder = '/Sites/' + school + '/Pages'
                        if len(parts) > 2:
                            if parts[2] == 'News':
                                folder = '/Sites/' + school + '/Articles'
                            else:
                                parts = parts[2:-1]
                                folder = folder + '/' + '/'.join([re.sub(r'[_]+', ' ', p).strip() for p in parts])
                elif parts[0] == 'files':
                    folder = '/Sites/District/Files'
        else:
            print('foreign host %s' % u.hostname)
        return folder

    def uploadImage(self, meta):
        folder_id = None
        folder = self.getFolderPathFromUrl(meta['location'])
        if folder is None:
            print('cannot upload image %s - no folder' % meta['location'])
        else:
            folder_id = self.getFolderId(folder)
            if folder_id is None:
                print('cannot upload image %s - no folder id for %s' % (meta['location'], folder))

        if folder_id:
            mime_type = meta['content_type']
            path = os.path.join(IMAGES_STORE, meta['path'])
            file = self.createFile(meta['title'], None, folder_id, path, mime_type)
            if file:
                self.addLink(meta['link_url'], file)

    def uploadFile(self, meta):
        folder_id = None
        folder = self.getFolderPathFromUrl(meta['location'])
        if folder is None:
            print('cannot upload file %s - no folder' % meta['location'])
        else:
            folder_id = self.getFolderId(folder)
            if folder_id is None:
                print('cannot upload file %s - no folder id for %s' % (meta['location'], folder))

        if folder_id:
            mime_type = None
            to_mime_type = None
            path = os.path.join(FILES_STORE, meta['path'])
            file_type = get_file_type(meta['content_type'])
            if file_type == 'html':
                mime_type = 'text/html'
                to_mime_type = 'application/vnd.google-apps.document'
                cleaned_path = make_cleaned_path(path)
                if sanitize_html_file(path, cleaned_path, meta['url'], self.links):
                    path = cleaned_path
            elif file_type == 'pdf':
                mime_type = 'application/pdf'
            if mime_type is None:
                print('cannot upload - no mime type for %s (%s)' % (meta['path'], meta['content_type']))
            else:
                file = self.createFile(meta['title'], None, folder_id, path, mime_type, to_mime_type)
                if file:
                    self.addLink(meta['link_url'], file)

    def uploadAllItems(self, fname):
        with open(fname) as data_file:    
            items = json.load(data_file)
            for item in items:
                if 'images' in item:
                    for i in range(len(item['images'])):
                        meta  = item['image_metas'][i].copy()
                        meta.update(item['images'][i])
                        self.uploadImage(meta)
                if 'files' in item:
                    for i in range(len(item['files'])):
                        meta  = item['file_metas'][i].copy()
                        meta.update(item['files'][i])
                        self.uploadFile(meta)
            for item in items:
                if 'inlines' in item:
                    for i in range(len(item['inlines'])):
                        meta  = item['inline_metas'][i].copy()
                        meta.update(item['inlines'][i])
                        self.uploadFile(meta)

if __name__ == '__main__':
    pu = PageUploader(True)
    # pu.createCredentials()
    pu.buildService()
    pu.uploadAllItems('/Users/pz/Projects/_active/edline-scraper/items.json')
    pu.dumpLinks()
