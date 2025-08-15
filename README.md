# Lost and Found Application
pip install -r requirements.txt
python init_db.py
python app.py

## Database Migration to MySQL

### Prerequisites
1. MySQL Server installed and running
2. Python 3.x installed
3. pip (Python package installer)

### MySQL Server Setup

#### Windows
1. Download and install MySQL Server from the official website
2. During installation:
   - Choose "Server only" or "Custom" installation
   - Set root password to 'root' (for development only)
   - Make sure MySQL service is installed and running
3. Verify MySQL service is running:
   - Open Services (services.msc)
   - Find "MySQL80" or similar
   - Ensure its status is "Running"

#### Troubleshooting MySQL Connection
- If you get connection errors:
  1. Verify MySQL service is running
  2. Check if port 3306 is not blocked by firewall
  3. Verify root password is correct
  4. Try connecting using MySQL Workbench or command line client

### Application Setup

1. Install required packages:
```bash
pip install -r requirements.txt
```

2. Initialize the database:
```bash
python init_db.py
```
The script will:
- Check MySQL connection (5 attempts)
- Create database if not exists
- Report any connection issues

3. Start the application:
```bash
python app.py
```

### Environment Variables
You can customize the database connection using environment variables:
- `DATABASE_URL`: MySQL connection URL (default: mysql://root:root@localhost/lost_and_found)
- `SESSION_SECRET`: Secret key for session management

### Production Deployment
1. Use strong passwords
2. Set secure environment variables
3. Configure proper MySQL user permissions
4. Enable MySQL security features
5. Regular backups

### Migration Notes
- The application will automatically create all necessary tables when started
- Backup any existing SQLite data before migration
- For production, use environment variables for secure credentials