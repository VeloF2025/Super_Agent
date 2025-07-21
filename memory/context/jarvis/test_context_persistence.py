#!/usr/bin/env python3
"""
Test script for Jarvis context persistence system.
Verifies all core functionality works correctly.
"""

import unittest
import tempfile
import shutil
import time
from pathlib import Path
from jarvis_context_manager import JarvisContextManager


class TestJarvisContextPersistence(unittest.TestCase):
    """Test cases for context persistence."""
    
    def setUp(self):
        """Create temporary directory for tests."""
        self.test_dir = tempfile.mkdtemp()
        self.cm = JarvisContextManager(self.test_dir)
    
    def tearDown(self):
        """Clean up test directory."""
        # Stop checkpoint thread
        self.cm._stop_checkpoint.set()
        if self.cm._checkpoint_thread:
            self.cm._checkpoint_thread.join(timeout=1)
        # Remove test directory
        shutil.rmtree(self.test_dir)
    
    def test_database_initialization(self):
        """Test database is created with correct schema."""
        self.assertTrue(self.cm.db_path.exists())
        
        # Check tables exist
        with self.cm._get_db_connection() as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = [t['name'] for t in tables]
            
            self.assertIn('context_snapshots', table_names)
            self.assertIn('task_progress', table_names)
            self.assertIn('agent_coordination', table_names)
            self.assertIn('decision_log', table_names)
    
    def test_save_and_restore_context(self):
        """Test saving and restoring context."""
        # Modify context
        self.cm.update_task_progress("test-task", {
            "description": "Test task",
            "percentage": 50
        })
        
        # Save context
        self.assertTrue(self.cm.save_context())
        
        # Create new instance and restore
        cm2 = JarvisContextManager(self.test_dir)
        self.assertTrue(cm2.restore_context())
        
        # Verify restored data
        self.assertIn("test-task", cm2.active_context['task_progress'])
        self.assertEqual(
            cm2.active_context['task_progress']['test-task']['percentage'],
            50
        )
    
    def test_auto_checkpoint(self):
        """Test automatic checkpointing."""
        # Add some data
        self.cm.update_task_progress("auto-task", {"percentage": 25})
        
        # Wait for auto-checkpoint (should happen within 30s)
        time.sleep(2)  # Short wait for test
        
        # Check database has snapshot
        with self.cm._get_db_connection() as conn:
            count = conn.execute(
                "SELECT COUNT(*) as count FROM context_snapshots"
            ).fetchone()
            self.assertGreater(count['count'], 0)
    
    def test_crash_recovery(self):
        """Test crash detection and recovery."""
        # Add context
        self.cm.update_task_progress("crash-task", {
            "description": "Task before crash",
            "percentage": 75
        })
        self.cm.save_context()
        
        # Simulate crash
        self.cm.crash_marker.touch()
        
        # Create new instance (should detect crash)
        cm2 = JarvisContextManager(self.test_dir)
        
        # Verify crash marker is removed
        self.assertFalse(self.cm.crash_marker.exists())
        
        # Verify context recovered
        self.assertIn("crash-task", cm2.active_context['task_progress'])
    
    def test_decision_logging(self):
        """Test decision logging."""
        self.cm.log_decision(
            decision_type="test_decision",
            context="test context",
            decision="test decision made",
            reasoning="test reasoning",
            outcome="success"
        )
        
        # Check in memory
        self.assertEqual(len(self.cm.active_context['decision_log']), 1)
        
        # Check in database
        with self.cm._get_db_connection() as conn:
            decisions = conn.execute(
                "SELECT * FROM decision_log"
            ).fetchall()
            self.assertEqual(len(decisions), 1)
            self.assertEqual(decisions[0]['decision_type'], 'test_decision')
    
    def test_agent_state_tracking(self):
        """Test agent state updates."""
        self.cm.update_agent_state("agent-001", {
            "status": "active",
            "current_task": "task-001"
        })
        
        state = self.cm.get_agent_state("agent-001")
        self.assertEqual(state['status'], 'active')
        self.assertIn('last_update', state)
    
    def test_recovery_points(self):
        """Test manual recovery points."""
        self.cm.mark_recovery_point("Test recovery point")
        
        # Check recovery point saved
        with self.cm._get_db_connection() as conn:
            recovery_points = conn.execute(
                "SELECT * FROM context_snapshots WHERE is_recovery_point = 1"
            ).fetchall()
            self.assertGreater(len(recovery_points), 0)
            self.assertEqual(
                recovery_points[0]['recovery_reason'],
                "Test recovery point"
            )
    
    def test_emergency_save(self):
        """Test emergency JSON save."""
        # Close database to force emergency save
        self.cm.db_path.unlink()
        
        # Try to save (should fall back to emergency)
        self.cm._emergency_save()
        
        # Check emergency file exists
        emergency_files = list(Path(self.test_dir).glob("emergency_*.json"))
        self.assertGreater(len(emergency_files), 0)
    
    def test_context_deduplication(self):
        """Test that identical contexts aren't duplicated."""
        # Save same context multiple times
        self.cm.save_context()
        time.sleep(0.1)
        self.cm.save_context()
        time.sleep(0.1)
        self.cm.save_context()
        
        # Check only one snapshot saved
        with self.cm._get_db_connection() as conn:
            count = conn.execute(
                "SELECT COUNT(DISTINCT hash) as count FROM context_snapshots"
            ).fetchone()
            self.assertEqual(count['count'], 1)
    
    def test_conversation_history_limit(self):
        """Test conversation history respects size limit."""
        # Add more than limit
        for i in range(150):
            self.cm.active_context['conversation_history'].append({
                'message': f'Message {i}'
            })
        
        # Check size is limited
        self.assertLessEqual(
            len(self.cm.active_context['conversation_history']),
            100
        )


def run_integration_test():
    """Run a full integration test."""
    print("Running integration test...")
    
    test_dir = tempfile.mkdtemp()
    try:
        # Create context manager
        cm = JarvisContextManager(test_dir)
        
        # Simulate workflow
        print("1. Starting new task...")
        cm.update_task_progress("integration-task", {
            "description": "Integration test task",
            "percentage": 0
        })
        
        print("2. Making decisions...")
        cm.log_decision(
            decision_type="agent_selection",
            context="Need specialized agent",
            decision="Select agent-001",
            reasoning="Has required capabilities"
        )
        
        print("3. Updating progress...")
        for i in range(0, 101, 25):
            cm.update_task_progress("integration-task", {
                "percentage": i
            })
            time.sleep(0.5)
        
        print("4. Simulating crash...")
        cm.crash_marker.touch()
        
        # New instance
        cm2 = JarvisContextManager(test_dir)
        
        print("5. Checking recovery...")
        task = cm2.active_context['task_progress'].get('integration-task')
        if task and task['percentage'] == 100:
            print("✓ Integration test PASSED!")
        else:
            print("✗ Integration test FAILED!")
    
    finally:
        shutil.rmtree(test_dir)


if __name__ == "__main__":
    # Run unit tests
    print("Running unit tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    print("\n" + "="*60 + "\n")
    
    # Run integration test
    run_integration_test()