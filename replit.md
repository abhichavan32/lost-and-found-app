# Lost and Found Application

This is a Flask-based web application for managing lost and found items with full user authentication and notification system. Users can register accounts, log in, and manage their personal lost and found items. The system automatically sends notifications to all users when new lost items are posted, helping to increase the chances of reuniting people with their belongings. The application uses MySQL database for persistent storage and includes a comprehensive dashboard for users to manage their items and notifications.

## Features

- User authentication (register, login, logout)
- Post lost or found items with images
- Browse and search items by category and location
- Automatic notifications system
- User dashboard
- Item management (create, edit, delete)

## Technical Stack

- **Framework**: Flask
- **Database**: MySQL with SQLAlchemy ORM
- **Authentication**: Flask-Login
- **File Storage**: Local file system
- **Frontend**: HTML, CSS, JavaScript