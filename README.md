# Digital Store - E-Commerce Platform

A full-stack e-commerce application for selling digital products (software, courses, etc.) with integrated payment processing, cloud storage, and admin management.

## 🌟 Features

- **User Authentication:** Secure registration and login with JWT tokens
- **Product Catalog:** Browse software and courses by category
- **Shopping Cart:** Add/remove items and manage cart
- **Payment Integration:** Razorpay payment gateway for secure transactions
- **Admin Dashboard:** Manage products, view orders, and track revenue
- **File Uploads:** Cloudinary integration for product images and downloadable files
- **MongoDB Database:** Scalable cloud database with MongoDB Atlas
- **Responsive Design:** Beautiful UI with Tailwind CSS and Framer Motion

## 🚀 Quick Deploy to Vercel

**See detailed guide:** [QUICK_DEPLOY_VERCEL.md](./QUICK_DEPLOY_VERCEL.md)

### Quick Steps:
1. Push code to GitHub
2. Import repository in Vercel
3. Add environment variables
4. Deploy!

## 🛠️ Technology Stack

### Frontend
- React 18
- React Router v7
- Tailwind CSS
- Framer Motion
- Axios
- Radix UI Components

### Backend
- FastAPI (Python)
- Motor (Async MongoDB driver)
- JWT Authentication
- Cloudinary (File storage)
- Razorpay (Payments)

### Database
- MongoDB Atlas

### Deployment
- Vercel (Serverless)

## 📋 Local Development

### Prerequisites
- Node.js 16+
- Python 3.9+
- MongoDB Atlas account
- Cloudinary account
- Razorpay account (test mode)

### Setup

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd app
```

2. **Backend Setup**
```bash
cd backend
pip install -r requirements.txt
# Create .env file with your credentials
python -m uvicorn server:app --reload
```

3. **Frontend Setup**
```bash
cd frontend
yarn install
yarn start
```

4. **Environment Variables**

Backend `.env`:
```
MONGO_URL=<your-mongodb-atlas-url>
DB_NAME=ecommerce_db
JWT_SECRET_KEY=<your-secret-key>
CLOUDINARY_CLOUD_NAME=<your-cloudinary-name>
CLOUDINARY_API_KEY=<your-cloudinary-key>
CLOUDINARY_API_SECRET=<your-cloudinary-secret>
RAZORPAY_KEY_ID=<your-razorpay-key>
RAZORPAY_KEY_SECRET=<your-razorpay-secret>
```

Frontend `.env`:
```
REACT_APP_BACKEND_URL=http://localhost:8001
```

## 📱 Admin Access

- Admin login is available at `/admin` URL (type directly in browser)
- No admin button visible on the main site
- Use admin credentials to access the dashboard

## 📚 Documentation

- [Quick Deploy Guide](./QUICK_DEPLOY_VERCEL.md) - Deploy in 5 minutes
- [Detailed Deployment Guide](./VERCEL_DEPLOYMENT_GUIDE.md) - Complete deployment documentation
- [Admin Guide](./ADMIN_GUIDE.md) - Admin features and management

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📄 License

MIT License
