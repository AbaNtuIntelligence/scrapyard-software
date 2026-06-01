# ScrapSoft - Scrap Yard Management System

A complete weighing and transaction management system for small to medium scrap yards.

## Features
- 📊 Dashboard with daily statistics
- 👥 Seller registration and tracking (with ID number for police register)
- 📦 Material type management with dynamic pricing
- 💰 Transaction recording with automatic amount calculation
- 📈 Reports (daily/weekly/monthly/yearly)
- 🔌 Physical scale integration via serial port
- 🎫 Printable transaction tickets
- 📱 Mobile-friendly responsive design

## Technology Stack
- Backend: Python 3.12+ with Flask
- Database: SQLite
- Frontend: Bootstrap 5, Font Awesome
- Scale Integration: PySerial

## Installation

### 1. Clone the repository
\\\ash
git clone https://github.com/yourusername/scrapsoft.git
cd scrapsoft
\\\

### 2. Create virtual environment
\\\ash
python -m venv .venv
source .venv/Scripts/activate  # Windows
# or
source .venv/bin/activate  # Linux/Mac
\\\

### 3. Install dependencies
\\\ash
pip install -r requirements.txt
\\\

### 4. Configure settings
\\\ash
cp config.example.py config.py
# Edit config.py with your scale's COM port
\\\

### 5. Run the application
\\\ash
python run.py
\\\

### 6. Open browser
Navigate to http://localhost:5000

## Hardware Setup

### Connecting a Scale
1. Connect your digital scale/terminal via USB-to-Serial adapter
2. Find the COM port (Windows: Device Manager, Linux: ls /dev/ttyUSB*)
3. Update SCALE_PORT in config.py
4. The system will automatically read weights

## Default Login
- Username: admin
- Password: admin123

*Note: Change credentials in production!*

## Police Register Compliance
The system automatically captures seller ID numbers and generates reports for police inspection.

## License
MIT

## Support
For issues or features, please open a GitHub issue.
