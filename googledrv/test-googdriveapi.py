
from __future__ import print_function
import pickle
import os.path
import os
import io
import sys
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']

def do_download(service, file_id, file_name):
  request = service.files().get_media(fileId=file_id)
  fh = io.BytesIO()
  downloader = MediaIoBaseDownload(fh, request)
  done = False
  while done is False:
      status, done = downloader.next_chunk()
      print ("Download %d%%." % int(status.progress() * 100))
  with open(file_name,'wb') as out:     ## Open file as bytes
    out.write(fh.getbuffer())

def main():

    n = len(sys.argv)
    if (n != 2):
      print("usage: test-googledriveapi directory")
      sys.exit(2)

    this_dir = sys.argv[1]
    if (this_dir != "list"):
      if not os.path.exists("../../data/" + this_dir):
        os.makedirs("../../data/" + this_dir)

    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                '/home/webrat/python/astrophotography/astro-google-creds.json',
                SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('drive', 'v3', credentials=creds)

    # Call the Drive v3 API
    # First, get the folder ID by querying by mimeType and name
    folderId = service.files().list(
        q = "mimeType = 'application/vnd.google-apps.folder' and name='QSI testing ASB'",
        pageSize=100, fields="nextPageToken, files(id, name)").execute()
    # this gives us a list of all folders with that name
    folderIdResult = folderId.get('files', [])
    id = folderIdResult[0].get('id')
    #print(folderIdResult)

    # Match the requested filename to something in the list.


    items = service.files().list(q = "'" + id + "' in parents",
        pageSize=10, fields="nextPageToken, files(id, name)").execute()

    if not items:
        print('No files found.')
    else:
        id = None
        for item in items['files']:
            print(item['name'])
            if (item['name'] == this_dir):
              id = item['id']

        if ((this_dir != "list") and (id == None)):
          print("Directory not found!")
          sys.exit(2)

        if (this_dir == "list"):
          sys.exit(2)

        page_token = None
        
        while True:
            params = {"q" : "'" + id + "' in parents and name contains 'fit'",
                "pageSize":10, "fields":"nextPageToken, files(id, name)"}
            if page_token:
                print("next page")
                params['pageToken'] = page_token
            items = service.files().list(**params).execute()
            for item in items['files']:
                print(item['name'])
                do_download(service, item['id'],
                  "../../data/" + this_dir + "/" + item['name'])
            page_token = items.get('nextPageToken')
            if not page_token:
                break
            

if __name__ == '__main__':
    main()
