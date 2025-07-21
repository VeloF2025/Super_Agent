#!/usr/bin/env python3
"""
Quick test of all dashboard functions
"""

import requests
import json

def test_dashboard():
    base_url = "http://localhost:3001/api"
    
    print("Testing Dashboard Functions...")
    print("=" * 50)
    
    # Test main endpoints
    endpoints = [
        "/health",
        "/dashboard", 
        "/agents",
        "/activities",
        "/communications",
        "/projects",
        "/metrics/current"
    ]
    
    results = {}
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                if isinstance(data, list):
                    count = len(data)
                elif isinstance(data, dict):
                    count = len(data.keys())
                else:
                    count = 1
                    
                results[endpoint] = {"status": "OK", "count": count}
                print(f"[OK] {endpoint} - {count} items")
            else:
                results[endpoint] = {"status": "FAIL", "code": response.status_code}
                print(f"[FAIL] {endpoint} - Status {response.status_code}")
                
        except Exception as e:
            results[endpoint] = {"status": "ERROR", "error": str(e)}
            print(f"[ERROR] {endpoint} - {e}")
    
    print("\n" + "=" * 50)
    
    # Test specific dashboard data
    try:
        response = requests.get(f"{base_url}/dashboard")
        if response.status_code == 200:
            data = response.json()
            
            print("Dashboard Data Summary:")
            print(f"  Agents: {len(data.get('agents', []))}")
            print(f"  Activities: {len(data.get('activities', []))}")
            print(f"  Communications: {len(data.get('communications', []))}")
            print(f"  Projects: {len(data.get('projects', []))}")
            
            # Check metrics
            metrics = data.get('metrics', {})
            if metrics:
                print(f"  Metrics available: YES")
                agent_metrics = metrics.get('agents', {})
                if agent_metrics:
                    print(f"    Agent stats: {list(agent_metrics.keys())}")
            else:
                print(f"  Metrics available: NO")
                
            # Check agent statuses
            agents = data.get('agents', [])
            if agents:
                online_count = sum(1 for a in agents if a.get('status') == 'active')
                print(f"  Agent Status: {online_count}/{len(agents)} online")
                
    except Exception as e:
        print(f"Dashboard data test failed: {e}")
    
    print("\n" + "=" * 50)
    
    # Summary
    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r["status"] == "OK")
    
    print(f"Test Summary: {passed_tests}/{total_tests} endpoints working")
    
    if passed_tests == total_tests:
        print("STATUS: All dashboard functions are working!")
    elif passed_tests >= total_tests * 0.8:
        print("STATUS: Most functions working - minor issues")
    else:
        print("STATUS: Major issues found")

if __name__ == "__main__":
    test_dashboard()