from __future__ import print_function
from googleapiclient import discovery
from httplib2 import Http
from oauth2client import file, client, tools 
from flask import Flask, render_template, request,jsonify 
import os
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
import win32print
import win32api
import webview

app=Flask('__name__',template_folder='templates')
DRIVE=None
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
LOG_FILE = 'download_log.csv'

#Function to print pdf
def print_pdf(file_path):
    try:
        printer_name = win32print.GetDefaultPrinter()
        print("Default printer:", printer_name)
        printer_name = win32print.GetPrinter(win32print.OpenPrinter(printer_name), 2)['pPrinterName']
        printer_handle = win32print.OpenPrinter(printer_name)
        hPrinter = win32print.OpenPrinter(printer_name)
        properties = win32print.GetPrinter(hPrinter, 2)
        print("Using printer:", printer_name)
        win32api.ShellExecute(
            0,
            "printto",
            file_path,
            '"{}"'.format(printer_name),
            ".",
            0
        )
        win32print.ClosePrinter(printer_handle)

    except Exception as e:
        print("Error in print dialog flow:", e)

#Index Page
@app.route('/')
def index():
    return render_template("index.html")

#Google API Authentication
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

#Function to veify pin
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

#Function to search for subfolders
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

#Fetching truck details
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
                import csv
                log_path = 'download_log.csv'
                downloaded_file_ids = set()
                if os.path.exists(log_path):
                    with open(log_path, mode='r', newline='') as log_file:
                        reader = csv.DictReader(log_file)
                        for row in reader:
                            if row['truck_no'] == truck_no and row['date'] == date:
                                downloaded_file_ids.add(row['file_id'])
                for f in files:
                    f['downloaded'] = f['id'] in downloaded_file_ids
                print(f"debug{files}")
                if not files:
                    print(f"No files found inside '{date}' subfolder.")
                    break
                else:
                    print(f"Files in subfolder '{date}':")
                    for f in files:
                        print(f"Name: {f['name']}, Type: {f['mimeType']}")
                    if page_token is None:
                        break
            else:
                return render_template('truck.html', truck_folders=truck_folders)     
    except HttpError as error:
        print(f"An error occurred: {error}")
        files = None
    return render_template('truck.html',truck_folders=truck_folders, files=files, truck_no=truck_no, date=date)

#Downloading file (each file) using google api
@app.route('/download_file',methods=['POST'])
def download_file(fids=None,tno=None,dt=None,f_name=None,nocall=True):
    import csv
    from flask import request
    if request.method == 'POST' and nocall:
        FILE_ID = request.form['file_id']
        truck_no = request.form['truck_no']
        date = request.form['date']
        file_name=request.form['name']
    else:
        FILE_ID = fids
        truck_no = tno
        date = dt
        file_name=f_name
    print(f"Truck No: {truck_no}, Date: {date}")
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, mode='r', newline='') as log_file:
            reader = csv.DictReader(log_file)
            for row in reader:
                if row['file_id'] == FILE_ID and row['date'] == date:
                    existing_path = row['file_path']
                    print("File already downloaded. Skipping download.")
                    os.startfile(existing_path)
                    return jsonify({
                        "success": True,
                        "file_path": existing_path,
                        "file_id": FILE_ID,
                        "skipped": True
                    })
    try:
        request = DRIVE.files().get_media(fileId=FILE_ID)
        DOWNLOAD_FOLDER_D = os.path.join(DOWNLOAD_FOLDER,date,truck_no)
        os.makedirs(DOWNLOAD_FOLDER_D, exist_ok=True)
        file_path = os.path.join(DOWNLOAD_FOLDER_D,file_name)
        file = open(file_path, "wb")
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}% complete.")
        file.close()  
        os.startfile(file_path)  
        if file_name.lower().endswith('.pdf'):
            print("Calling print_pdf for:", file_path)
            print_pdf(file_path)  
        file_exists = os.path.isfile(LOG_FILE)
        with open(LOG_FILE, mode='a', newline='') as log_file:
            fieldnames = ['file_id', 'date', 'truck_no', 'file_name', 'file_path']
            writer = csv.DictWriter(log_file, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                'file_id': FILE_ID,
                'date': date,
                'truck_no': truck_no,
                'file_name': file_name,
                'file_path': file_path
            })
        return jsonify({"success": True, "file_path": file_path,"file_id": FILE_ID})
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

#Downloading selected files
@app.route('/process_selected_files',methods=['POST'])
def selected_files():
    data=request.get_json()
    files=data.get('file_ids',[])
    print(files)
    l=[]
    m=[]
    for f in files:
        k=download_file(f['file_id'],f['truck_no'],f['date'],f['file_name'],False)
        if k: 
            k_data = k.get_json()  
            l.append(k_data.get('file_path')) 
            if k_data.get('file_path', '').lower().endswith('.pdf'):
                print_pdf(k_data['file_path'])
            m.append(k_data.get('file_id'))
    print(l)
    return jsonify({"success": True,'file_paths':l,'file_id':m})

#Viewing pending files to be downloaded
@app.route('/pending_summary', methods=['POST'])
def pending_summary():
    import csv
    selected_date = request.form['date']
    print(f"Generating summary for date: {selected_date}")
    try:
        response = DRIVE.files().list(
            q="mimeType='application/vnd.google-apps.folder' and 'root' in parents and trashed=false",
            fields="files(id, name)"
        ).execute()
        truck_folders = response.get('files', [])
        downloaded_file_ids = set()
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, mode='r', newline='') as log_file:
                reader = csv.DictReader(log_file)
                for row in reader:
                    if row['date'] == selected_date:
                        downloaded_file_ids.add(row['file_id'])
        summary = []
        files_to_download = []
        for truck in truck_folders:
            truck_name = truck['name']
            truck_id = truck['id']
            subfolder_id = search_subfolders(DRIVE, truck_id, selected_date)
            if not subfolder_id:
                continue
            query = f"'{subfolder_id}' in parents and trashed=false"
            response = DRIVE.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, mimeType)'
            ).execute()
            files = response.get('files', [])
            total = len(files)
            pending = 0
            pending_files = []
            for f in files:
                if f['id'] not in downloaded_file_ids:
                    pending += 1
                    pending_files.append({
                        'file_id': f['id'],
                        'file_name': f['name'],
                        'truck_no': truck_name,
                        'date': selected_date
                    })
            if total > 0:
                summary.append({
                    'truck': truck_name,
                    'total': total,
                    'pending': pending,
                    'files': pending_files
                })
                files_to_download.extend(pending_files)
        return jsonify({'summary': summary})
    except Exception as e:
        print(f"Error generating pending summary: {e}")
        return jsonify({'error': str(e)}), 500
    
webview.create_window("LogiDocs", app,maximized=True)
if __name__=="__main__":
    webview.start()
