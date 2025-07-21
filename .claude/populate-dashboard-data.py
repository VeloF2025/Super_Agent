#!/usr/bin/env python3
"""
Populate dashboard with test data to verify all UI functions work
Creates real data for activities, communications, and metrics
"""

import requests
import json
from datetime import datetime, timedelta
import uuid

def populate_dashboard():
    base_url = "http://localhost:3001/api"
    
    print("Populating dashboard with test data...")
    
    # 1. Add some communications
    communications = [
        {
            "from_agent": "agent-orchestrator",
            "to_agent": "agent-development", 
            "message_type": "task_assignment",
            "priority": "high",
            "content": {"task": "Review authentication system", "deadline": "2025-01-22"}
        },
        {
            "from_agent": "agent-development",
            "to_agent": "agent-quality",
            "message_type": "code_review_request", 
            "priority": "normal",
            "content": {"component": "user authentication", "branch": "auth-improvements"}
        },
        {
            "from_agent": "agent-quality",
            "to_agent": "agent-orchestrator",
            "message_type": "test_report",
            "priority": "high", 
            "content": {"tests_passed": 45, "tests_failed": 2, "coverage": "89%"}
        },
        {
            "from_agent": "agent-research",
            "to_agent": "agent-architect",
            "message_type": "findings",
            "priority": "normal",
            "content": {"topic": "Microservices patterns", "confidence": 0.92}
        }
    ]
    
    print("Adding communications...")
    for comm in communications:
        try:
            response = requests.post(f"{base_url}/communications", json=comm)
            if response.status_code == 200:
                print(f"  + {comm['from_agent']} -> {comm['to_agent']}")
            else:
                print(f"  - Failed: {comm['from_agent']} -> {comm['to_agent']}")
        except Exception as e:
            print(f"  ! Error: {e}")
    
    # 2. Add some activities
    activities = [
        {
            "agentId": "agent-development",
            "activity": "Implementing user authentication improvements"
        },
        {
            "agentId": "agent-quality", 
            "activity": "Running integration tests on auth module"
        },
        {
            "agentId": "agent-research",
            "activity": "Analyzing microservices architecture patterns"
        },
        {
            "agentId": "agent-architect",
            "activity": "Designing scalable authentication service"
        }
    ]
    
    print("\nAdding activities...")
    activity_ids = []
    for activity in activities:
        try:
            response = requests.post(f"{base_url}/activities", json=activity)
            if response.status_code == 200:
                result = response.json()
                activity_ids.append(result.get("activityId"))
                print(f"  + {activity['agentId']}: {activity['activity']}")
            else:
                print(f"  - Failed: {activity['agentId']}")
        except Exception as e:
            print(f"  ! Error: {e}")
    
    # 3. Complete some activities
    if activity_ids:
        print("\nCompleting some activities...")
        for i, activity_id in enumerate(activity_ids[:2]):  # Complete first 2
            if activity_id:
                try:
                    response = requests.put(
                        f"{base_url}/activities/{activity_id}/complete",
                        json={"result": "Successfully completed"}
                    )
                    if response.status_code == 200:
                        print(f"  + Completed activity {activity_id}")
                except Exception as e:
                    print(f"  ! Error completing {activity_id}: {e}")
    
    print("\nTest data populated!")
    print("Dashboard should now show:")
    print("  - Active communications")
    print("  - Current and completed activities") 
    print("  - Agent interactions")
    print("  - Real metrics and stats")

def test_populated_dashboard():
    """Test the dashboard with populated data"""
    print("\n" + "=" * 50)
    print("TESTING POPULATED DASHBOARD")
    print("=" * 50)
    
    base_url = "http://localhost:3001/api"
    
    try:
        response = requests.get(f"{base_url}/dashboard")
        if response.status_code == 200:
            data = response.json()
            
            print("Current Dashboard State:")
            print(f"  Agents: {len(data.get('agents', []))}")
            
            # Count online agents
            agents = data.get('agents', [])
            online_count = sum(1 for a in agents if a.get('status') == 'active')
            print(f"  Online agents: {online_count}/{len(agents)}")
            
            print(f"  Activities: {len(data.get('activities', []))}")
            print(f"  Communications: {len(data.get('communications', []))}")
            print(f"  Projects: {len(data.get('projects', []))}")
            
            # Test metrics
            metrics = data.get('metrics', {})
            if metrics:
                print("  Metrics: Available")
                agent_metrics = metrics.get('agents', {})
                if agent_metrics:
                    print(f"    Total: {agent_metrics.get('total', 0)}")
                    print(f"    Online: {agent_metrics.get('online', 0)}")
                    print(f"    Working: {agent_metrics.get('working', 0)}")
            
            print("\nUI Components that should be populated:")
            print("  - Agent cards with status indicators")
            print("  - Activity feed with real entries")
            print("  - Communication panel with messages")
            print("  - Metrics dashboard with live data")
            print("  - Project overview")
            
        else:
            print(f"Dashboard API error: {response.status_code}")
            
    except Exception as e:
        print(f"Error testing dashboard: {e}")

if __name__ == "__main__":
    populate_dashboard()
    test_populated_dashboard()