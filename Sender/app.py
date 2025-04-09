from __future__ import print_function
from googleapiclient import discovery
from httplib2 import Http
from oauth2client import file, client, tools
from flask import Flask, render_template, request,jsonify
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
import webview

app=Flask('__name__',template_folder='templates')
DRIVE=None

#Index Page
@app.route('/')
def index():
    return render_template("index.html")

#Function to login using google api
def login():
    SCOPES = 'https://www.googleapis.com/auth/drive'
    store = file.Storage('storage.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('client_id.json', SCOPES)
        creds = tools.run_flow(flow, store)
    else:
        print("User Authenticated")
    global DRIVE
    DRIVE = discovery.build('drive', 'v3', http=creds.authorize(Http()))
    return render_template("index.html")

#Pin Verification
@app.route('/verify_pin', methods=['POST'])
def verify_pin():
    login()
    pin = request.form['pin']
    if pin=="4444":
        return truck()
    else:
        return render_template('index.html')
    
#Main page
@app.route('/truck')
def truck():
    try:
        response = DRIVE.files().list(
            q="mimeType='application/vnd.google-apps.folder' and 'root' in parents and trashed=false",
            fields="files(id, name)"
        ).execute()
        truck_folders = [file['name'] for file in response.get('files', [])]
        print("Truck Folders Found:", truck_folders)
        return render_template('truck.html', truck_folders=truck_folders)
    except Exception as e:
        print(f"Error fetching truck folders: {e}")
        return "An error occurred while fetching truck folders.", 500

#Function search for subfolders in gdrive
def search_subfolders(DRIVE, parent_folder_id,sub_folder):
    query = f"mimeType='application/vnd.google-apps.folder' and '{parent_folder_id}' in parents and trashed=false"
    results = DRIVE.files().list(
        q=query,
        fields="files(id, name)"
    ).execute()
    folders = results.get('files', [])
    print("Debug",folders)
    if not folders:
        print('No subfolders found.')
        try:
            file_metadata = {
                "name": sub_folder,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [parent_folder_id],
                }
            file = DRIVE.files().create(body=file_metadata, fields="id").execute()
            print(f'Folder ID: "{file.get("id")}".')
            return file.get('id')
        except HttpError as error:
            print(f"An error occurred: {error}")
    else:
        print('Subfolders:')
        for folder in folders:
            if(folder['name'] == sub_folder):
              print(f"Name: {folder['name']}, ID: {folder['id']}")
              return folder['id'] 
        else:
            try:
                file_metadata = {
                    "name": sub_folder,
                    "mimeType": "application/vnd.google-apps.folder",
                    "parents": [parent_folder_id],
                    }
                file = DRIVE.files().create(body=file_metadata, fields="id").execute()
                print(f'Folder ID: "{file.get("id")}".')
                return file.get("id")
            except HttpError as error:
                print(f"An error occurred: {error}")
    return None

#Upload File in gdrive 
@app.route('/upload_file', methods=['POST'])
def upload_file():
    try:
        truck_no = request.form.get('truck_no')
        date = request.form.get('date')
        uploaded_files = request.files.getlist('files[]') 
        print(f"Received data -> Truck: {truck_no}, Date: {date}, Number of Files: {len(uploaded_files)}")
        if not uploaded_files or len(uploaded_files) == 0:
            return jsonify({"success": False, "error": "No files provided"})
        print("Searching for truck folder...")
        response = DRIVE.files().list(
            q=f"mimeType='application/vnd.google-apps.folder' and name='{truck_no}' and trashed=false",
            fields="files(id, name)"
        ).execute()
        folders = response.get('files', [])
        if not folders:
            return jsonify({"success": False, "error": "Truck folder not found"})
        folder_id = folders[0]['id']
        print(f"Truck folder found: {folder_id}")
        print("Searching/Creating date subfolder...")
        subfolder_id = search_subfolders(DRIVE, folder_id, date)
        if not subfolder_id:
            return jsonify({"success": False, "error": "Date subfolder creation failed"})
        print(f"Date subfolder found/created: {subfolder_id}")
        uploaded_file_names = []
        for uploaded_file in uploaded_files:
            if uploaded_file:
                print(f"Uploading file: {uploaded_file.filename}")
                file_metadata = {'name': uploaded_file.filename, 'parents': [subfolder_id]}
                media = MediaIoBaseUpload(uploaded_file.stream, mimetype=uploaded_file.mimetype)
                DRIVE.files().create(body=file_metadata, media_body=media, fields='id').execute()
                uploaded_file_names.append(uploaded_file.filename)
            else:
                print("Empty file detected, skipping.")
        print("All files uploaded successfully.")
        return jsonify({"success": True, "uploaded_files": uploaded_file_names})
    except Exception as e:
        print(f"Error uploading files: {e}")
        return jsonify({"success": False, "error": str(e)})

#Function for truck details
@app.route('/truck_details',methods=['POST','GET'])
def truck_details():
    global DRIVE
    try:
        response = DRIVE.files().list(
            q="mimeType='application/vnd.google-apps.folder' and 'root' in parents and trashed=false",
            fields="files(id, name)"
        ).execute()
        truck_folders = [file['name'] for file in response.get('files', [])]
        print("Truck Folders Found:", truck_folders)
    except Exception as e:
        print(f"Error fetching truck folders: {e}")
        return "An error occurred while fetching truck folders.", 500
    if request.method == 'POST':
        truck_no = request.form['truck_no']
        date = request.form['date']
    else:
        truck_no = request.args.get('truck_no')
        date = request.args.get('date')
    print(f"Truck No: {truck_no}, Date: {date}")
    try:
        files = []
        page_token = None
        folder_id=None
        while True:
            response = (
                DRIVE.files()
                .list(
                    q="mimeType='application/vnd.google-apps.folder'",
                    spaces="drive",
                    fields="nextPageToken, files(id, name)",
                    pageToken=page_token,
                )
                .execute()
            )
            for file in response.get("files", []):
                if file.get("name")==truck_no:
                    folder_id=file.get("id")
                    print("d found subfolder")
                    print(f'Found file: {file.get("name")}, {file.get("id")}')
                    break
            files.extend(response.get("files", []))
            page_token = response.get("nextPageToken", None)
            subfolder_id=search_subfolders(DRIVE,folder_id,date)
            if subfolder_id:
                query = f"'{subfolder_id}' in parents and trashed=false"
                response = DRIVE.files().list(
                    q=query,
                    spaces='drive',
                    fields='files(id, name, mimeType, webViewLink, createdTime, modifiedTime)'
                ).execute()
                files = response.get('files', [])
                print(f"debug{files}")
                if not files:
                    print(f"No files found inside '{date}' subfolder.")
                    break
                else:
                    print(f"Files in subfolder '{date}':")
                    for f in files:
                        print(f"Name: {f['name']}, Type: {f['mimeType']},file-id{f['id']}")
                    if page_token is None:
                        break
            else:
                break       
    except HttpError as error:
        print(f"An error occurred: {error}")
        files = None
    return render_template('truck.html',truck_folders=truck_folders, files=files, truck_no=truck_no, date=date)

#Function to add new trucks in gdrive 
@app.route('/add_truck',methods=['POST'])
def add_truck():
    truck_no = request.form['truck_no']
    try:
        file_metadata = {
            "name": truck_no,
            "mimeType": "application/vnd.google-apps.folder",
            }
        file = DRIVE.files().create(body=file_metadata, fields="id").execute()
        print(f'Folder ID: "{file.get("id")}".')
    except HttpError as error:
        print(f"An error occurred: {error}")
    return truck()

#Function to remove file from the gdrive
@app.route('/remove_file', methods=['POST'])
def remove_file():
    FILE_ID = request.form['file_id']
    truck_no = request.form['truck_no']
    date = request.form['date']
    print(f"Truck No: {truck_no}, Date: {date}")
    print(f"{FILE_ID}")
    body_value = {'trashed': True}
    response = DRIVE.files().update(fileId=FILE_ID, body=body_value).execute()
    return jsonify({'success': True})

webview.create_window("LogiDocs", app,maximized=True)
if __name__=="__main__":
    webview.start()
