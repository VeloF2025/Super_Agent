#!/usr/bin/env python3
"""
Directory Context Safety System
Prevents agents from working in wrong directories and ensures safe cross-directory operations
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DirectoryContextSafety:
    """Ensures agents work in correct directories and prompts for confirmation when needed"""
    
    def __init__(self):
        self.base_paths = {
            'super_agent': Path(r'C:\Jarvis\AI Workspace\Super Agent'),
            'jarvis_ai_app': Path(r'C:\Jarvis\AI Workspace\Super Agent\projects\Jarvis AI\app'),
            'memory_context': Path(r'C:\Jarvis\memory\context'),
            'jarvis_main': Path(r'C:\Jarvis')
        }
        
        self.sensitive_directories = {
            'system': ['.git', 'node_modules', '__pycache__', '.venv', 'venv'],
            'config': ['config', 'settings', '.env', 'credentials'],
            'critical': ['shared', 'core', 'system', 'kernel']
        }
        
        self.file_patterns = {
            'config': [r'\.env.*', r'config\..*', r'settings\..*'],
            'system': [r'package\.json', r'requirements\.txt', r'Cargo\.toml'],
            'critical': [r'.*\.key', r'.*\.pem', r'.*\.cert']
        }
        
        self.agent_contexts = {}
        self.load_agent_contexts()
    
    def load_agent_contexts(self):
        """Load known agent working contexts"""
        context_file = self.base_paths['super_agent'] / 'shared' / 'config' / 'agent_contexts.json'
        if context_file.exists():
            try:
                with open(context_file, 'r') as f:
                    self.agent_contexts = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load agent contexts: {e}")
                self.agent_contexts = {}
    
    def save_agent_contexts(self):
        """Save agent working contexts"""
        context_file = self.base_paths['super_agent'] / 'shared' / 'config' / 'agent_contexts.json'
        context_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(context_file, 'w') as f:
            json.dump(self.agent_contexts, f, indent=2)
    
    def validate_directory_context(self, agent_id: str, current_dir: str, target_dir: str) -> Tuple[bool, str, List[str]]:
        """
        Validate if an agent should operate in the target directory
        Returns: (is_safe, risk_level, warnings)
        """
        current_path = Path(current_dir).resolve()
        target_path = Path(target_dir).resolve()
        
        warnings = []
        risk_level = "low"
        
        # Check if paths exist (for files, check parent directory)
        if not current_path.exists():
            warnings.append(f"Current directory does not exist: {current_path}")
            risk_level = "high"
        
        # For file operations, check parent directory
        if not target_path.exists():
            if target_path.parent.exists():
                # File doesn't exist but parent does - this is OK for write operations
                target_path = target_path.parent
            else:
                warnings.append(f"Target directory does not exist: {target_path}")
                risk_level = "high"
        
        # Check if crossing major boundaries
        current_base = self._identify_base_path(current_path)
        target_base = self._identify_base_path(target_path)
        
        if current_base != target_base:
            warnings.append(f"Crossing directory boundary: {current_base} -> {target_base}")
            risk_level = "medium" if risk_level == "low" else risk_level
        
        # Check for sensitive directories
        if self._is_sensitive_directory(target_path):
            warnings.append(f"Target is a sensitive directory: {target_path}")
            risk_level = "high"
        
        # Check agent's known contexts
        if agent_id in self.agent_contexts:
            known_dirs = self.agent_contexts[agent_id].get('known_directories', [])
            if str(target_path) not in known_dirs:
                warnings.append("Target directory is not in agent's known working directories")
                risk_level = "medium" if risk_level == "low" else risk_level
        
        # Determine if safe
        is_safe = risk_level in ["low", "medium"] and len(warnings) < 3
        
        return is_safe, risk_level, warnings
    
    def _identify_base_path(self, path: Path) -> str:
        """Identify which base path a directory belongs to"""
        for name, base_path in self.base_paths.items():
            try:
                path.relative_to(base_path)
                return name
            except ValueError:
                continue
        return "unknown"
    
    def _is_sensitive_directory(self, path: Path) -> bool:
        """Check if a directory is sensitive"""
        path_str = str(path).lower()
        
        # Check directory names
        for category, dirs in self.sensitive_directories.items():
            for sensitive_dir in dirs:
                if sensitive_dir in path_str:
                    return True
        
        # Check if it's a system directory
        if path.name.startswith('.'):
            return True
        
        return False
    
    def confirm_operation(self, agent_id: str, operation: str, source: str, target: str, auto_accept: bool = False) -> bool:
        """
        Confirm if an operation should proceed
        Returns True if safe to proceed, False otherwise
        """
        validation = self.validate_directory_context(agent_id, source, target)
        is_safe, risk_level, warnings = validation
        
        # Log the operation
        logger.info(f"Agent {agent_id} attempting {operation}: {source} -> {target}")
        logger.info(f"Risk level: {risk_level}, Warnings: {len(warnings)}")
        
        if warnings:
            for warning in warnings:
                logger.warning(f"  - {warning}")
        
        # Auto-reject high risk operations
        if risk_level == "high" and not auto_accept:
            logger.error(f"[BLOCKED] High risk operation blocked for agent {agent_id}")
            return False
        
        # Auto-accept low risk operations
        if risk_level == "low" and len(warnings) == 0:
            logger.info(f"[APPROVED] Low risk operation auto-approved")
            self._update_agent_context(agent_id, target)
            return True
        
        # For medium risk, check auto-accept settings
        if risk_level == "medium" and auto_accept:
            logger.info(f"[APPROVED] Medium risk operation auto-approved")
            self._update_agent_context(agent_id, target)
            return True
        
        # Otherwise require manual confirmation
        logger.warning(f"[PENDING] Operation requires manual confirmation")
        return False
    
    def _update_agent_context(self, agent_id: str, directory: str):
        """Update agent's known working directories"""
        if agent_id not in self.agent_contexts:
            self.agent_contexts[agent_id] = {
                'known_directories': [],
                'last_updated': datetime.now().isoformat()
            }
        
        known_dirs = self.agent_contexts[agent_id]['known_directories']
        if directory not in known_dirs:
            known_dirs.append(directory)
            # Keep only last 10 directories
            if len(known_dirs) > 10:
                known_dirs.pop(0)
        
        self.agent_contexts[agent_id]['last_updated'] = datetime.now().isoformat()
        self.save_agent_contexts()
    
    def check_file_operation(self, agent_id: str, file_path: str, operation: str) -> Tuple[bool, str]:
        """
        Check if a file operation is safe
        Returns: (is_safe, reason)
        """
        path = Path(file_path)
        
        # Check if file matches critical patterns
        for category, patterns in self.file_patterns.items():
            for pattern in patterns:
                if re.match(pattern, path.name, re.IGNORECASE):
                    if category == 'critical':
                        return False, f"Critical file pattern detected: {path.name}"
                    elif category == 'system' and operation in ['delete', 'move']:
                        return False, f"System file cannot be {operation}d: {path.name}"
        
        # Check directory context
        file_dir = str(path.parent)
        current_dir = os.getcwd()
        
        is_safe, risk_level, warnings = self.validate_directory_context(
            agent_id, current_dir, file_dir
        )
        
        if not is_safe:
            return False, f"Directory context validation failed: {', '.join(warnings)}"
        
        return True, "Operation approved"
    
    def get_safe_working_directory(self, agent_id: str, requested_dir: Optional[str] = None) -> str:
        """Get a safe working directory for an agent"""
        if requested_dir:
            current_dir = os.getcwd()
            is_safe, _, _ = self.validate_directory_context(agent_id, current_dir, requested_dir)
            if is_safe:
                return requested_dir
        
        # Return agent's last known safe directory
        if agent_id in self.agent_contexts:
            known_dirs = self.agent_contexts[agent_id].get('known_directories', [])
            if known_dirs:
                return known_dirs[-1]
        
        # Default to super agent base
        return str(self.base_paths['super_agent'])


