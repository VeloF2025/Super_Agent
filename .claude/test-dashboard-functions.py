#!/usr/bin/env python3
"""
Test all dashboard UI functions and API endpoints
Comprehensive testing of cards, stats, reporting, and functionality
"""

import requests
import json
from datetime import datetime

class DashboardTester:
    def __init__(self, base_url="http://localhost:3001"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.test_results = []
        
    def test_endpoint(self, endpoint, method="GET", data=None, expected_keys=None):
        """Test a single API endpoint"""
        url = f"{self.api_url}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url)
            elif method == "POST":
                response = requests.post(url, json=data)
            elif method == "PUT":
                response = requests.put(url, json=data)
            
            success = response.status_code == 200
            result = {
                "endpoint": endpoint,
                "method": method,
                "status_code": response.status_code,
                "success": success,
                "response_size": len(response.text) if response.text else 0
            }
            
            if success and response.text:
                try:
                    json_data = response.json()
                    result["has_data"] = len(json_data) > 0 if isinstance(json_data, (list, dict)) else True
                    
                    # Check for expected keys
                    if expected_keys and isinstance(json_data, dict):
                        result["has_expected_keys"] = all(key in json_data for key in expected_keys)
                    
                    # Check specific data types
                    if endpoint == "/dashboard":
                        result["dashboard_sections"] = list(json_data.keys()) if isinstance(json_data, dict) else []
                    elif endpoint == "/agents":
                        result["agent_count"] = len(json_data) if isinstance(json_data, list) else 0
                    elif endpoint == "/metrics/current":
                        result["metric_types"] = list(json_data.keys()) if isinstance(json_data, dict) else []
                        
                except json.JSONDecodeError:
                    result["json_error"] = True
            
            self.test_results.append(result)
            return result
            
        except requests.exceptions.RequestException as e:
            result = {
                "endpoint": endpoint,
                "method": method,
                "success": False,
                "error": str(e)
            }
            self.test_results.append(result)
            return result
    
    def test_all_endpoints(self):
        """Test all dashboard endpoints"""
        print("=" * 60)
        print("DASHBOARD API ENDPOINT TESTING")
        print("=" * 60)
        
        # Core endpoints
        endpoints = [
            ("/health", "GET", None, ["status", "timestamp"]),
            ("/dashboard", "GET", None, ["agents", "activities", "metrics"]),
            ("/agents", "GET", None, None),
            ("/activities", "GET", None, None),
            ("/communications", "GET", None, None),
            ("/projects", "GET", None, None),
            ("/metrics", "GET", None, None),
            ("/metrics/current", "GET", None, None),
            ("/metrics/distribution", "GET", None, None),
        ]
        
        for endpoint, method, data, expected_keys in endpoints:
            result = self.test_endpoint(endpoint, method, data, expected_keys)
            
            status = "✓ PASS" if result["success"] else "✗ FAIL"
            print(f"{status} {method} {endpoint}")
            
            if result["success"]:
                print(f"     Status: {result['status_code']}")
                print(f"     Data: {result.get('response_size', 0)} bytes")
                
                if "dashboard_sections" in result:
                    print(f"     Sections: {', '.join(result['dashboard_sections'])}")
                elif "agent_count" in result:
                    print(f"     Agents: {result['agent_count']}")
                elif "metric_types" in result:
                    print(f"     Metrics: {', '.join(result['metric_types'])}")
            else:
                print(f"     Error: {result.get('error', 'Unknown error')}")
            
            print()
    
    def test_dashboard_data_quality(self):
        """Test the quality and completeness of dashboard data"""
        print("=" * 60)
        print("DASHBOARD DATA QUALITY TESTING")
        print("=" * 60)
        
        # Get dashboard data
        dashboard_result = self.test_endpoint("/dashboard")
        
        if not dashboard_result["success"]:
            print("✗ Cannot test data quality - dashboard endpoint failed")
            return
        
        try:
            response = requests.get(f"{self.api_url}/dashboard")
            data = response.json()
            
            # Test agents data
            agents = data.get("agents", [])
            print(f"Agents Data:")
            print(f"  Total agents: {len(agents)}")
            
            if agents:
                online_agents = [a for a in agents if a.get("status") == "active"]
                print(f"  Online agents: {len(online_agents)}")
                print(f"  Agent types: {set(a.get('type', 'unknown') for a in agents)}")
                
                # Check agent data completeness
                required_fields = ["id", "name", "status", "type"]
                complete_agents = [a for a in agents if all(field in a for field in required_fields)]
                print(f"  Complete agent records: {len(complete_agents)}/{len(agents)}")
            
            # Test metrics data
            metrics = data.get("metrics", {})
            print(f"\nMetrics Data:")
            if metrics:
                print(f"  Timestamp: {metrics.get('timestamp', 'Missing')}")
                agent_metrics = metrics.get("agents", {})
                if agent_metrics:
                    print(f"  Agent metrics: {', '.join(agent_metrics.keys())}")
                else:
                    print("  No agent metrics")
            else:
                print("  No metrics data")
            
            # Test activities data
            activities = data.get("activities", [])
            print(f"\nActivities Data:")
            print(f"  Recent activities: {len(activities)}")
            
            # Test communications data
            communications = data.get("communications", [])
            print(f"\nCommunications Data:")
            print(f"  Recent communications: {len(communications)}")
            
            # Test projects data
            projects = data.get("projects", [])
            print(f"\nProjects Data:")
            print(f"  Active projects: {len(projects)}")
            
        except Exception as e:
            print(f"✗ Error testing data quality: {e}")
    
    def test_ui_functionality(self):
        """Test specific UI functionality requirements"""
        print("=" * 60)
        print("UI FUNCTIONALITY TESTING")
        print("=" * 60)
        
        # Test agent detail endpoint
        agents_result = self.test_endpoint("/agents")
        if agents_result["success"]:
            try:
                response = requests.get(f"{self.api_url}/agents")
                agents = response.json()
                
                if agents:
                    # Test individual agent endpoint
                    agent_id = agents[0]["id"]
                    agent_detail = self.test_endpoint(f"/agents/{agent_id}")
                    
                    status = "✓ PASS" if agent_detail["success"] else "✗ FAIL"
                    print(f"{status} Agent Detail View")
                    
                    # Test agent metrics endpoint
                    agent_metrics = self.test_endpoint(f"/agents/{agent_id}/metrics")
                    status = "✓ PASS" if agent_metrics["success"] else "✗ FAIL"
                    print(f"{status} Agent Metrics View")
                else:
                    print("✗ No agents to test detail views")
            except:
                print("✗ Error testing agent functionality")
        
        # Test activity creation (POST)
        activity_data = {
            "agentId": "agent-orchestrator",
            "activity": "Test activity creation"
        }
        activity_result = self.test_endpoint("/activities", "POST", activity_data)
        status = "✓ PASS" if activity_result["success"] else "✗ FAIL"
        print(f"{status} Activity Creation")
        
        # Test communication creation (POST)
        comm_data = {
            "from_agent": "test-agent",
            "to_agent": "agent-orchestrator", 
            "message_type": "test",
            "content": {"message": "Test communication"}
        }
        comm_result = self.test_endpoint("/communications", "POST", comm_data)
        status = "✓ PASS" if comm_result["success"] else "✗ FAIL"
        print(f"{status} Communication Recording")
    
    def generate_report(self):
        """Generate a comprehensive test report"""
        print("\n" + "=" * 60)
        print("DASHBOARD TESTING SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        
        print(f"Total tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Show failed tests
        failed_tests = [r for r in self.test_results if not r["success"]]
        if failed_tests:
            print(f"\nFailed tests:")
            for test in failed_tests:
                print(f"  ✗ {test['method']} {test['endpoint']}")
                if "error" in test:
                    print(f"    Error: {test['error']}")
        
        print(f"\nDashboard status: {'✓ HEALTHY' if passed_tests >= total_tests * 0.8 else '⚠ ISSUES FOUND'}")

def main():
    tester = DashboardTester()
    
    # Run all tests
    tester.test_all_endpoints()
    tester.test_dashboard_data_quality()
    tester.test_ui_functionality()
    tester.generate_report()

if __name__ == "__main__":
    main()