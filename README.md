# DigiLib — Digital Library Management System
### Production-Ready | WhatsApp + SMS Reminders | Free Cloud Hosting

---

## Quick Start (Local)

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# 2. Install packages
pip install -r requirements.txt

# 3. Run
python app.py

# Open: http://localhost:5000
# Admin: http://localhost:5000/admin/login  (admin / admin123)
```

---

## Deploy Online — FREE on Render.com

Your app will get a public URL like: `https://digilib.onrender.com`

### Step 1 — Push to GitHub

```bash
# In your project folder:
git init
git add .
git commit -m "DigiLib initial commit"

# Create a new repo at github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/digilib.git
git push -u origin main
```

### Step 2 — Deploy on Render

1. Go to **https://render.com** → Sign up free
2. Click **"New +"** → **"Web Service"**
3. Connect your **GitHub account** → Select your `digilib` repo
4. Fill in these settings:

| Field | Value |
|---|---|
| Name | digilib |
| Environment | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:application --bind 0.0.0.0:$PORT --workers 2` |

5. Click **"Add Environment Variable"** and add:

| Key | Value |
|---|---|
| `SECRET_KEY` | (click Generate) |
| `ADMIN_USERNAME` | admin |
| `ADMIN_PASSWORD` | YourSecurePassword123 |
| `APP_URL` | https://digilib.onrender.com |

6. Click **"Create Web Service"** → Wait 2-3 minutes → Your app is live!

> **Note:** Free Render apps sleep after 15 mins of inactivity. First load may take ~30 seconds.
> Upgrade to Starter ($7/month) for always-on.

---

## Deploy on Railway.app (Alternative)

1. Go to **https://railway.app** → Sign up with GitHub
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select your repo → Railway auto-detects Python
4. Go to **Variables** tab → Add the same env vars as above
5. Your app gets a URL like `https://digilib.up.railway.app`

---

## Setup WhatsApp & SMS Notifications

### Option A — Twilio (WhatsApp + SMS)
Free trial gives $15 credit (~1000 WhatsApp messages)

1. Sign up at **https://www.twilio.com**
2. Go to Console → get your **Account SID** and **Auth Token**
3. For WhatsApp: Go to **Messaging → Try it out → WhatsApp** → Join sandbox
4. Add these environment variables (in Render dashboard or .env file):

```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP=whatsapp:+14155238886
TWILIO_PHONE=+1234567890
```

### Option B — Fast2SMS (India SMS — Very Cheap)
Rs.10 = ~500 SMS messages. No WhatsApp, just SMS.

1. Sign up at **https://www.fast2sms.com**
2. Go to **Dev API** → Copy your API Key
3. Add environment variable:
```
FAST2SMS_API_KEY=your_api_key_here
```

### Testing Notifications
1. Login to Admin Panel
2. Go to **Admin → Notifications**
3. Enter a mobile number → Select channel → Click **Send Test**

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | YES | Random secret string (use Generate in Render) |
| `ADMIN_USERNAME` | YES | Admin login username |
| `ADMIN_PASSWORD` | YES | Admin login password |
| `APP_URL` | YES | Your public URL e.g. https://digilib.onrender.com |
| `DATABASE_URL` | No | PostgreSQL URL (auto-set if using Render DB) |
| `TWILIO_ACCOUNT_SID` | No | For WhatsApp/SMS via Twilio |
| `TWILIO_AUTH_TOKEN` | No | For WhatsApp/SMS via Twilio |
| `TWILIO_WHATSAPP` | No | Twilio WhatsApp sender number |
| `TWILIO_PHONE` | No | Twilio SMS sender number |
| `FAST2SMS_API_KEY` | No | For cheap India SMS |
| `REMINDER_DAYS_BEFORE` | No | Days before due date to send reminder (default: 3) |

---

## How WhatsApp Notifications Work

| Event | Message Sent |
|---|---|
| Student Registration | Booking details + receipt number + fee |
| Mark as Paid | Payment confirmation + next renewal date |
| Monthly Renewal | Reminder 3 days before due date |
| Renewal Collected | Confirmation with amount paid |

Admin can also:
- **Send All** — bulk send WhatsApp/SMS to all overdue students
- **Send individual** — one button per student in reminders table
- **View logs** — full notification history in Admin → Notifications

---

## Project Structure

```
digilib/
├── app.py              # Entry point + app factory
├── config.py           # All settings (env var based)
├── models.py           # Database models (6 tables)
├── routes.py           # All URL routes
├── notifications.py    # WhatsApp + SMS service
├── requirements.txt    # Python dependencies
├── Procfile            # For Render/Railway/Heroku
├── render.yaml         # Render one-click deploy config
├── .env.example        # Environment variables template
├── .gitignore
├── templates/          # 14 HTML templates
└── static/
    ├── css/style.css
    └── js/main.js
```

---

## Database Tables

| Table | Purpose |
|---|---|
| `admins` | Admin login with hashed passwords |
| `shifts` | 3 daily shifts |
| `seats` | 92 seats |
| `students` | Registered students |
| `bookings` | Seat + shift + student links |
| `payments` | Fee with discount + payment mode |
| `fee_reminders` | Monthly renewal tracking |
| `notification_logs` | WhatsApp/SMS history |

---

## Upgrade to PostgreSQL (Recommended for Production)

1. In Render → **New +** → **PostgreSQL** → Create free DB
2. Copy the **Internal Database URL**
3. Add as env var: `DATABASE_URL=postgresql://...`
4. Restart your web service — tables auto-create!
