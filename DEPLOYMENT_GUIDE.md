# 🌐 Global Deployment Guide - Smart Library Management System

This guide explains how to deploy your website to the public internet so that anyone anywhere in the world (professors, evaluators, teammates, or interviewers) can open it on their browser or phone.

---

## 🚀 Option 1: Deploy on Render.com (Recommended — 100% Free & Permanent)

**Render.com** provides free cloud hosting for Python/Flask web applications with automatic HTTPS certificates (`https://your-app.onrender.com`).

### Step 1: Push your code to GitHub

Open **PowerShell** or **Terminal** inside your `library-app` folder:

```bash
cd library-app

# Initialize Git
git init
git add .
git commit -m "Initial commit of Smart Library System"
```

Now create a new repository on [GitHub](https://github.com/new) (name it `smart-library-app`), then run:

```bash
git remote add origin https://github.com/YOUR_USERNAME/smart-library-app.git
git branch -M main
git push -u origin main
```

---

### Step 2: Create a Free Web Service on Render

1. Go to [render.com](https://render.com) and sign in using your GitHub account.
2. In the Render Dashboard, click **New +** (top right) and select **Web Service**.
3. Choose **Build and deploy from a Git repository**, and connect your `smart-library-app` repository.
4. Fill in the following settings:
   - **Name**: `smart-library-system` (or any custom name)
   - **Region**: Choose the closest region (e.g. *Singapore* or *Frankfurt*)
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: Select **Free** ($0/month)

---

### Step 3: Configure Environment Variables

Scroll down to the **Environment Variables** section and add:

| Key | Value | Description |
|---|---|---|
| `SECRET_KEY` | `smartlib-super-secret-key-college-dbms` | Flask session encryption key |
| `USE_DB` | `false` *(or `true` if connecting cloud DB)* | `false` runs in ultra-fast Mock mode immediately |

---

### Step 4: Click "Deploy Web Service"

- Render will automatically build the app and deploy it.
- Within 2-3 minutes, you will get your permanent live URL:
  👉 **`https://smart-library-system.onrender.com`**

Anyone in the world can now open this link on their laptop or mobile phone!

---

## 🗄️ Optional: Connecting a Free Cloud PostgreSQL Database

If you want live PostgreSQL running in the cloud (instead of Mock mode):

### 1. Get a Free Cloud PostgreSQL database
- Create a free database on **[Neon.tech](https://neon.tech)** or **[Supabase.com](https://supabase.com)** (both offer free managed PostgreSQL).
- Copy the connection string (`DATABASE_URL`), which looks like:
  `postgresql://neondb_owner:password@ep-xyz.aws.neon.tech/neondb?sslmode=require`

### 2. Populate the Database
From your local machine, run the setup tool with that URL:
```bash
python init_db.py "postgresql://neondb_owner:password@ep-xyz.aws.neon.tech/neondb?sslmode=require"
```
This automatically executes [`sql/setup_database.sql`](file:///c:/Users/poora/OneDrive/Desktop/bits_bytes_hackathon/library-app/sql/setup_database.sql), creating all 9 ER tables and seed rows in the cloud database!

### 3. Update Render Environment Variables
In your Render Dashboard -> **Environment Variables**:
- Set `USE_DB` = `true`
- Add `DATABASE_URL` = `<your_copied_cloud_postgres_url>`

Click **Save Changes** -> Render redeploys and connects to live PostgreSQL!

---

## ⚡ Option 2: Instant Public Link in 60 Seconds (ngrok)

If you are demoing in a hackathon or presenting to someone **right now** from your computer:

1. Download **[ngrok](https://ngrok.com/download)**.
2. Make sure your app is running locally:
   ```bash
   python app.py
   ```
3. In a second terminal window, run:
   ```bash
   ngrok http 5000
   ```
4. ngrok gives you an instant temporary global HTTPS URL:
   👉 `https://xxxx-xx-xx.ngrok-free.app`
5. Anyone in the world can open that URL immediately on their phone or laptop!
