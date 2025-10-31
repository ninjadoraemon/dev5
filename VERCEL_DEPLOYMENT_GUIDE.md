# Vercel Deployment Guide

This guide will help you deploy your Digital Store e-commerce application to Vercel.

## Prerequisites

1. **GitHub Account** - Your code must be in a GitHub repository
2. **Vercel Account** - Sign up at [vercel.com](https://vercel.com)
3. **MongoDB Atlas** - Your database is already hosted on Atlas ✓
4. **Cloudinary Account** - Your media storage is already set up ✓

## Project Structure for Vercel

```
/app/
├── api/                    # Backend as serverless functions
│   ├── index.py           # Entry point for Vercel
│   └── requirements.txt   # Python dependencies
├── backend/               # Your FastAPI application
│   ├── server.py         # Main FastAPI app
│   └── .env              # Local environment variables (not deployed)
├── frontend/             # React application
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── .env              # Frontend environment variables
├── vercel.json           # Vercel configuration
└── package.json          # Root package.json for build scripts
```

## Step-by-Step Deployment

### Step 1: Push Your Code to GitHub

```bash
# If not already a git repository
git init
git add .
git commit -m "Prepare for Vercel deployment"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

### Step 2: Import Project to Vercel

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click **"Add New Project"**
3. Click **"Import Git Repository"**
4. Select your GitHub repository
5. Vercel will detect the configuration automatically

### Step 3: Configure Environment Variables

In the Vercel dashboard, add these environment variables:

#### Required Environment Variables:

```
MONGO_URL=mongodb+srv://saikumar22102005:projectstartup@cluster0.spzm4pc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0

DB_NAME=ecommerce_db

JWT_SECRET_KEY=your-secret-key-change-in-production-9x8z7y6w5v4u3t2s1r

CLOUDINARY_CLOUD_NAME=dwvx9kg8e

CLOUDINARY_API_KEY=454177812827398

CLOUDINARY_API_SECRET=nUJL9QABXjQgmbMyKTId_laog74

RAZORPAY_KEY_ID=rzp_test_RU1gB1HeiMJiKu

RAZORPAY_KEY_SECRET=EbZ0rfiiuk2jEHBRaylnYdhO

REACT_APP_BACKEND_URL=https://your-app-name.vercel.app
```

**Important Notes:**
- Replace `your-app-name` with your actual Vercel domain after deployment
- You may need to redeploy after setting `REACT_APP_BACKEND_URL`
- Keep your secrets secure and never commit them to Git

### Step 4: Configure Build Settings

**Framework Preset:** Other

**Build Command:**
```bash
cd frontend && yarn install && yarn build
```

**Output Directory:**
```
frontend/build
```

**Install Command:**
```bash
cd frontend && yarn install
```

### Step 5: Deploy

1. Click **"Deploy"**
2. Wait for the build to complete (usually 2-5 minutes)
3. Once deployed, you'll get a URL like `https://your-app-name.vercel.app`

### Step 6: Update Frontend Environment Variable

1. Copy your deployment URL (e.g., `https://your-app-name.vercel.app`)
2. Go to Vercel Dashboard → Your Project → Settings → Environment Variables
3. Update `REACT_APP_BACKEND_URL` with your deployment URL
4. Go to Deployments tab and click **"Redeploy"** to apply changes

### Step 7: Test Your Deployment

1. Visit your Vercel URL
2. Test the following:
   - ✓ Homepage loads correctly
   - ✓ User registration/login works
   - ✓ Products page displays products from MongoDB
   - ✓ Admin login at `/admin` URL
   - ✓ Admin can create products with file uploads to Cloudinary
   - ✓ Payment flow with Razorpay

## Troubleshooting

### Backend API Issues

**Problem:** API requests return 404 or 500 errors

**Solution:**
- Check Vercel Function Logs in dashboard
- Verify all environment variables are set correctly
- Ensure MongoDB Atlas allows connections from `0.0.0.0/0` (or Vercel's IP ranges)

### Frontend Can't Connect to Backend

**Problem:** Frontend shows network errors

**Solution:**
- Verify `REACT_APP_BACKEND_URL` is set to your Vercel deployment URL
- Check browser console for CORS errors
- Redeploy after updating environment variables

### File Upload Issues

**Problem:** Product images/files fail to upload

**Solution:**
- Verify Cloudinary credentials are correct
- Check Cloudinary dashboard for upload limits
- Review Vercel function logs for detailed errors

### MongoDB Connection Issues

**Problem:** Database operations fail

**Solution:**
- Go to MongoDB Atlas Dashboard
- Navigate to Network Access
- Add `0.0.0.0/0` to allow all connections (or Vercel's specific IPs)
- Verify connection string is correct

## Important Considerations

### Serverless Function Limits

- **Execution Time:** 10 seconds (Hobby), 60 seconds (Pro)
- **Payload Size:** 4.5 MB for request/response
- **File Uploads:** Large files should be uploaded directly to Cloudinary via frontend

### Database Connection Pooling

- Use MongoDB Atlas connection string with `maxPoolSize` parameter
- Example: `...mongodb.net/?retryWrites=true&w=majority&maxPoolSize=10`

### Custom Domain (Optional)

1. Go to Vercel Dashboard → Your Project → Settings → Domains
2. Add your custom domain
3. Update DNS records as instructed
4. Update `REACT_APP_BACKEND_URL` if using custom domain

## Monitoring & Maintenance

### View Logs

1. Vercel Dashboard → Your Project → Functions
2. Click on any function to see execution logs
3. Filter by errors or specific time ranges

### Analytics

- Vercel provides built-in analytics
- Monitor page views, API requests, and performance
- Available in Dashboard → Analytics

### Automatic Deployments

- Every push to `main` branch triggers automatic deployment
- Preview deployments created for pull requests
- Configure in Settings → Git Integration

## Cost Considerations

### Vercel Free Tier Includes:

- Unlimited deployments
- 100 GB bandwidth per month
- Serverless function executions
- Automatic HTTPS

### Paid Services:

- **MongoDB Atlas:** Free tier (512 MB storage)
- **Cloudinary:** Free tier (25 credits/month)
- **Razorpay:** Transaction fees apply

## Security Best Practices

1. **Never commit `.env` files** - Use Vercel environment variables
2. **Use environment variable secrets** - Mark sensitive variables as "Secret"
3. **Enable HTTPS only** - Vercel enforces this by default
4. **Rotate JWT secrets** - Change `JWT_SECRET_KEY` periodically
5. **Monitor API usage** - Watch for unusual activity

## Next Steps

- Set up custom domain
- Configure email notifications for deployments
- Set up monitoring/alerting
- Enable preview deployments for testing
- Consider upgrading to Pro for better limits

## Support Resources

- **Vercel Documentation:** https://vercel.com/docs
- **Vercel Community:** https://github.com/vercel/vercel/discussions
- **FastAPI on Vercel:** https://vercel.com/guides/deploying-fastapi-with-vercel

---

**Your deployment is now complete! 🎉**

Access your live application at: `https://your-app-name.vercel.app`
