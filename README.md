# GreenBin - Smart Plastic Recycling App

Description
-----------
GreenBin is a web application that gamifies plastic recycling by rewarding users for depositing plastic into smart bins. Users scan bin QR codes to earn points, redeem rewards, and track environmental impact.

Features
--------
- QR code scanning for smart bins
- Point-based rewards system
- Rewards redemption (gift cards, coupons, transfers)
- User profiles, achievements, and leaderboards
- Admin tools for bin management and monitoring
- Analytics dashboard and exportable reports
- Mobile-responsive UI

Project Structure
-----------------
flask/
- app.py                 # Main Flask application entry
- requirements.txt       # Python dependencies
- README.md              # Project documentation
- models/                # Database models
  - __init__.py
  - models.py
- routes/                # Route handlers and API endpoints
  - main.py
  - auth.py
  - admin.py
  - api.py
- templates/             # Jinja2 templates
  - base.html
  - index.html
  - dashboard.html
  - scan.html
  - redeem.html
  - analytics.html
  - profile.html
  - auth/
    - login.html
    - register.html
  - admin/
    - bins.html
- static/                # CSS, JS, images

Quick Start
-----------
Prerequisites
- Python 3.8+
- pip

Install and run
1. Clone the repo and enter project directory:
   cd GreenBin
2. Install dependencies:
   pip install -r requirements.txt
3. Run locally:
   flask run --host=0.0.0.0 --port=5000
4. Open: http://localhost:5000

How It Works
------------
User flow:
1. Register or log in.
2. Locate a smart bin and deposit plastic.
3. Scan the bin's QR code via the app.
4. Points are credited automatically.
5. Redeem points for rewards or view impact statistics.

Admin flow:
- Register bins, generate QR codes, monitor capacity, and view aggregated analytics.

Technical Details
-----------------
- Backend: Flask, Flask-Login
- Database: SQLite (configurable to PostgreSQL/MySQL)
- ORM: SQLAlchemy
- Frontend: Bootstrap 5, Chart.js, Font Awesome
- Security: Password hashing (Werkzeug), CSRF protection, input validation
- Deployment: WSGI server (Gunicorn) recommended for production

Features Showcase
-----------------
- Real-time points and activity feed
- Weekly/monthly analytics and environmental metrics
- Achievement badges and leaderboards
- Manual QR entry for testing and demo mode

Environmental Impact
--------------------
- Calculates estimated plastic diverted (kg)
- Estimates CO2 emissions saved and tree-equivalent metrics
- Displays community and individual impact over time

Customization
-------------
- Add reward types: update Redemption model and templates
- Adjust point values: modify QR code generation logic
- Change themes: edit base.html and CSS variables
- Extend database: migrate models and update routes

Deployment & Production Notes
-----------------------------
- Set environment variables before production:
  - FLASK_ENV=production
  - SECRET_KEY=your-secret-key
- Use Gunicorn or another WSGI server:
  pip install gunicorn
  gunicorn app:app

Troubleshooting
---------------
- Database issues: remove local DB and reinitialize
- Port conflicts: change port in app.py
- Template errors: verify template paths and names

License
-------
MIT-style license for educational and hackathon use. Modify and reuse as needed.


Happy Recycling! 🌍♻️
