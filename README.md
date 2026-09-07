# UChat 💬

**A WhatsApp-inspired real-time chat application built from scratch with Python and Flask.**

UChat is a full-stack messaging application designed to demonstrate how a modern chat system works behind the scenes.

Users can create accounts, update their profiles, start one-to-one conversations, send messages, and see unread messages and recent conversations through a responsive WhatsApp-inspired interface.

The application uses lightweight polling to create a near-real-time messaging experience without relying on external chat services or WebSocket infrastructure.

![UChat screenshot](screenshot.png)

## ✨ What You Can Try

* **Create an account** and securely log in
* **Start conversations** with other registered users
* **Send and receive messages** between accounts
* **See unread message indicators** and conversation previews
* **View timestamps** on messages
* **Edit your profile**, including display name and status
* **Use the application on desktop or mobile-sized screens**

To experience the chat functionality, open the application in two browser windows or an incognito window and log in with different accounts.

## 🛠️ Built With

* **Python**
* **Flask**
* **Flask-SQLAlchemy**
* **Flask-Login**
* **Jinja2**
* **SQLite**
* **Vanilla CSS**
* **JavaScript**

No chat SDK or UI framework is used. The messaging system, database structure, authentication, and interface are implemented specifically for this project.

## ⚙️ How It Works

### Authentication

User sessions are managed with Flask-Login, while passwords are securely hashed using Werkzeug.

### Messaging

Every message is stored in the database with information such as:

* Sender
* Recipient
* Message content
* Timestamp
* Read status

### Near Real-Time Updates

Instead of requiring a WebSocket server, UChat periodically checks for new messages using lightweight HTTP polling.

This provides a real-time-feeling experience while keeping the architecture simple and easy to deploy.

### Read Status

Messages can be marked as read when the recipient opens or polls the conversation.

## 🎯 What This Project Demonstrates

UChat demonstrates practical backend and full-stack development concepts including:

* User authentication
* Password security
* Relational database design
* CRUD operations
* Session management
* REST-style API endpoints
* Asynchronous-feeling UI updates
* Responsive frontend development
* Server-side templating
* Database-backed messaging

## 🚀 Possible Improvements

The application could be extended with:

* WebSocket-based real-time messaging
* Image and file sharing
* Group conversations
* Typing indicators
* Online/offline status
* Message reactions
* Message editing and deletion
* Push notifications

## 📁 Project Structure

```text
uchat/
├── app.py
├── requirements.txt
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── index.html
│   └── profile.html
└── static/
    ├── css/style.css
    └── js/app.js
```
