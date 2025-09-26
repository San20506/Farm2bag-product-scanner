#!/usr/bin/env python3
"""
Comprehensive backend API testing for Grocery Price Scraper Phase 3.
Tests all REST API endpoints including authentication, scraping, scheduling, and monitoring.
"""

import requests
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

# Backend URL configuration
BACKEND_URL = "http://localhost:8001"
API_BASE = f"{BACKEND_URL}/api/scraper"

class GroceryScraperAPITester:
    """Test suite for Grocery Price Scraper API endpoints."""
    
    def __init__(self):
        self.api_key = None
        self.key_id = None
        self.test_results = []
        self.created_schedules = []
        self.created_tasks = []
        
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
                    headers: Dict = None, use_auth: bool = True) -> requests.Response:
        """Make HTTP request with optional authentication."""
        url = f"{API_BASE}{endpoint}"
        
        # Add authentication headers if required
        if use_auth and self.api_key:
            if not headers:
                headers = {}
            headers["Authorization"] = f"Bearer {self.api_key}"
        
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
    
    def test_api_info_endpoint(self):
        """Test the public API info endpoint (no auth required)."""
        try:
            response = self.make_request("GET", "/info", use_auth=False)
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = ["name", "version", "description", "endpoints", "authentication"]
                
                if all(field in data for field in expected_fields):
                    self.log_test("API Info Endpoint", True, 
                                f"API: {data.get('name')} v{data.get('version')}")
                else:
                    self.log_test("API Info Endpoint", False, 
                                f"Missing expected fields in response")
            else:
                self.log_test("API Info Endpoint", False, 
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("API Info Endpoint", False, f"Exception: {str(e)}")
    
    def test_api_key_creation(self):
        """Test API key creation."""
        try:
            key_data = {
                "name": f"test-key-{uuid.uuid4().hex[:8]}",
                "expires_days": 30
            }
            
            response = self.make_request("POST", "/auth/keys", data=key_data, use_auth=False)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["key_id", "name", "api_key", "created_at"]
                
                if all(field in data for field in required_fields):
                    self.api_key = data["api_key"]
                    self.key_id = data["key_id"]
                    self.log_test("API Key Creation", True, 
                                f"Created key: {data['name']} (ID: {self.key_id[:8]}...)")
                else:
                    self.log_test("API Key Creation", False, 
                                "Missing required fields in response")
            else:
                self.log_test("API Key Creation", False, 
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("API Key Creation", False, f"Exception: {str(e)}")
    
    def test_api_key_validation(self):
        """Test API key validation by accessing protected endpoint."""
        if not self.api_key:
            self.log_test("API Key Validation", False, "No API key available")
            return
        
        try:
            # Test with valid key
            response = self.make_request("GET", "/status")
            
            if response.status_code == 200:
                self.log_test("API Key Validation (Valid)", True, 
                            "Successfully accessed protected endpoint")
            else:
                self.log_test("API Key Validation (Valid)", False, 
                            f"HTTP {response.status_code}: {response.text}")
            
            # Test with invalid key
            invalid_headers = {"Authorization": "Bearer invalid_key_12345"}
            response = self.make_request("GET", "/status", headers=invalid_headers, use_auth=False)
            
            if response.status_code == 403:
                self.log_test("API Key Validation (Invalid)", True, 
                            "Correctly rejected invalid API key")
            else:
                self.log_test("API Key Validation (Invalid)", False, 
                            f"Expected 403, got {response.status_code}")
                
        except Exception as e:
            self.log_test("API Key Validation", False, f"Exception: {str(e)}")
    
    def test_unauthorized_access(self):
        """Test that protected endpoints reject requests without API keys."""
        try:
            response = self.make_request("GET", "/status", use_auth=False)
            
            if response.status_code == 401:
                self.log_test("Unauthorized Access Protection", True, 
                            "Correctly rejected request without API key")
            else:
                self.log_test("Unauthorized Access Protection", False, 
                            f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_test("Unauthorized Access Protection", False, f"Exception: {str(e)}")
    
    def test_scraper_status_endpoint(self):
        """Test the scraper status endpoint."""
        if not self.api_key:
            self.log_test("Scraper Status", False, "No API key available")
            return
        
        try:
            response = self.make_request("GET", "/status")
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = ["service_available", "active_tasks", "database_stats", "system_info"]
                
                if all(field in data for field in expected_fields):
                    self.log_test("Scraper Status", True, 
                                f"Service available: {data.get('service_available')}, "
                                f"Active tasks: {data.get('active_tasks')}")
                else:
                    self.log_test("Scraper Status", False, 
                                "Missing expected fields in response")
            else:
                self.log_test("Scraper Status", False, 
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Scraper Status", False, f"Exception: {str(e)}")
    
    def test_database_stats_endpoint(self):
        """Test the database statistics endpoint."""
        if not self.api_key:
            self.log_test("Database Stats", False, "No API key available")
            return
        
        try:
            response = self.make_request("GET", "/stats")
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = ["total_products", "products_by_site", "total_comparisons"]
                
                if all(field in data for field in expected_fields):
                    self.log_test("Database Stats", True, 
                                f"Total products: {data.get('total_products')}, "
                                f"Total comparisons: {data.get('total_comparisons')}")
                else:
                    self.log_test("Database Stats", False, 
                                "Missing expected fields in response")
            else:
                self.log_test("Database Stats", False, 
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Database Stats", False, f"Exception: {str(e)}")
    
    def test_start_scraping(self):
        """Test starting a scraping operation."""
        if not self.api_key:
            self.log_test("Start Scraping", False, "No API key available")
            return
        
        try:
            scrape_data = {
                "categories": ["vegetables", "fruits"],
                "sites": ["bigbasket", "jiomart"],
                "generate_report": True,
                "store_data": True
            }
            
            response = self.make_request("POST", "/scrape", data=scrape_data)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["task_id", "status", "message", "started_at"]
                
                if all(field in data for field in required_fields):
                    task_id = data["task_id"]
                    self.created_tasks.append(task_id)
                    self.log_test("Start Scraping", True, 
                                f"Started task: {task_id}, Status: {data['status']}")
                    return task_id
                else:
                    self.log_test("Start Scraping", False, 
                                "Missing required fields in response")
            else:
                self.log_test("Start Scraping", False, 
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Start Scraping", False, f"Exception: {str(e)}")
        
        return None
    
    def test_task_status(self, task_id: str):
        """Test getting task status."""
        if not self.api_key or not task_id:
            self.log_test("Task Status", False, "No API key or task ID available")
            return
        
        try:
            response = self.make_request("GET", f"/tasks/{task_id}")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["task_id", "status", "started_at"]
                
                if all(field in data for field in required_fields):
                    self.log_test("Task Status", True, 
                                f"Task {task_id[:8]}... Status: {data['status']}")
                else:
                    self.log_test("Task Status", False, 
                                "Missing required fields in response")
            elif response.status_code == 404:
                self.log_test("Task Status", False, "Task not found")
            else:
                self.log_test("Task Status", False, 
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Task Status", False, f"Exception: {str(e)}")
    
    def test_recent_tasks(self):
        """Test getting recent tasks."""
        if not self.api_key:
            self.log_test("Recent Tasks", False, "No API key available")
            return
        
        try:
            response = self.make_request("GET", "/tasks?limit=5")
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    self.log_test("Recent Tasks", True, 
                                f"Retrieved {len(data)} recent tasks")
                else:
                    self.log_test("Recent Tasks", False, 
                                "Response is not a list")
            else:
                self.log_test("Recent Tasks", False, 
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Recent Tasks", False, f"Exception: {str(e)}")
    
    def test_create_schedule(self):
        """Test creating a new schedule."""
        if not self.api_key:
            self.log_test("Create Schedule", False, "No API key available")
            return None
        
        try:
            schedule_data = {
                "name": f"test-schedule-{uuid.uuid4().hex[:8]}",
                "interval": "daily",
                "hour": 8,
                "minute": 30,
                "categories": ["vegetables"],
                "sites": ["bigbasket"],
                "enabled": True
            }
            
            response = self.make_request("POST", "/schedules", data=schedule_data)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "name", "interval", "enabled", "created_at"]
                
                if all(field in data for field in required_fields):
                    schedule_id = data["id"]
                    self.created_schedules.append(schedule_id)
                    self.log_test("Create Schedule", True, 
                                f"Created schedule: {data['name']} (ID: {schedule_id[:8]}...)")
                    return schedule_id
                else:
                    self.log_test("Create Schedule", False, 
                                "Missing required fields in response")
            else:
                self.log_test("Create Schedule", False, 
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Create Schedule", False, f"Exception: {str(e)}")
        
        return None
    
    def test_list_schedules(self):
        """Test listing all schedules."""
        if not self.api_key:
            self.log_test("List Schedules", False, "No API key available")
            return
        
        try:
            response = self.make_request("GET", "/schedules")
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    # Check if default schedule exists
                    default_schedule = next((s for s in data if s.get("name") == "default_daily_scrape"), None)
                    if default_schedule:
                        self.log_test("List Schedules", True, 
                                    f"Found {len(data)} schedules including default daily schedule")
                    else:
                        self.log_test("List Schedules", True, 
                                    f"Found {len(data)} schedules (no default schedule)")
                else:
                    self.log_test("List Schedules", False, 
                                "Response is not a list")
            else:
                self.log_test("List Schedules", False, 
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("List Schedules", False, f"Exception: {str(e)}")
    
    def test_get_schedule(self, schedule_id: str):
        """Test getting a specific schedule."""
        if not self.api_key or not schedule_id:
            self.log_test("Get Schedule", False, "No API key or schedule ID available")
            return
        
        try:
            response = self.make_request("GET", f"/schedules/{schedule_id}")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "name", "interval", "enabled"]
                
                if all(field in data for field in required_fields):
                    self.log_test("Get Schedule", True, 
                                f"Retrieved schedule: {data['name']}")
                else:
                    self.log_test("Get Schedule", False, 
                                "Missing required fields in response")
            elif response.status_code == 404:
                self.log_test("Get Schedule", False, "Schedule not found")
            else:
                self.log_test("Get Schedule", False, 
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Get Schedule", False, f"Exception: {str(e)}")
    
    def test_update_schedule(self, schedule_id: str):
        """Test updating a schedule."""
        if not self.api_key or not schedule_id:
            self.log_test("Update Schedule", False, "No API key or schedule ID available")
            return
        
        try:
            update_data = {
                "name": f"updated-schedule-{uuid.uuid4().hex[:8]}",
                "interval": "weekly",
                "hour": 10,
                "minute": 0,
                "day_of_week": 2,  # Tuesday
                "categories": ["fruits", "dairy"],
                "sites": ["jiomart"],
                "enabled": True
            }
            
            response = self.make_request("PUT", f"/schedules/{schedule_id}", data=update_data)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("name") == update_data["name"] and data.get("interval") == "weekly":
                    self.log_test("Update Schedule", True, 
                                f"Updated schedule to: {data['name']}")
                else:
                    self.log_test("Update Schedule", False, 
                                "Schedule not updated correctly")
            elif response.status_code == 404:
                self.log_test("Update Schedule", False, "Schedule not found")
            else:
                self.log_test("Update Schedule", False, 
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Update Schedule", False, f"Exception: {str(e)}")
    
    def test_delete_schedule(self, schedule_id: str):
        """Test deleting a schedule."""
        if not self.api_key or not schedule_id:
            self.log_test("Delete Schedule", False, "No API key or schedule ID available")
            return
        
        try:
            response = self.make_request("DELETE", f"/schedules/{schedule_id}")
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    self.log_test("Delete Schedule", True, 
                                f"Deleted schedule: {schedule_id[:8]}...")
                else:
                    self.log_test("Delete Schedule", False, 
                                "No confirmation message in response")
            elif response.status_code == 404:
                self.log_test("Delete Schedule", False, "Schedule not found")
            else:
                self.log_test("Delete Schedule", False, 
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Delete Schedule", False, f"Exception: {str(e)}")
    
    def test_cleanup_maintenance(self):
        """Test the data cleanup maintenance endpoint."""
        if not self.api_key:
            self.log_test("Data Cleanup", False, "No API key available")
            return
        
        try:
            response = self.make_request("POST", "/maintenance/cleanup?days_to_keep=30")
            
            if response.status_code == 200:
                data = response.json()
                
                if "success" in data:
                    self.log_test("Data Cleanup", True, 
                                f"Cleanup result: {data.get('message', 'Success')}")
                else:
                    self.log_test("Data Cleanup", False, 
                                "No success indicator in response")
            else:
                self.log_test("Data Cleanup", False, 
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Data Cleanup", False, f"Exception: {str(e)}")
    
    def test_api_key_management(self):
        """Test API key listing and revocation."""
        if not self.api_key:
            self.log_test("API Key Management", False, "No API key available")
            return
        
        try:
            # Test listing API keys
            response = self.make_request("GET", "/auth/keys")
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list) and len(data) > 0:
                    self.log_test("List API Keys", True, 
                                f"Found {len(data)} API keys")
                else:
                    self.log_test("List API Keys", False, 
                                "No API keys found or invalid response")
            else:
                self.log_test("List API Keys", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("API Key Management", False, f"Exception: {str(e)}")
    
    def test_edge_cases(self):
        """Test various edge cases and error conditions."""
        if not self.api_key:
            self.log_test("Edge Cases", False, "No API key available")
            return
        
        # Test non-existent task ID
        try:
            fake_task_id = str(uuid.uuid4())
            response = self.make_request("GET", f"/tasks/{fake_task_id}")
            
            if response.status_code == 404:
                self.log_test("Non-existent Task ID", True, 
                            "Correctly returned 404 for non-existent task")
            else:
                self.log_test("Non-existent Task ID", False, 
                            f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_test("Non-existent Task ID", False, f"Exception: {str(e)}")
        
        # Test non-existent schedule ID
        try:
            fake_schedule_id = str(uuid.uuid4())
            response = self.make_request("GET", f"/schedules/{fake_schedule_id}")
            
            if response.status_code == 404:
                self.log_test("Non-existent Schedule ID", True, 
                            "Correctly returned 404 for non-existent schedule")
            else:
                self.log_test("Non-existent Schedule ID", False, 
                            f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_test("Non-existent Schedule ID", False, f"Exception: {str(e)}")
        
        # Test malformed request data
        try:
            malformed_data = {"invalid": "data", "missing": "required_fields"}
            response = self.make_request("POST", "/schedules", data=malformed_data)
            
            if response.status_code in [400, 422]:  # Bad Request or Unprocessable Entity
                self.log_test("Malformed Request", True, 
                            f"Correctly rejected malformed request with {response.status_code}")
            else:
                self.log_test("Malformed Request", False, 
                            f"Expected 400/422, got {response.status_code}")
        except Exception as e:
            self.log_test("Malformed Request", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all API tests in sequence."""
        print("🚀 Starting Grocery Price Scraper API Tests")
        print("=" * 60)
        
        # Phase 1: Basic API and Authentication Tests
        print("\n📋 Phase 1: Basic API & Authentication")
        self.test_api_info_endpoint()
        self.test_unauthorized_access()
        self.test_api_key_creation()
        self.test_api_key_validation()
        self.test_api_key_management()
        
        # Phase 2: Core Scraper API Tests
        print("\n🔍 Phase 2: Core Scraper API")
        self.test_scraper_status_endpoint()
        self.test_database_stats_endpoint()
        
        task_id = self.test_start_scraping()
        if task_id:
            # Wait a moment for task to start
            time.sleep(2)
            self.test_task_status(task_id)
        
        self.test_recent_tasks()
        
        # Phase 3: Scheduling API Tests
        print("\n📅 Phase 3: Scheduling API")
        self.test_list_schedules()  # Check for default schedule
        
        schedule_id = self.test_create_schedule()
        if schedule_id:
            self.test_get_schedule(schedule_id)
            self.test_update_schedule(schedule_id)
            self.test_delete_schedule(schedule_id)
        
        # Phase 4: Maintenance and Edge Cases
        print("\n🔧 Phase 4: Maintenance & Edge Cases")
        self.test_cleanup_maintenance()
        self.test_edge_cases()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
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
            "API Key Creation", "API Key Validation", "Start Scraping", 
            "List Schedules", "Create Schedule"
        ]
        
        critical_results = [r for r in self.test_results if r["test"] in critical_tests]
        critical_passed = sum(1 for r in critical_results if r["success"])
        
        if critical_passed == len(critical_results):
            print("✅ All critical functionality working")
        else:
            print(f"❌ {len(critical_results) - critical_passed} critical tests failed")
        
        return passed_tests, failed_tests


def main():
    """Main test execution."""
    print("🧪 Grocery Price Scraper API Test Suite")
    print("Testing Phase 3: REST API Layer & Automated Scheduling")
    print("Backend URL:", BACKEND_URL)
    
    tester = GroceryScraperAPITester()
    
    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Test suite failed with exception: {e}")
    
    return tester


if __name__ == "__main__":
    main()