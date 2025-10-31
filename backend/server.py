from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from passlib.context import CryptContext
import razorpay
from fastapi import Request
import cloudinary
import cloudinary.uploader
import cloudinary.api

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Cloudinary configuration
cloudinary.config(
    cloud_name='dwvx9kg8e',
    api_key='454177812827398',
    api_secret='nUJL9QABXjQgmbMyKTId_laog74'
)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Razorpay client
razorpay_client = razorpay.Client(auth=(
    os.environ.get('RAZORPAY_KEY_ID', ''),
    os.environ.get('RAZORPAY_KEY_SECRET', '')
))

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# Models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ClerkUserSync(BaseModel):
    clerk_id: str
    email: EmailStr
    name: str
    profile_image_url: Optional[str] = None

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str
    role: str = "user"  # "user" or "admin"
    clerk_id: Optional[str] = None  # Clerk user ID for Clerk authenticated users
    profile_image_url: Optional[str] = None
    purchased_products: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class Product(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    price: float
    category: str  # "software" or "course"
    image_url: str
    download_link: str
    video_url: Optional[str] = None
    video_chapters: Optional[List[dict]] = Field(default_factory=list)
    features: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    category: str
    image_url: str
    download_link: str
    video_url: Optional[str] = None
    video_chapters: Optional[List[dict]] = Field(default_factory=list)
    features: List[str] = Field(default_factory=list)

class CartItem(BaseModel):
    product_id: str
    quantity: int = 1

class Cart(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    items: List[CartItem] = Field(default_factory=list)
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class Order(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    items: List[dict]
    total: float
    razorpay_order_id: str
    razorpay_payment_id: Optional[str] = None
    status: str = "created"  # created, paid, failed
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class RazorpayOrderCreate(BaseModel):
    amount: float

class PaymentVerification(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    order_id: str

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    download_link: Optional[str] = None
    video_url: Optional[str] = None
    video_chapters: Optional[List[dict]] = None
    features: Optional[List[str]] = None

# Helper functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_admin_user(current_user: dict = Depends(get_current_user)):
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# Auth Routes
@api_router.post("/auth/register")
async def register(user_data: UserRegister):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user with demo course
    demo_course_id = "12e942d3-1091-43f0-b22c-33508096276b"
    user = User(
        email=user_data.email,
        name=user_data.name,
        purchased_products=[demo_course_id]
    )
    user_dict = user.model_dump()
    user_dict['password_hash'] = hash_password(user_data.password)
    
    await db.users.insert_one(user_dict)
    
    # Create token
    token = create_access_token({"sub": user.id})
    
    return {
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role
        }
    }

@api_router.post("/auth/login")
async def login(login_data: UserLogin):
    user = await db.users.find_one({"email": login_data.email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not verify_password(login_data.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token({"sub": user['id']})
    
    return {
        "token": token,
        "user": {
            "id": user['id'],
            "email": user['email'],
            "name": user['name'],
            "role": user.get('role', 'user')
        }
    }

@api_router.post("/auth/clerk-sync")
async def clerk_sync(clerk_user: ClerkUserSync):
    """
    Sync Clerk user to MongoDB. Creates new user or updates existing one.
    """
    # Check if user already exists by clerk_id
    existing_user = await db.users.find_one({"clerk_id": clerk_user.clerk_id}, {"_id": 0})
    
    if existing_user:
        # Update existing user
        update_data = {
            "name": clerk_user.name,
            "email": clerk_user.email,
        }
        if clerk_user.profile_image_url:
            update_data["profile_image_url"] = clerk_user.profile_image_url
            
        await db.users.update_one(
            {"clerk_id": clerk_user.clerk_id},
            {"$set": update_data}
        )
        return {
            "status": "updated",
            "user": {
                "id": existing_user['id'],
                "email": clerk_user.email,
                "name": clerk_user.name,
                "clerk_id": clerk_user.clerk_id
            }
        }
    else:
        # Create new user with demo course
        demo_course_id = "12e942d3-1091-43f0-b22c-33508096276b"
        user = User(
            email=clerk_user.email,
            name=clerk_user.name,
            clerk_id=clerk_user.clerk_id,
            profile_image_url=clerk_user.profile_image_url,
            purchased_products=[demo_course_id]
        )
        user_dict = user.model_dump()
        
        await db.users.insert_one(user_dict)
        
        return {
            "status": "created",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "clerk_id": user.clerk_id,
                "purchased_products": user.purchased_products
            }
        }

@api_router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user['id'],
        "email": current_user['email'],
        "name": current_user['name'],
        "role": current_user.get('role', 'user'),
        "purchased_products": current_user.get('purchased_products', [])
    }

# Product Routes
@api_router.get("/products", response_model=List[Product])
async def get_products(category: Optional[str] = None):
    query = {}
    if category:
        query['category'] = category
    products = await db.products.find(query, {"_id": 0}).to_list(1000)
    return products

@api_router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@api_router.post("/products", response_model=Product)
async def create_product(product_data: ProductCreate, current_user: dict = Depends(get_current_user)):
    product = Product(**product_data.model_dump())
    await db.products.insert_one(product.model_dump())
    return product

# Cart Routes
@api_router.get("/cart")
async def get_cart(current_user: dict = Depends(get_current_user)):
    cart = await db.carts.find_one({"user_id": current_user['id']}, {"_id": 0})
    if not cart:
        return {"items": []}
    
    # Get product details for cart items
    items_with_details = []
    for item in cart.get('items', []):
        product = await db.products.find_one({"id": item['product_id']}, {"_id": 0})
        if product:
            items_with_details.append({
                "product": product,
                "quantity": item['quantity']
            })
    
    return {"items": items_with_details}

@api_router.post("/cart/add")
async def add_to_cart(item: CartItem, current_user: dict = Depends(get_current_user)):
    # Check if product exists
    product = await db.products.find_one({"id": item.product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    cart = await db.carts.find_one({"user_id": current_user['id']})
    
    if not cart:
        # Create new cart
        new_cart = Cart(user_id=current_user['id'], items=[item.model_dump()])
        await db.carts.insert_one(new_cart.model_dump())
    else:
        # Update existing cart
        items = cart.get('items', [])
        existing_item = next((i for i in items if i['product_id'] == item.product_id), None)
        
        if existing_item:
            # Product already in cart - don't add again
            raise HTTPException(status_code=400, detail="Product already in cart")
        else:
            items.append(item.model_dump())
        
        await db.carts.update_one(
            {"user_id": current_user['id']},
            {"$set": {"items": items, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    return {"message": "Item added to cart"}

@api_router.delete("/cart/remove/{product_id}")
async def remove_from_cart(product_id: str, current_user: dict = Depends(get_current_user)):
    cart = await db.carts.find_one({"user_id": current_user['id']})
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    items = [item for item in cart.get('items', []) if item['product_id'] != product_id]
    
    await db.carts.update_one(
        {"user_id": current_user['id']},
        {"$set": {"items": items, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Item removed from cart"}

@api_router.delete("/cart/clear")
async def clear_cart(current_user: dict = Depends(get_current_user)):
    await db.carts.update_one(
        {"user_id": current_user['id']},
        {"$set": {"items": [], "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Cart cleared"}

# Payment & Order Routes
@api_router.post("/orders/create")
async def create_order(current_user: dict = Depends(get_current_user)):
    # Get cart
    cart = await db.carts.find_one({"user_id": current_user['id']})
    if not cart or not cart.get('items'):
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    # Calculate total and get product details
    items = []
    total = 0
    for item in cart['items']:
        product = await db.products.find_one({"id": item['product_id']}, {"_id": 0})
        if product:
            items.append({
                "product_id": product['id'],
                "name": product['name'],
                "price": product['price'],
                "quantity": item['quantity']
            })
            total += product['price'] * item['quantity']
    
    # Create Razorpay order
    razorpay_order = razorpay_client.order.create({
        "amount": int(total * 100),  # Convert to paise
        "currency": "INR",
        "payment_capture": 1
    })
    
    # Create order in database
    order = Order(
        user_id=current_user['id'],
        items=items,
        total=total,
        razorpay_order_id=razorpay_order['id']
    )
    
    await db.orders.insert_one(order.model_dump())
    
    return {
        "order_id": order.id,
        "razorpay_order_id": razorpay_order['id'],
        "amount": total,
        "currency": "INR",
        "key_id": os.environ.get('RAZORPAY_KEY_ID', '')
    }

@api_router.post("/orders/verify")
async def verify_payment(verification: PaymentVerification, current_user: dict = Depends(get_current_user)):
    try:
        # Verify signature
        razorpay_client.utility.verify_payment_signature({
            'razorpay_order_id': verification.razorpay_order_id,
            'razorpay_payment_id': verification.razorpay_payment_id,
            'razorpay_signature': verification.razorpay_signature
        })
        
        # Update order
        order = await db.orders.find_one({"id": verification.order_id}, {"_id": 0})
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        await db.orders.update_one(
            {"id": verification.order_id},
            {"$set": {
                "status": "paid",
                "razorpay_payment_id": verification.razorpay_payment_id
            }}
        )
        
        # Add products to user's purchased list
        product_ids = [item['product_id'] for item in order['items']]
        await db.users.update_one(
            {"id": current_user['id']},
            {"$addToSet": {"purchased_products": {"$each": product_ids}}}
        )
        
        # Clear cart
        await db.carts.update_one(
            {"user_id": current_user['id']},
            {"$set": {"items": []}}
        )
        
        return {"message": "Payment verified successfully", "status": "paid"}
    except Exception as e:
        await db.orders.update_one(
            {"id": verification.order_id},
            {"$set": {"status": "failed"}}
        )
        raise HTTPException(status_code=400, detail=f"Payment verification failed: {str(e)}")

@api_router.get("/orders")
async def get_orders(current_user: dict = Depends(get_current_user)):
    orders = await db.orders.find({"user_id": current_user['id']}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return orders

@api_router.get("/orders/{order_id}")
async def get_order(order_id: str, current_user: dict = Depends(get_current_user)):
    order = await db.orders.find_one({"id": order_id, "user_id": current_user['id']}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

# Purchased Products
@api_router.get("/purchased-products")
async def get_purchased_products(current_user: dict = Depends(get_current_user)):
    purchased_ids = current_user.get('purchased_products', [])
    if not purchased_ids:
        return []
    
    products = await db.products.find({"id": {"$in": purchased_ids}}, {"_id": 0}).to_list(1000)
    return products

@api_router.get("/clerk/purchased-products/{clerk_id}")
async def get_clerk_purchased_products(clerk_id: str):
    """
    Get purchased products for a Clerk user by their clerk_id
    """
    user = await db.users.find_one({"clerk_id": clerk_id}, {"_id": 0})
    if not user:
        return []
    
    purchased_ids = user.get('purchased_products', [])
    if not purchased_ids:
        return []
    
    products = await db.products.find({"id": {"$in": purchased_ids}}, {"_id": 0}).to_list(1000)
    return products

# Admin Routes
@api_router.post("/admin/upload")
async def upload_file(
    file: UploadFile = File(...),
    admin_user: dict = Depends(get_admin_user)
):
    try:
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            file.file,
            folder="ecommerce",
            resource_type="auto"
        )
        return {
            "url": result['secure_url'],
            "public_id": result['public_id']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@api_router.post("/admin/products")
async def admin_create_product(
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    category: str = Form(...),
    features: str = Form(""),
    video_url: str = Form(""),
    video_chapters: str = Form(""),
    image: UploadFile = File(None),
    download_file: UploadFile = File(None),
    admin_user: dict = Depends(get_admin_user)
):
    try:
        image_url = ""
        download_link = ""
        
        # Upload image if provided
        if image:
            img_result = cloudinary.uploader.upload(
                image.file,
                folder="ecommerce/products",
                resource_type="image"
            )
            image_url = img_result['secure_url']
        
        # Upload download file if provided
        if download_file:
            file_result = cloudinary.uploader.upload(
                download_file.file,
                folder="ecommerce/downloads",
                resource_type="auto"
            )
            download_link = file_result['secure_url']
        
        # Parse features
        features_list = [f.strip() for f in features.split(',') if f.strip()] if features else []
        
        # Parse video chapters (JSON string)
        import json
        video_chapters_list = []
        if video_chapters:
            try:
                video_chapters_list = json.loads(video_chapters)
            except:
                pass
        
        # Create product
        product = Product(
            name=name,
            description=description,
            price=price,
            category=category,
            image_url=image_url,
            download_link=download_link,
            video_url=video_url if video_url else None,
            video_chapters=video_chapters_list,
            features=features_list
        )
        
        await db.products.insert_one(product.model_dump())
        return product
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create product: {str(e)}")

@api_router.put("/admin/products/{product_id}")
async def admin_update_product(
    product_id: str,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    category: Optional[str] = Form(None),
    features: Optional[str] = Form(None),
    video_url: Optional[str] = Form(None),
    video_chapters: Optional[str] = Form(None),
    image: UploadFile = File(None),
    download_file: UploadFile = File(None),
    admin_user: dict = Depends(get_admin_user)
):
    try:
        product = await db.products.find_one({"id": product_id}, {"_id": 0})
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        update_data = {}
        
        if name:
            update_data['name'] = name
        if description:
            update_data['description'] = description
        if price is not None:
            update_data['price'] = price
        if category:
            update_data['category'] = category
        if features:
            update_data['features'] = [f.strip() for f in features.split(',') if f.strip()]
        if video_url is not None:
            update_data['video_url'] = video_url if video_url else None
        if video_chapters:
            import json
            try:
                update_data['video_chapters'] = json.loads(video_chapters)
            except:
                pass
        
        # Upload new image if provided
        if image:
            img_result = cloudinary.uploader.upload(
                image.file,
                folder="ecommerce/products",
                resource_type="image"
            )
            update_data['image_url'] = img_result['secure_url']
        
        # Upload new download file if provided
        if download_file:
            file_result = cloudinary.uploader.upload(
                download_file.file,
                folder="ecommerce/downloads",
                resource_type="auto"
            )
            update_data['download_link'] = file_result['secure_url']
        
        if update_data:
            await db.products.update_one(
                {"id": product_id},
                {"$set": update_data}
            )
        
        updated_product = await db.products.find_one({"id": product_id}, {"_id": 0})
        return updated_product
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update product: {str(e)}")

@api_router.delete("/admin/products/{product_id}")
async def admin_delete_product(
    product_id: str,
    admin_user: dict = Depends(get_admin_user)
):
    product = await db.products.find_one({"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    await db.products.delete_one({"id": product_id})
    return {"message": "Product deleted successfully"}

@api_router.get("/admin/stats")
async def get_admin_stats(admin_user: dict = Depends(get_admin_user)):
    total_users = await db.users.count_documents({"role": "user"})
    total_products = await db.products.count_documents({})
    total_orders = await db.orders.count_documents({})
    paid_orders = await db.orders.count_documents({"status": "paid"})
    
    # Calculate total revenue
    orders = await db.orders.find({"status": "paid"}, {"_id": 0}).to_list(1000)
    total_revenue = sum(order.get('total', 0) for order in orders)
    
    return {
        "total_users": total_users,
        "total_products": total_products,
        "total_orders": total_orders,
        "paid_orders": paid_orders,
        "total_revenue": total_revenue
    }

@api_router.post("/admin/distribute-demo-course")
async def distribute_demo_course(admin_user: dict = Depends(get_admin_user)):
    """Add demo course to all existing users"""
    demo_course_id = "12e942d3-1091-43f0-b22c-33508096276b"
    
    # Check if demo course exists
    demo_course = await db.products.find_one({"id": demo_course_id})
    if not demo_course:
        raise HTTPException(status_code=404, detail="Demo course not found")
    
    # Add to all users who don't already have it
    result = await db.users.update_many(
        {"purchased_products": {"$ne": demo_course_id}},
        {"$addToSet": {"purchased_products": demo_course_id}}
    )
    
    return {
        "message": "Demo course distributed",
        "users_updated": result.modified_count
    }

@api_router.post("/admin/seed")
async def seed_admin():
    """One-time endpoint to create admin user"""
    existing_admin = await db.users.find_one({"email": "admin@digitalstore.com"})
    if existing_admin:
        return {"message": "Admin already exists"}
    
    admin_user = User(
        email="admin@digitalstore.com",
        name="Admin",
        role="admin"
    )
    admin_dict = admin_user.model_dump()
    admin_dict['password_hash'] = hash_password("admin123")
    
    await db.users.insert_one(admin_dict)
    return {"message": "Admin user created", "email": "admin@digitalstore.com", "password": "admin123"}

# ✅ Include all routers
app.include_router(api_router)

# ✅ Safe, flexible CORS handling
origins_env = os.environ.get("CORS_ORIGINS", "*")

if origins_env == "*":
    allow_origins = ["*"]
else:
    allow_origins = [origin.strip() for origin in origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Simple logging (Vercel captures stdout automatically)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("server")

logger.info("🚀 FastAPI server initialized successfully")

# ✅ Graceful shutdown for MongoDB or other clients
@app.on_event("shutdown")
async def shutdown_db_client():
    try:
        client.close()
        logger.info("✅ MongoDB connection closed successfully.")
    except Exception as e:
        logger.error(f"❌ Error closing MongoDB client: {e}")
