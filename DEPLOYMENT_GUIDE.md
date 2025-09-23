# 🚀 Car Management API - Render Deployment Guide

## 📋 Prerequisites
- GitHub account
- Render account (sign up at https://render.com)
- Your code pushed to a GitHub repository

## 🛠️ Project Setup Status

✅ **Your project is now configured for:**
- **Local Development:** SQLite database (automatic)
- **Production (Render):** PostgreSQL database (automatic)
- **Automatic switching** between databases based on environment

## 📁 Files Created for Deployment

1. **`build.sh`** - Build script for Render
2. **`render.yaml`** - Render configuration file
3. **`.gitignore`** - Excludes unnecessary files
4. **`runtime.txt`** - Python version specification
5. **`requirements.txt`** - Python dependencies

## 🚀 Deployment Steps

### Step 1: Push to GitHub

```bash
# Initialize git (if not already done)
cd "/home/ahmed/Desktop/car managment/venv/src"
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - Car Management API"

# Add your GitHub repository (replace with your repo URL)
git remote add origin https://github.com/YOUR_USERNAME/car-management-api.git

# Push to GitHub
git push -u origin main
```

### Step 2: Deploy to Render

#### Option A: Automatic Deployment (Using render.yaml)

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub account
4. Select your repository
5. Render will detect `render.yaml` and set everything up automatically
6. Click **"Apply"**
7. Wait for deployment (5-10 minutes)

#### Option B: Manual Deployment

1. Go to [Render Dashboard](https://dashboard.render.com)

2. **Create PostgreSQL Database:**
   - Click **"New +"** → **"PostgreSQL"**
   - Name: `carmanagement-db`
   - Database: `carmanagement`
   - User: `carmanagement`
   - Region: Oregon (or your preferred)
   - Click **"Create Database"**
   - Copy the **Internal Database URL**

3. **Create Web Service:**
   - Click **"New +"** → **"Web Service"**
   - Connect GitHub repository
   - Name: `car-management-api`
   - Environment: `Python`
   - Build Command: `./build.sh`
   - Start Command: `gunicorn project.wsgi:application`
   
4. **Add Environment Variables:**
   - `DATABASE_URL`: (paste the Internal Database URL from step 2)
   - `SECRET_KEY`: (click "Generate" for random value)
   - `DEBUG`: `False`
   - `ALLOWED_HOSTS`: `.onrender.com`
   
5. Click **"Create Web Service"**

### Step 3: Verify Deployment

After deployment completes (5-10 minutes):

1. Your API will be available at: `https://car-management-api.onrender.com`
2. Test endpoints:
   - `GET https://car-management-api.onrender.com/api/cars/`
   - `POST https://car-management-api.onrender.com/api/cars/`

## 🔧 Environment Configuration

### Local Development (Automatic)
- Database: **SQLite** (no configuration needed)
- Debug: **True**
- Run: `python manage.py runserver`

### Production on Render (Automatic)
- Database: **PostgreSQL** (configured via DATABASE_URL)
- Debug: **False**
- Static files: Served via WhiteNoise
- WSGI Server: Gunicorn

## 📝 Important Notes

1. **Free Tier Limitations:**
   - Web service sleeps after 15 minutes of inactivity
   - First request after sleep takes 30-60 seconds
   - PostgreSQL database expires after 90 days

2. **Keep Service Awake (Optional):**
   - Use [UptimeRobot](https://uptimerobot.com) to ping every 14 minutes
   - Set URL: `https://car-management-api.onrender.com/api/cars/`

3. **Database Migrations:**
   - Migrations run automatically during deployment (in `build.sh`)
   - No manual intervention needed

## 🔍 Troubleshooting

### If deployment fails:

1. **Check Logs:**
   - Go to Render Dashboard → Your Service → "Logs"

2. **Common Issues:**
   - **Import Error:** Ensure all packages in requirements.txt
   - **Database Error:** Check DATABASE_URL is set correctly
   - **Build Error:** Check Python version in runtime.txt

3. **Re-deploy:**
   - Go to "Manual Deploy" → "Deploy latest commit"

## 📊 Monitoring

- **Service Health:** https://dashboard.render.com
- **Database:** Check connections and storage in PostgreSQL dashboard
- **Logs:** Real-time logs in Render dashboard

## 🎉 Success Checklist

- [ ] Code pushed to GitHub
- [ ] Render account created
- [ ] Service deployed via render.yaml or manually
- [ ] Database connected (PostgreSQL)
- [ ] Environment variables set
- [ ] API endpoints working
- [ ] (Optional) UptimeRobot configured

## 📚 API Endpoints

Once deployed, your API will be available at:

- **Base URL:** `https://car-management-api.onrender.com/api/`
- **Create Car:** `POST /api/cars/`
- **Get All Cars:** `GET /api/cars/`
- **Get Car by ID:** `GET /api/cars/{id}/`
- **Update Car:** `PUT /api/cars/{id}/`
- **Delete Car:** `DELETE /api/cars/{id}/`

## 💡 Next Steps

1. Add authentication (Django REST Framework Token/JWT)
2. Add API documentation (Swagger/ReDoc)
3. Set up CI/CD with GitHub Actions
4. Add more models and relationships
5. Implement pagination and filtering

---

**Need Help?** 
- Render Docs: https://render.com/docs
- Django Deployment: https://docs.djangoproject.com/en/5.2/howto/deployment/

Good luck with your deployment! 🚀