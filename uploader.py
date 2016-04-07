from __future__ import print_function

from datetime import datetime
import json
import os
import re
import sys
import time
import uuid
import webbrowser

from six.moves.urllib.parse import urljoin, urlparse, urlunparse

from apiclient.http import MediaFileUpload
from apiclient import errors as apierrors

from drive_service import DriveServiceAuth

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

class MaxUpload(Exception):
    pass

class UntitledFolder(Exception):
    pass

class UntitledFile(Exception):
    pass

class PageUploader():

    def __init__(self, max_files=100, verbose=False, dry_run=False, mime_types=None):
        secrets_path = os.path.join(os.path.dirname(__file__), 'client_secrets.json')
        credentials_path = os.path.join(os.path.dirname(__file__), 'credentials.json')
        self.drive_auth = DriveServiceAuth(secrets_path, credentials_path)
        self.drive_service = None
        self.verbose = verbose
        self.dry_run = dry_run
        if not mime_types:
            self.mime_types = ['*/*']
        if isinstance(mime_types, (list, tuple)):
            self.mime_types = mime_types
        else:
            self.mime_types = [mime_types]
        self.max_files = max_files
        self.counter = 0
        self.tag = 'UPLOADER-' + datetime.now().replace(second=0, microsecond=0).isoformat()
        self.folders = { }
        self.links = { }

    def mockFolder(self, parent_id, metadata={}):
        folder_id = uuid.uuid4().hex
        file = { 'id': folder_id }
        file.update(metadata)
        if self.verbose and '*/*' in self.mime_types:
            print('Folder %s mocked at %s' % (file['title'], parent_id))
        return file

    def mockFile(self, parent_id, metadata={}):
        file_id = uuid.uuid4().hex
        link = 'https://docs.google.com/a/kentfieldschools.org/document/d/%s/edit?usp=drivesdk' % file_id
        file = { 'id': file_id, 'alternateLink': link }
        file.update(metadata)
        print('File %s mocked at %s' % (file['title'], parent_id))
        return file

    def addLink(self, link_url, file):
        u = urlparse(link_url)
        link = urlunparse((u.scheme, u.netloc, u.path, None, None, None)).lower()
        self.links[link] = { 'href': file['alternateLink'], 'title': file['title'], 'id': file['id'] }

    def dumpLinks(self):
        print('\n\nLINKS:')
        print('title\tfrom\tto')
        for url in sorted(self.links.keys()):
            print('%s\t%s\t%s' % (self.links[url]['title'], url, self.links[url]['href']))

    def initService(self):
        self.drive_service = self.drive_auth.build_service()
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

    def createFolder(self, title, parent_id):
        if title is None or title.strip() == '':
            raise UntitledFolder
 
        folder_metadata = {
            'title': title,
            'parents': [ { 'id': parent_id } ],
            'mimeType': 'application/vnd.google-apps.folder',
            'properties': { 'tag': self.tag },
        }


        file = None
        if self.dry_run:
            file = self.mockFolder(parent_id, folder_metadata)
        else:
            try:
                file = self.drive_service.files().insert(body=folder_metadata).execute()
            except apierrors.HttpError as error:
                print('An error occurred: %s' % error)
            time.sleep(0.5)
        return file
 
    def findOrCreateFolder(self, name, parent_id):
        created = False
        file = None
        if not self.dry_run:
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
        if self.max_files > 0 and self.counter >= self.max_files:
            raise MaxUpload('Maximum %d files uploaded' % self.counter)

        if not('*/*' in self.mime_types or mime_type in self.mime_types):
            return None

        self.counter += 1    

        if title is None or title.strip() == '':
            raise UntitledFile

        file_metadata = {
            'title': title,
            'mimeType': to_mime_type,
            'properties': { 'tag': self.tag },
        }

        file = None
        if self.dry_run:
            file = self.mockFile(parent_id, file_metadata)
        else:
            media_body = MediaFileUpload(filename, mimetype=mime_type, resumable=True)
            if to_mime_type is None:
                to_mime_type = mime_type

            if description:
                file_metadata['description'] = description
            if parent_id:
                file_metadata['parents'] = [ { 'id': parent_id } ]

            try:
                file = self.drive_service.files().insert(
                    body=file_metadata, media_body=media_body).execute()
                print('File %s inserted at %s' % (title, parent_id))
            except apierrors.HttpError as error:
                print('An error occurred: %s' % error)
            time.sleep(0.5)
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
                    if len(parts) > 1 and parts[1] == 'Kentfield_School_District':
                        del parts[1]
                    if len(parts) > 1:
                        if parts[1] == 'News':
                            folder = '/Sites/District/Articles'
                            parts = []
                elif parts[0] == 'files':
                    folder = '/Sites/District/Files'
                    parts = []
        elif u.hostname == 'www.edlinesites.net':
            if len(parts) > 0:
                if parts[0] == 'pages':
                    if len(parts) > 1:
                        school = parts[1].split('_', 1)[0]
                        folder = '/Sites/' + school + '/Pages'
                        del parts[1]
                    if len(parts) > 1:
                        if parts[1] == 'News':
                            folder = '/Sites/' + school + '/Articles'
                            parts = []
                elif parts[0] == 'files':
                    folder = '/Sites/District/Files'
                    parts = []
        else:
            if self.verbose:
                print('foreign host %s' % u.hostname)
            parts = []

        if len(parts) > 2:
            parts = parts[1:-1]
            folder = folder + '/' + '/'.join([re.sub(r'[_]+', ' ', p).strip() for p in parts])
        # print('%s -> %s' % (url, folder))
        return folder

    def uploadImage(self, meta):
        folder_id = None
        folder = self.getFolderPathFromUrl(meta['location'])
        if folder is None:
            if self.verbose:
                print('cannot upload image %s - no folder' % meta['location'])
        else:
            folder_id = self.getFolderId(folder)
            if folder_id is None and self.verbose:
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
            if self.verbose:
                print('cannot upload file %s - no folder' % meta['location'])
        else:
            folder_id = self.getFolderId(folder)
            if folder_id is None and self.verbose:
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
                if self.verbose:
                    print('cannot upload - no mime type for %s (%s)' % (meta['path'], meta['content_type']))
            else:
                file = self.createFile(meta['title'], None, folder_id, path, mime_type, to_mime_type)
                if file:
                    self.addLink(meta['link_url'], file)

    def uploadAllItems(self, fname):
        self.initService()

        with open(fname) as data_file:    
            items = json.load(data_file)
            for item in items:
                if 'images' in item:
                    for i in range(len(item['images'])):
                        meta = item['images'][i]
                        if 'image_metas' in item and len(item['image_metas']) > i:
                            meta.update(item['image_metas'][i])
                        try:
                            self.uploadImage(meta)
                        except MaxUpload as e:
                            return
                        except Exception as e:
                            print('images[%d] %s: %r' % (i, e.__class__.__name__, meta))
                            raise
                            return
                if 'files' in item:
                    for i in range(len(item['files'])):
                        meta = item['files'][i]
                        if 'file_metas' in item and len(item['file_metas']) > i:
                            meta.update(item['file_metas'][i])
                        try:
                            self.uploadFile(meta)
                        except MaxUpload as e:
                            return
                        except Exception as e:
                            print('files[%d] %s: %r' % (i, e.__class__.__name__, meta))
                            raise
                            return
            for item in items:
                if 'inlines' in item:
                    for i in range(len(item['inlines'])):
                        meta = item['inlines'][i]
                        if 'inline_metas' in item and len(item['inline_metas']) > i:
                            meta.update(item['inline_metas'][i])
                        try:
                            self.uploadFile(meta)
                        except MaxUpload as e:
                            return
                        except Exception as e:
                            print('inlines[%d] %s: %r' % (i, e.__class__.__name__, meta))
                            raise
                            return

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Upload items to Google Drive folder')
    parser.add_argument('-v', '--verbose', action='store_true', help='print progress on stdout')
    parser.add_argument('-n', '--dry-run', action='store_true', help='dry run (no uploading)')
    parser.add_argument('-t', '--mime-types', help='mime_types, comma-delimited')

    args = parser.parse_args()
    mime_types = [mt for mt in args.mime_types.split(',')]
    pu = PageUploader(-1, args.verbose, args.dry_run, mime_types)

    items_file = os.path.join(os.path.dirname(__file__), 'items.json')
    pu.uploadAllItems(items_file)
    pu.dumpLinks()
