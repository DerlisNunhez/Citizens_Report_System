# Deployment Guide - Render.com

## Step-by-Step Deployment Instructions

### 1. Push Your Code to GitHub

First, make sure all your changes are committed and pushed:

```bash
cd C:\Users\mique\Desktop\pothole\Citizens_Report_System
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### 2. Create a Render Account

1. Go to https://render.com
2. Sign up with your GitHub account
3. Authorize Render to access your repositories

### 3. Create a New Web Service

1. Click **"New +"** button → Select **"Web Service"**
2. Connect your GitHub repository: `Citizens_Report_System`
3. Configure the service:

**Basic Settings:**
- **Name**: `citizens-report-system` (or your preferred name)
- **Region**: Choose closest to your users (e.g., Oregon USA)
- **Branch**: `main` (or your default branch)
- **Root Directory**: Leave empty
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`

**Instance Type:**
- Select **"Free"** (for testing) or **"Starter"** ($7/month for better performance)

### 4. Add Environment Variables

Click **"Advanced"** → **"Add Environment Variable"**:

| Key | Value |
|-----|-------|
| `SECRET_KEY` | `your-super-secret-random-key-here-change-this` |
| `PYTHON_VERSION` | `3.12.0` |

**To generate a secure SECRET_KEY:**
```python
import secrets
print(secrets.token_hex(32))
```

### 5. Deploy!

1. Click **"Create Web Service"**
2. Wait for deployment (takes 2-5 minutes)
3. Once done, you'll get a URL like: `https://citizens-report-system.onrender.com`

### 6. Post-Deployment

**Important Notes:**

⚠️ **Database Persistence**: Render's free tier uses ephemeral storage. Your SQLite database will reset on each deploy. For production, consider:
- Upgrading to a paid plan with persistent disk
- Using Render's PostgreSQL database (recommended for production)

⚠️ **File Uploads**: Uploaded images will also be lost on redeploy with the free tier. For production:
- Use cloud storage like AWS S3, Cloudinary, or Render's persistent disk

⚠️ **Initial Setup**: The app will create test users automatically:
- Admin: `admin@ejemplo.com` / `admin123`
- User: `usuario@ejemplo.com` / `usuario123`

### 7. Optional: Use PostgreSQL (Recommended for Production)

If you want persistence:

1. Create a PostgreSQL database in Render
2. Install `psycopg2-binary` in requirements.txt
3. Update `database.py` to use PostgreSQL instead of SQLite
4. Add `DATABASE_URL` environment variable

### Troubleshooting

**Deployment fails?**
- Check the logs in Render dashboard
- Ensure all files are committed to GitHub
- Verify `requirements.txt` is correct

**App crashes?**
- Check logs: Click on your service → **"Logs"**
- Common issues:
  - Missing environment variables
  - Database connection errors
  - File permission issues

**Database resets?**
- This is normal on free tier (ephemeral storage)
- Upgrade to paid plan or use PostgreSQL

### Custom Domain (Optional)

1. In Render dashboard, go to your service
2. Click **"Settings"** → **"Custom Domain"**
3. Add your domain and follow DNS instructions

---

## Quick Reference

**Render Dashboard**: https://dashboard.render.com
**Your app will be at**: `https://[your-service-name].onrender.com`

**Logs**: Service → Logs
**Redeploy**: Service → Manual Deploy → Deploy latest commit
**Environment Variables**: Service → Environment → Add Environment Variable
