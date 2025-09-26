#!/usr/bin/env python3
"""
Comprehensive backend API testing for Grocery Price Scraper Phase 4.
Tests new frontend API endpoints: Product Catalog API and JWT Authentication.
"""

import requests
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

# Backend URL configuration
BACKEND_URL = "http://localhost:8001"
API_BASE = f"{BACKEND_URL}/api"

class GroceryScraperPhase4Tester:
    """Test suite for Phase 4 frontend API endpoints."""
    
    def __init__(self):
        self.api_key = None
        self.key_id = None
        self.jwt_token = None
        self.test_user_id = None
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results."""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"    Details: {details}")
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, 
                    headers: Dict = None, use_api_key: bool = False, use_jwt: bool = False) -> requests.Response:
        """Make HTTP request with optional authentication."""
        url = f"{API_BASE}{endpoint}"
        
        # Add authentication headers if required
        if not headers:
            headers = {}
            
        if use_api_key and self.api_key:
            headers["X-API-Key"] = self.api_key
        elif use_jwt and self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            raise
    
    # ========== PHASE 4: PUBLIC ENDPOINTS ==========
    
    def test_api_health_check(self):
        """Test the public /api/test health check endpoint."""
        try:
            response = self.make_request("GET", "/test")
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = ["status", "services", "message"]
                
                if all(field in data for field in expected_fields):
                    self.log_test("API Health Check (/api/test)", True, 
                                f"Status: {data.get('status')}, Message: {data.get('message')}")
                else:
                    self.log_test("API Health Check (/api/test)", False, 
                                f"Missing expected fields in response")
            else:
                self.log_test("API Health Check (/api/test)", False, 
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("API Health Check (/api/test)", False, f"Exception: {str(e)}")
    
    def test_auth_status_endpoint(self):
        """Test the public /api/auth/status endpoint."""
        try:
            response = self.make_request("GET", "/auth/status")
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = ["auth_system", "service_available", "endpoints", "token_type"]
                
                if all(field in data for field in expected_fields):
                    self.log_test("Auth Status (/api/auth/status)", True, 
                                f"Auth system: {data.get('auth_system')}, Available: {data.get('service_available')}")
                else:
                    self.log_test("Auth Status (/api/auth/status)", False, 
                                f"Missing expected fields in response")
            else:
                self.log_test("Auth Status (/api/auth/status)", False, 
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Auth Status (/api/auth/status)", False, f"Exception: {str(e)}")
    
    # ========== PHASE 4: API KEY SETUP ==========
    
    def test_create_api_key(self):
        """Create API key for testing product catalog endpoints."""
        try:
            key_data = {
                "name": f"phase4-test-key-{uuid.uuid4().hex[:8]}",
                "expires_days": 30
            }
            
            response = self.make_request("POST", "/scraper/auth/keys", data=key_data)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["key_id", "name", "api_key", "created_at"]
                
                if all(field in data for field in required_fields):
                    self.api_key = data["api_key"]
                    self.key_id = data["key_id"]
                    self.log_test("Create API Key", True, 
                                f"Created key: {data['name']} (ID: {self.key_id[:8]}...)")
                else:
                    self.log_test("Create API Key", False, 
                                "Missing required fields in response")
            else:
                self.log_test("Create API Key", False, 
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Create API Key", False, f"Exception: {str(e)}")
    
    # ========== PHASE 4: PRODUCT CATALOG API ==========
    
    def test_get_products_catalog(self):
        """Test GET /api/products endpoint with API key authentication."""
        if not self.api_key:
            self.log_test("Get Products Catalog", False, "No API key available")
            return
        
        try:
            response = self.make_request("GET", "/products", use_api_key=True)
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = ["products", "total", "page", "page_size", "total_pages"]
                
                if all(field in data for field in expected_fields):
                    products = data.get("products", [])
                    self.log_test("Get Products Catalog", True, 
                                f"Retrieved {len(products)} products, Total: {data.get('total')}")
                else:
                    self.log_test("Get Products Catalog", False, 
                                "Missing expected fields in response")
            else:
                self.log_test("Get Products Catalog", False, 
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Get Products Catalog", False, f"Exception: {str(e)}")
    
    def test_get_products_with_filters(self):
        """Test GET /api/products with filtering and pagination."""
        if not self.api_key:
            self.log_test("Get Products with Filters", False, "No API key available")
            return
        
        try:
            # Test with category filter
            response = self.make_request("GET", "/products?category=vegetables&page=1&page_size=5", use_api_key=True)
            
            if response.status_code == 200:
                data = response.json()
                products = data.get("products", [])
                self.log_test("Get Products with Filters", True, 
                            f"Filtered products: {len(products)} vegetables")
            else:
                self.log_test("Get Products with Filters", False, 
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Get Products with Filters", False, f"Exception: {str(e)}")
    
    def test_search_products(self):
        """Test GET /api/products/search endpoint."""
        if not self.api_key:
            self.log_test("Search Products", False, "No API key available")
            return
        
        try:
            response = self.make_request("GET", "/products/search?q=tomato&limit=10", use_api_key=True)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Search Products", True, 
                                f"Search results: {len(data)} products for 'tomato'")
                else:
                    self.log_test("Search Products", False, 
                                "Response is not a list")
            else:
                self.log_test("Search Products", False, 
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Search Products", False, f"Exception: {str(e)}")
    
    def test_get_product_details(self):
        """Test GET /api/products/{id} endpoint."""
        if not self.api_key:
            self.log_test("Get Product Details", False, "No API key available")
            return
        
        try:
            # First get a product ID from the catalog
            response = self.make_request("GET", "/products?page_size=1", use_api_key=True)
            
            if response.status_code == 200:
                data = response.json()
                products = data.get("products", [])
                
                if products:
                    product_id = products[0].get("id")
                    if product_id:
                        # Test product details endpoint
                        detail_response = self.make_request("GET", f"/products/{product_id}", use_api_key=True)
                        
                        if detail_response.status_code == 200:
                            detail_data = detail_response.json()
                            expected_fields = ["id", "name", "category", "site"]
                            
                            if all(field in detail_data for field in expected_fields):
                                self.log_test("Get Product Details", True, 
                                            f"Product details: {detail_data.get('name')} from {detail_data.get('site')}")
                            else:
                                self.log_test("Get Product Details", False, 
                                            "Missing expected fields in product details")
                        else:
                            self.log_test("Get Product Details", False, 
                                        f"HTTP {detail_response.status_code}: {detail_response.text}")
                    else:
                        self.log_test("Get Product Details", False, "No product ID found")
                else:
                    self.log_test("Get Product Details", False, "No products available for testing")
            else:
                self.log_test("Get Product Details", False, 
                            f"Failed to get products: HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Get Product Details", False, f"Exception: {str(e)}")
    
    def test_get_current_prices(self):
        """Test GET /api/prices/{id} endpoint."""
        if not self.api_key:
            self.log_test("Get Current Prices", False, "No API key available")
            return
        
        try:
            # First get a product ID
            response = self.make_request("GET", "/products?page_size=1", use_api_key=True)
            
            if response.status_code == 200:
                data = response.json()
                products = data.get("products", [])
                
                if products:
                    product_id = products[0].get("id")
                    if product_id:
                        # Test current prices endpoint
                        prices_response = self.make_request("GET", f"/prices/{product_id}", use_api_key=True)
                        
                        if prices_response.status_code == 200:
                            prices_data = prices_response.json()
                            if isinstance(prices_data, list):
                                self.log_test("Get Current Prices", True, 
                                            f"Current prices: {len(prices_data)} competitor prices")
                            else:
                                self.log_test("Get Current Prices", False, 
                                            "Response is not a list")
                        else:
                            self.log_test("Get Current Prices", False, 
                                        f"HTTP {prices_response.status_code}: {prices_response.text}")
                    else:
                        self.log_test("Get Current Prices", False, "No product ID found")
                else:
                    self.log_test("Get Current Prices", False, "No products available for testing")
            else:
                self.log_test("Get Current Prices", False, 
                            f"Failed to get products: HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Get Current Prices", False, f"Exception: {str(e)}")
    
    def test_get_price_history(self):
        """Test GET /api/prices/history/{id} endpoint."""
        if not self.api_key:
            self.log_test("Get Price History", False, "No API key available")
            return
        
        try:
            # First get a product ID
            response = self.make_request("GET", "/products?page_size=1", use_api_key=True)
            
            if response.status_code == 200:
                data = response.json()
                products = data.get("products", [])
                
                if products:
                    product_id = products[0].get("id")
                    if product_id:
                        # Test price history endpoint
                        history_response = self.make_request("GET", f"/prices/history/{product_id}?days=30", use_api_key=True)
                        
                        if history_response.status_code == 200:
                            history_data = history_response.json()
                            if isinstance(history_data, list):
                                self.log_test("Get Price History", True, 
                                            f"Price history: {len(history_data)} data points")
                            else:
                                self.log_test("Get Price History", False, 
                                            "Response is not a list")
                        else:
                            self.log_test("Get Price History", False, 
                                        f"HTTP {history_response.status_code}: {history_response.text}")
                    else:
                        self.log_test("Get Price History", False, "No product ID found")
                else:
                    self.log_test("Get Price History", False, "No products available for testing")
            else:
                self.log_test("Get Price History", False, 
                            f"Failed to get products: HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Get Price History", False, f"Exception: {str(e)}")
    
    def test_get_categories(self):
        """Test GET /api/categories endpoint."""
        if not self.api_key:
            self.log_test("Get Categories", False, "No API key available")
            return
        
        try:
            response = self.make_request("GET", "/categories", use_api_key=True)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    categories = [cat.get("name") for cat in data if isinstance(cat, dict)]
                    self.log_test("Get Categories", True, 
                                f"Available categories: {len(data)} ({', '.join(categories[:5])})")
                else:
                    self.log_test("Get Categories", False, 
                                "Response is not a list")
            else:
                self.log_test("Get Categories", False, 
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Get Categories", False, f"Exception: {str(e)}")
    
    def test_get_api_stats(self):
        """Test GET /api/stats endpoint."""
        if not self.api_key:
            self.log_test("Get API Stats", False, "No API key available")
            return
        
        try:
            response = self.make_request("GET", "/stats", use_api_key=True)
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = ["database_stats", "api_info"]
                
                if all(field in data for field in expected_fields):
                    db_stats = data.get("database_stats", {})
                    self.log_test("Get API Stats", True, 
                                f"API stats retrieved, DB products: {db_stats.get('total_products', 'N/A')}")
                else:
                    self.log_test("Get API Stats", False, 
                                "Missing expected fields in response")
            else:
                self.log_test("Get API Stats", False, 
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Get API Stats", False, f"Exception: {str(e)}")
    
    # ========== PHASE 4: JWT AUTHENTICATION ==========
    
    def test_user_registration(self):
        """Test POST /api/auth/register endpoint."""
        try:
            user_data = {
                "username": f"testuser_{uuid.uuid4().hex[:8]}",
                "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
                "password": "SecurePassword123!",
                "full_name": "Test User"
            }
            
            response = self.make_request("POST", "/auth/register", data=user_data)
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = ["access_token", "token_type", "expires_in", "user"]
                
                if all(field in data for field in expected_fields):
                    self.jwt_token = data["access_token"]
                    self.test_user_id = data["user"]["id"]
                    self.log_test("User Registration", True, 
                                f"Registered user: {data['user']['username']}, Token expires in: {data['expires_in']}s")
                else:
                    self.log_test("User Registration", False, 
                                "Missing expected fields in response")
            else:
                self.log_test("User Registration", False, 
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("User Registration", False, f"Exception: {str(e)}")
    
    def test_user_login(self):
        """Test POST /api/auth/login endpoint."""
        try:
            # Create a new user for login test
            user_data = {
                "username": f"loginuser_{uuid.uuid4().hex[:8]}",
                "email": f"login_{uuid.uuid4().hex[:8]}@example.com",
                "password": "LoginPassword123!",
                "full_name": "Login Test User"
            }
            
            # Register user first
            register_response = self.make_request("POST", "/auth/register", data=user_data)
            
            if register_response.status_code == 200:
                # Now test login
                login_data = {
                    "username": user_data["username"],
                    "password": user_data["password"]
                }
                
                login_response = self.make_request("POST", "/auth/login", data=login_data)
                
                if login_response.status_code == 200:
                    data = login_response.json()
                    expected_fields = ["access_token", "token_type", "expires_in", "user"]
                    
                    if all(field in data for field in expected_fields):
                        self.log_test("User Login", True, 
                                    f"Login successful for: {data['user']['username']}")
                    else:
                        self.log_test("User Login", False, 
                                    "Missing expected fields in login response")
                else:
                    self.log_test("User Login", False, 
                                f"Login failed: HTTP {login_response.status_code}: {login_response.text}")
            else:
                self.log_test("User Login", False, 
                            f"Failed to create test user for login: HTTP {register_response.status_code}")
        except Exception as e:
            self.log_test("User Login", False, f"Exception: {str(e)}")
    
    def test_get_current_user(self):
        """Test GET /api/auth/me endpoint."""
        if not self.jwt_token:
            self.log_test("Get Current User", False, "No JWT token available")
            return
        
        try:
            response = self.make_request("GET", "/auth/me", use_jwt=True)
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = ["id", "username", "email", "is_active", "created_at"]
                
                if all(field in data for field in expected_fields):
                    self.log_test("Get Current User", True, 
                                f"User info: {data['username']} ({data['email']}), Active: {data['is_active']}")
                else:
                    self.log_test("Get Current User", False, 
                                "Missing expected fields in response")
            else:
                self.log_test("Get Current User", False, 
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Get Current User", False, f"Exception: {str(e)}")
    
    def test_refresh_token(self):
        """Test POST /api/auth/refresh endpoint."""
        if not self.jwt_token:
            self.log_test("Refresh Token", False, "No JWT token available")
            return
        
        try:
            response = self.make_request("POST", "/auth/refresh", use_jwt=True)
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = ["access_token", "token_type", "expires_in", "user"]
                
                if all(field in data for field in expected_fields):
                    new_token = data["access_token"]
                    self.log_test("Refresh Token", True, 
                                f"Token refreshed successfully, expires in: {data['expires_in']}s")
                    # Update token for future tests
                    self.jwt_token = new_token
                else:
                    self.log_test("Refresh Token", False, 
                                "Missing expected fields in response")
            else:
                self.log_test("Refresh Token", False, 
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Refresh Token", False, f"Exception: {str(e)}")
    
    def test_logout_user(self):
        """Test POST /api/auth/logout endpoint."""
        if not self.jwt_token:
            self.log_test("Logout User", False, "No JWT token available")
            return
        
        try:
            response = self.make_request("POST", "/auth/logout", use_jwt=True)
            
            if response.status_code == 200:
                data = response.json()
                
                if "message" in data:
                    self.log_test("Logout User", True, 
                                f"Logout successful: {data['message']}")
                else:
                    self.log_test("Logout User", False, 
                                "No confirmation message in response")
            else:
                self.log_test("Logout User", False, 
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Logout User", False, f"Exception: {str(e)}")
    
    # ========== PHASE 4: AUTHENTICATION VALIDATION ==========
    
    def test_api_key_vs_jwt_auth(self):
        """Test that both API key and JWT authentication work for different endpoints."""
        if not self.api_key or not self.jwt_token:
            self.log_test("Dual Authentication Test", False, "Missing API key or JWT token")
            return
        
        try:
            # Test that product endpoints require API key (not JWT)
            response_no_auth = self.make_request("GET", "/products")
            response_jwt_auth = self.make_request("GET", "/products", use_jwt=True)
            response_api_key = self.make_request("GET", "/products", use_api_key=True)
            
            # Test that auth endpoints work with JWT (not API key)
            auth_response_no_auth = self.make_request("GET", "/auth/me")
            auth_response_api_key = self.make_request("GET", "/auth/me", use_api_key=True)
            auth_response_jwt = self.make_request("GET", "/auth/me", use_jwt=True)
            
            # Analyze results
            product_auth_correct = (
                response_no_auth.status_code in [401, 403] and
                response_jwt_auth.status_code in [401, 403] and
                response_api_key.status_code == 200
            )
            
            auth_auth_correct = (
                auth_response_no_auth.status_code == 401 and
                auth_response_api_key.status_code == 401 and
                auth_response_jwt.status_code == 200
            )
            
            if product_auth_correct and auth_auth_correct:
                self.log_test("Dual Authentication Test", True, 
                            "Product endpoints require API key, Auth endpoints require JWT")
            else:
                self.log_test("Dual Authentication Test", False, 
                            f"Auth validation failed - Product: {product_auth_correct}, Auth: {auth_auth_correct}")
                
        except Exception as e:
            self.log_test("Dual Authentication Test", False, f"Exception: {str(e)}")
    
    def test_invalid_credentials(self):
        """Test rejection of invalid credentials."""
        try:
            # Test invalid API key
            invalid_api_response = self.make_request("GET", "/products", 
                                                   headers={"X-API-Key": "invalid_key_12345"})
            
            # Test invalid JWT token
            invalid_jwt_response = self.make_request("GET", "/auth/me", 
                                                   headers={"Authorization": "Bearer invalid_token_12345"})
            
            # Test invalid login
            invalid_login_response = self.make_request("POST", "/auth/login", 
                                                     data={"username": "nonexistent", "password": "wrong"})
            
            success = (
                invalid_api_response.status_code in [401, 403] and
                invalid_jwt_response.status_code == 401 and
                invalid_login_response.status_code == 401
            )
            
            if success:
                self.log_test("Invalid Credentials Test", True, 
                            "All invalid credentials correctly rejected")
            else:
                self.log_test("Invalid Credentials Test", False, 
                            f"Invalid credential handling failed - API: {invalid_api_response.status_code}, "
                            f"JWT: {invalid_jwt_response.status_code}, Login: {invalid_login_response.status_code}")
                
        except Exception as e:
            self.log_test("Invalid Credentials Test", False, f"Exception: {str(e)}")
    
    # ========== TEST EXECUTION ==========
    
    def run_all_tests(self):
        """Run all Phase 4 API tests in sequence."""
        print("🚀 Starting Grocery Price Scraper Phase 4 API Tests")
        print("Testing: Product Catalog API + JWT Authentication")
        print("=" * 70)
        
        # Phase 1: Public Endpoints
        print("\n📋 Phase 1: Public Endpoints (No Auth Required)")
        self.test_api_health_check()
        self.test_auth_status_endpoint()
        
        # Phase 2: API Key Setup
        print("\n🔑 Phase 2: API Key Setup")
        self.test_create_api_key()
        
        # Phase 3: Product Catalog API (API Key Auth)
        print("\n🛒 Phase 3: Product Catalog API (API Key Required)")
        self.test_get_products_catalog()
        self.test_get_products_with_filters()
        self.test_search_products()
        self.test_get_product_details()
        self.test_get_current_prices()
        self.test_get_price_history()
        self.test_get_categories()
        self.test_get_api_stats()
        
        # Phase 4: JWT Authentication
        print("\n👤 Phase 4: JWT Authentication System")
        self.test_user_registration()
        self.test_user_login()
        self.test_get_current_user()
        self.test_refresh_token()
        self.test_logout_user()
        
        # Phase 5: Authentication Validation
        print("\n🔒 Phase 5: Authentication Validation")
        self.test_api_key_vs_jwt_auth()
        self.test_invalid_credentials()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 70)
        print("📊 PHASE 4 TEST SUMMARY")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['details']}")
        
        print(f"\n🎯 CRITICAL FUNCTIONALITY:")
        critical_tests = [
            "API Health Check (/api/test)", "Auth Status (/api/auth/status)",
            "Create API Key", "Get Products Catalog", "User Registration", 
            "User Login", "Get Current User", "Dual Authentication Test"
        ]
        
        critical_results = [r for r in self.test_results if r["test"] in critical_tests]
        critical_passed = sum(1 for r in critical_results if r["success"])
        
        if critical_passed == len(critical_results):
            print("✅ All critical Phase 4 functionality working")
        else:
            print(f"❌ {len(critical_results) - critical_passed} critical tests failed")
        
        return passed_tests, failed_tests


def main():
    """Main test execution."""
    print("🧪 Grocery Price Scraper Phase 4 API Test Suite")
    print("Testing: Frontend Product Catalog API + JWT Authentication")
    print("Backend URL:", BACKEND_URL)
    
    tester = GroceryScraperPhase4Tester()
    
    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Test suite failed with exception: {e}")
    
    return tester


if __name__ == "__main__":
    main()