class DirectorySafetyIntegration:
    """Integration layer for directory safety with existing systems"""
    
    def __init__(self):
        self.safety = DirectoryContextSafety()
    
    def wrap_file_operation(self, agent_id: str, operation_func, *args, **kwargs):
        """Wrap a file operation with safety checks"""
        # Extract file path from args
        file_path = None
        if args and isinstance(args[0], (str, Path)):
            file_path = str(args[0])
        elif 'file_path' in kwargs:
            file_path = str(kwargs['file_path'])
        elif 'path' in kwargs:
            file_path = str(kwargs['path'])
        
        if file_path:
            operation_name = operation_func.__name__
            is_safe, reason = self.safety.check_file_operation(agent_id, file_path, operation_name)
            
            if not is_safe:
                logger.error(f"[SAFETY] Operation blocked: {reason}")
                raise PermissionError(f"Directory safety check failed: {reason}")
        
        # Execute operation if safe
        return operation_func(*args, **kwargs)
    
    def get_agent_confirmation(self, agent_id: str, message: str) -> bool:
        """Get confirmation for an operation (placeholder for UI integration)"""
        # In a real implementation, this would interact with the UI
        # For now, log and return based on safety rules
        logger.warning(f"[CONFIRMATION] Agent {agent_id}: {message}")
        
        # Check if we're in auto-accept mode
        auto_accept_file = Path(r'C:\Jarvis\memory\context\jarvis\auto_accept_mode.json')
        if auto_accept_file.exists():
            try:
                with open(auto_accept_file, 'r') as f:
                    auto_settings = json.load(f)
                    if auto_settings.get('enabled', False):
                        confidence = auto_settings.get('confidence_threshold', 0.7)
                        if confidence > 0.8:
                            logger.info("[AUTO-ACCEPTED] High confidence auto-acceptance")
                            return True
            except:
                pass
        
        return False


def main():
    """Test directory safety system"""
    safety = DirectoryContextSafety()
    
    # Test scenarios
    test_cases = [
        ("agent-001", r"C:\Jarvis\AI Workspace\Super Agent", r"C:\Jarvis\AI Workspace\Super Agent\shared"),
        ("agent-002", r"C:\Jarvis\AI Workspace\Super Agent", r"C:\Jarvis\AI Workspace\Super Agent\projects\Jarvis AI\app"),
        ("agent-003", r"C:\Jarvis", r"C:\Windows\System32"),
        ("agent-004", r"C:\Jarvis\AI Workspace\Super Agent", r"C:\Jarvis\AI Workspace\Super Agent\.git"),
    ]
    
    print("[DIRECTORY SAFETY SYSTEM TEST]")
    print("=" * 80)
    
    for agent_id, current, target in test_cases:
        print(f"\nTest: {agent_id}")
        print(f"  Current: {current}")
        print(f"  Target:  {target}")
        
        is_safe, risk, warnings = safety.validate_directory_context(agent_id, current, target)
        approved = safety.confirm_operation(agent_id, "edit", current, target)
        
        print(f"  Risk:     {risk}")
        print(f"  Safe:     {is_safe}")
        print(f"  Approved: {approved}")
        if warnings:
            print("  Warnings:")
            for w in warnings:
                print(f"    - {w}")


if __name__ == "__main__":
    main()