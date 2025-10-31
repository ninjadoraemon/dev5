#!/usr/bin/env python3
"""
Backend Testing Script for E-commerce Features
Tests cart duplicate prevention, demo course distribution, video URLs, and user registration
"""

import requests
import json
import os
import uuid
import time

# Get backend URL from frontend .env
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except:
        pass
    return "http://localhost:8001"

BASE_URL = get_backend_url()
API_URL = f"{BASE_URL}/api"

class EcommerceFeatureTester:
    def __init__(self):
        self.admin_token = None
        self.user_token = None
        self.test_user_id = None
        self.demo_course_id = "12e942d3-1091-43f0-b22c-33508096276b"
        self.session = requests.Session()
        
    def create_test_image(self):
        """Create a small test image file"""
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes
    
    def create_test_pdf(self):
        """Create a small test PDF file"""
        pdf_bytes = io.BytesIO()
        c = canvas.Canvas(pdf_bytes, pagesize=letter)
        c.drawString(100, 750, "Test Download File")
        c.drawString(100, 730, "This is a test PDF for product downloads")
        c.save()
        pdf_bytes.seek(0)
        return pdf_bytes
    
    def test_admin_authentication(self):
        """Test admin user creation and authentication"""
        print("🔐 Testing Admin Authentication...")
        
        # First, seed admin user
        try:
            response = self.session.post(f"{API_URL}/admin/seed")
            print(f"   Admin seed response: {response.status_code}")
            if response.status_code == 200:
                print(f"   Admin seed result: {response.json()}")
        except Exception as e:
            print(f"   Admin seed error: {e}")
        
        # Login as admin
        login_data = {
            "email": "admin@digitalstore.com",
            "password": "admin123"
        }
        
        try:
            response = self.session.post(f"{API_URL}/auth/login", json=login_data)
            print(f"   Admin login status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.admin_token = result.get('token')
                user_info = result.get('user', {})
                print(f"   ✅ Admin login successful")
                print(f"   Admin role: {user_info.get('role')}")
                print(f"   Token received: {'Yes' if self.admin_token else 'No'}")
                return True
            else:
                print(f"   ❌ Admin login failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Admin login error: {e}")
            return False

    def test_demo_course_distribution(self):
        """Test POST /api/admin/distribute-demo-course"""
        print("\n📚 Testing Demo Course Distribution...")
        
        if not self.admin_token:
            print("   ❌ No admin token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            response = self.session.post(f"{API_URL}/admin/distribute-demo-course", headers=headers)
            print(f"   Demo course distribution status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                users_updated = result.get('users_updated', 0)
                message = result.get('message', '')
                
                print(f"   ✅ Demo course distribution successful")
                print(f"   Message: {message}")
                print(f"   Users updated: {users_updated}")
                return True
            else:
                print(f"   ❌ Demo course distribution failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Demo course distribution error: {e}")
            return False

    def test_video_url_in_products(self):
        """Test GET /api/products/{demo_course_id} for video_url and video_chapters"""
        print("\n🎥 Testing Video URL in Products...")
        
        try:
            response = self.session.get(f"{API_URL}/products/{self.demo_course_id}")
            print(f"   Product retrieval status: {response.status_code}")
            
            if response.status_code == 200:
                product = response.json()
                video_url = product.get('video_url')
                video_chapters = product.get('video_chapters', [])
                
                print(f"   ✅ Product retrieved successfully")
                print(f"   Product ID: {product.get('id')}")
                print(f"   Product name: {product.get('name')}")
                print(f"   Video URL present: {'Yes' if video_url else 'No'}")
                print(f"   Video URL: {video_url}")
                print(f"   Video chapters count: {len(video_chapters)}")
                
                if video_chapters:
                    print(f"   Video chapters: {video_chapters}")
                
                # Check if both video_url and video_chapters are present
                has_video_features = bool(video_url) and isinstance(video_chapters, list)
                print(f"   Video features complete: {'✅' if has_video_features else '❌'}")
                return has_video_features
            else:
                print(f"   ❌ Product retrieval failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Product retrieval error: {e}")
            return False

    def test_new_user_registration_with_demo_course(self):
        """Test POST /api/auth/register and verify demo course is added"""
        print("\n👤 Testing New User Registration with Demo Course...")
        
        # Generate unique user data
        unique_id = str(uuid.uuid4())[:8]
        user_data = {
            "email": f"testuser_{unique_id}@example.com",
            "password": "testpassword123",
            "name": f"Test User {unique_id}"
        }
        
        try:
            # Register new user
            response = self.session.post(f"{API_URL}/auth/register", json=user_data)
            print(f"   User registration status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.user_token = result.get('token')
                user_info = result.get('user', {})
                self.test_user_id = user_info.get('id')
                
                print(f"   ✅ User registration successful")
                print(f"   User ID: {self.test_user_id}")
                print(f"   User email: {user_info.get('email')}")
                print(f"   Token received: {'Yes' if self.user_token else 'No'}")
                
                # Now test GET /api/auth/me to check purchased_products
                if self.user_token:
                    return self.test_user_demo_course_access()
                else:
                    print("   ❌ No token received for further testing")
                    return False
            else:
                print(f"   ❌ User registration failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ User registration error: {e}")
            return False

    def test_user_demo_course_access(self):
        """Test GET /api/auth/me to verify demo course in purchased_products"""
        print("\n🔍 Testing User Demo Course Access...")
        
        if not self.user_token:
            print("   ❌ No user token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.user_token}"}
        
        try:
            response = self.session.get(f"{API_URL}/auth/me", headers=headers)
            print(f"   User info retrieval status: {response.status_code}")
            
            if response.status_code == 200:
                user_info = response.json()
                purchased_products = user_info.get('purchased_products', [])
                
                print(f"   ✅ User info retrieved successfully")
                print(f"   User ID: {user_info.get('id')}")
                print(f"   Purchased products count: {len(purchased_products)}")
                print(f"   Purchased products: {purchased_products}")
                
                # Check if demo course is in purchased products
                has_demo_course = self.demo_course_id in purchased_products
                print(f"   Demo course in purchased products: {'✅' if has_demo_course else '❌'}")
                
                return has_demo_course
            else:
                print(f"   ❌ User info retrieval failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ User info retrieval error: {e}")
            return False

    def test_cart_duplicate_prevention(self):
        """Test POST /api/cart/add with same product twice"""
        print("\n🛒 Testing Cart Duplicate Prevention...")
        
        if not self.user_token:
            print("   ❌ No user token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.user_token}"}
        
        # First, get a product to add to cart (use demo course)
        cart_item = {
            "product_id": self.demo_course_id,
            "quantity": 1
        }
        
        try:
            # First attempt - should succeed
            print("   Attempting first add to cart...")
            response1 = self.session.post(f"{API_URL}/cart/add", json=cart_item, headers=headers)
            print(f"   First add to cart status: {response1.status_code}")
            
            if response1.status_code == 200:
                result1 = response1.json()
                print(f"   ✅ First add to cart successful: {result1.get('message')}")
                
                # Second attempt - should fail with 400
                print("   Attempting second add to cart (should fail)...")
                response2 = self.session.post(f"{API_URL}/cart/add", json=cart_item, headers=headers)
                print(f"   Second add to cart status: {response2.status_code}")
                
                if response2.status_code == 400:
                    result2 = response2.json()
                    error_message = result2.get('detail', '')
                    print(f"   ✅ Second add to cart correctly failed")
                    print(f"   Error message: {error_message}")
                    
                    # Check if error message is correct
                    correct_message = "Product already in cart" in error_message
                    print(f"   Correct error message: {'✅' if correct_message else '❌'}")
                    
                    return correct_message
                else:
                    print(f"   ❌ Second add to cart should have failed with 400, got {response2.status_code}")
                    print(f"   Response: {response2.text}")
                    return False
            else:
                print(f"   ❌ First add to cart failed: {response1.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Cart duplicate prevention test error: {e}")
            return False
    
    def cleanup_test_data(self):
        """Clean up test data after testing"""
        print("\n🧹 Cleaning up test data...")
        
        if self.user_token:
            headers = {"Authorization": f"Bearer {self.user_token}"}
            try:
                # Clear cart
                response = self.session.delete(f"{API_URL}/cart/clear", headers=headers)
                if response.status_code == 200:
                    print("   ✅ Test cart cleared")
                else:
                    print(f"   ⚠️ Cart clear failed: {response.status_code}")
            except Exception as e:
                print(f"   ⚠️ Cart cleanup error: {e}")
    
    def run_all_tests(self):
        """Run all e-commerce feature tests"""
        print("🚀 Starting E-commerce Features Tests")
        print("=" * 60)
        print(f"Backend URL: {BASE_URL}")
        print(f"API URL: {API_URL}")
        print("=" * 60)
        
        test_results = {}
        
        # Test 1: Admin Authentication
        test_results['admin_auth'] = self.test_admin_authentication()
        
        # Test 2: Demo Course Distribution (admin auth required)
        test_results['demo_course_distribution'] = self.test_demo_course_distribution()
        
        # Test 3: Video URL in Products
        test_results['video_url_in_products'] = self.test_video_url_in_products()
        
        # Test 4: New User Registration with Demo Course
        test_results['user_registration_demo_course'] = self.test_new_user_registration_with_demo_course()
        
        # Test 5: Cart Duplicate Prevention
        test_results['cart_duplicate_prevention'] = self.test_cart_duplicate_prevention()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 E-COMMERCE FEATURES TEST RESULTS")
        print("=" * 60)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_name.replace('_', ' ').title()}: {status}")
            if result:
                passed += 1
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All e-commerce features are working correctly!")
        else:
            print("⚠️  Some features failed. Please check the detailed output above.")
        
        return test_results

if __name__ == "__main__":
    tester = EcommerceFeatureTester()
    results = tester.run_all_tests()