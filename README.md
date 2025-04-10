
# 🚛 LogiDocs - Truck Transport Document Manager

**LogiDocs** is a Python Flask-based document management system for transport companies. It reduces manual errors and streamlines the transfer of documents like invoices and bills from dispatch offices to delivery hubs using **Google Drive as a cloud backend**.

---

## 📌 Project Modules

### 1️⃣ Sender Module (Office Side)
- Secure login with shared Google Drive account and PIN (default: `4444`)
- Add new trucks (creates truck folders in Drive)
- Organize documents by date (creates subfolders)
- Upload and view files per truck and date
- Delete unwanted files

### 2️⃣ Receiver Module (Hub Side)
- Fetch truck folders and files for a selected date
- Download and print documents automatically
- Log downloaded files in a CSV to avoid duplicates
- One-click bulk download and printing
- Summary view to check pending/unprinted files by date

---

## ⚙️ Tech Stack

| Layer        | Tools                             |
|--------------|-----------------------------------|
| Frontend     | HTML5, CSS3, JavaScript, Jinja2   |
| Backend      | Python Flask                      |
| File Storage | Google Drive API                  |
| Desktop UI   | PyWebView                         |
| Auth         | `oauth2client` Google OAuth Flow  |
| Extras       | `win32print`, `win32api` (for printing) |

---
## 📊 Screenshots
### Login
![Login](https://github.com/SNIGDHA-VIJAY/LogiDocs/blob/main/Screenshots/Login.png?raw=true)
### Sender App
![Sender](https://github.com/SNIGDHA-VIJAY/LogiDocs/blob/main/Screenshots/Sender.png?raw=true)
### Receiver App
![Receiver](https://github.com/SNIGDHA-VIJAY/LogiDocs/blob/main/Screenshots/Receiver.png?raw=true)
### Sender Sample
![Sender Sample](https://github.com/SNIGDHA-VIJAY/LogiDocs/blob/main/Screenshots/Sender-Sample.png?raw=true)
### Receiver Sample
![Receiver Sample](https://github.com/SNIGDHA-VIJAY/LogiDocs/blob/main/Screenshots/Receiver-Sample.png?raw=true)

---
## 🚀 Getting Started

### ✅ Prerequisites

- Python 3.8+
- `client_id.json` from Google Cloud Console (OAuth credentials)
- Windows OS (for printing support)

### 📦 Install Dependencies

```bash
pip install -r requirements.txt
```

### ▶️ Run Sender App

```bash
cd sender
python app.py
```

### ▶️ Run Receiver App

```bash
cd receiver
python app.py
```

---

## 🗃️ Directory Overview

```
logidocs/
├── sender/          # Upload documents
├── receiver/        # Download & print documents
├── docs/            # Screenshots, architecture
├── requirements.txt
└── README.md
```
---

## 🧠 Smart Features

- Smart folder structure: `/TruckNumber/Date/Files`
- CSV-based download logs to avoid duplicates
- Bulk download and print by selecting a date
- Simple and secure UI with localStorage for truck selection

---

## 🛡️ License

MIT License – use freely with credits 💙

---

## 🤝 Contributing

Contributions and feature suggestions are welcome! Feel free to fork, raise issues, or open a pull request.

---

> Built by Prince Jain & ([@SNIGDHA-VIJAY](https://github.com/SNIGDHA-VIJAY))

