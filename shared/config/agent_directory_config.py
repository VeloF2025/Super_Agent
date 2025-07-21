#!/usr/bin/env python3
"""
Agent Directory Configuration and Safety Protocol
Ensures agents work in appropriate directories and request confirmation when needed
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentDirectoryConfig:
    """Configuration for agent directory permissions and restrictions"""
    
    DEFAULT_CONFIG = {
        "agent-orchestrator": {
            "allowed_paths": [
                "C:\\Jarvis\\AI Workspace\\Super Agent",
                "C:\\Jarvis\\memory\\context",
                "C:\\Jarvis\\AI Workspace\\Super Agent\\shared"
            ],
            "restricted_paths": [
                "C:\\Windows",
                "C:\\Program Files",
                "C:\\Users\\*\\AppData\\Roaming"
            ],
            "require_confirmation": [
                "C:\\Jarvis\\AI Workspace\\Super Agent\\config",
                "C:\\Jarvis\\AI Workspace\\Super Agent\\projects\\*\\config"
            ],
            "read_only_paths": [
                "C:\\Jarvis\\AI Workspace\\Super Agent\\.git",
                "C:\\Jarvis\\AI Workspace\\Super Agent\\node_modules"
            ]
        },
        "agent-architect": {
            "allowed_paths": [
                "C:\\Jarvis\\AI Workspace\\Super Agent",
                "C:\\Jarvis\\AI Workspace\\Super Agent\\projects",
                "C:\\Jarvis\\memory\\context\\jarvis"
            ],
            "restricted_paths": [
                "C:\\Windows",
                "C:\\Program Files"
            ],
            "require_confirmation": [
                "C:\\Jarvis\\AI Workspace\\Super Agent\\shared\\core",
                "C:\\Jarvis\\AI Workspace\\Super Agent\\system"
            ],
            "read_only_paths": []
        },
        "agent-development": {
            "allowed_paths": [
                "C:\\Jarvis\\AI Workspace\\Super Agent\\projects",
                "C:\\Jarvis\\AI Workspace\\Super Agent\\shared\\tools",
                "C:\\Jarvis\\AI Workspace\\Super Agent\\tests"
            ],
            "restricted_paths": [
                "C:\\Jarvis\\AI Workspace\\Super Agent\\config",
                "C:\\Jarvis\\AI Workspace\\Super Agent\\.env"
            ],
            "require_confirmation": [
                "C:\\Jarvis\\AI Workspace\\Super Agent\\shared\\config"
            ],
            "read_only_paths": []
        },
        "agent-housekeeper": {
            "allowed_paths": [
                "C:\\Jarvis\\AI Workspace\\Super Agent\\logs",
                "C:\\Jarvis\\AI Workspace\\Super Agent\\temp",
                "C:\\Jarvis\\AI Workspace\\Super Agent\\cache",
                "C:\\Jarvis\\AI Workspace\\Super Agent\\shared\\heartbeats"
            ],
            "restricted_paths": [
                "C:\\Jarvis\\AI Workspace\\Super Agent\\src",
                "C:\\Jarvis\\AI Workspace\\Super Agent\\core"
            ],
            "require_confirmation": [
                "C:\\Jarvis\\AI Workspace\\Super Agent\\backups"
            ],
            "read_only_paths": [
                "C:\\Jarvis\\AI Workspace\\Super Agent\\projects"
            ]
        },
        "agent-quality": {
            "allowed_paths": [
                "C:\\Jarvis\\AI Workspace\\Super Agent",
                "C:\\Jarvis\\AI Workspace\\Super Agent\\tests",
                "C:\\Jarvis\\AI Workspace\\Super Agent\\reports"
            ],
            "restricted_paths": [],
            "require_confirmation": [
                "C:\\Jarvis\\AI Workspace\\Super Agent\\config"
            ],
            "read_only_paths": []
        },
        "agent-*": {  # Default for all other agents
            "allowed_paths": [
                "C:\\Jarvis\\AI Workspace\\Super Agent",
                "C:\\Jarvis\\memory\\context"
            ],
            "restricted_paths": [
                "C:\\Windows",
                "C:\\Program Files",
                "C:\\System32"
            ],
            "require_confirmation": [
                "C:\\Jarvis\\AI Workspace\\Super Agent\\config",
                "C:\\Jarvis\\AI Workspace\\Super Agent\\.git"
            ],
            "read_only_paths": [
                "C:\\Jarvis\\AI Workspace\\Super Agent\\node_modules"
            ]
        }
    }
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or os.path.join(
            os.path.dirname(__file__), 'agent_directory_rules.json'
        )
        self.config = self._load_config()
        self.confirmation_cache = {}  # Cache user confirmations
    
    def _load_config(self) -> Dict:
        """Load configuration from file or use defaults"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults
                    for agent, rules in self.DEFAULT_CONFIG.items():
                        if agent not in loaded_config:
                            loaded_config[agent] = rules
                    return loaded_config
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
        
        # Save default config
        self._save_config(self.DEFAULT_CONFIG)
        return self.DEFAULT_CONFIG.copy()
    
    def _save_config(self, config: Dict):
        """Save configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def get_agent_rules(self, agent_id: str) -> Dict:
        """Get directory rules for specific agent"""
        # Try exact match first
        if agent_id in self.config:
            return self.config[agent_id]
        
        # Try pattern match (e.g., agent-orchestrator-001 -> agent-orchestrator)
        for pattern in self.config:
            if pattern.endswith('*'):
                prefix = pattern[:-1]
                if agent_id.startswith(prefix):
                    return self.config[pattern]
            elif agent_id.startswith(pattern):
                return self.config[pattern]
        
        # Return default rules
        return self.config.get('agent-*', {
            'allowed_paths': [],
            'restricted_paths': [],
            'require_confirmation': [],
            'read_only_paths': []
        })
    
    def check_path_permission(self, agent_id: str, path: str, operation: str = 'read') -> Dict:
        """
        Check if agent has permission for path operation
        Returns: {
            'allowed': bool,
            'reason': str,
            'requires_confirmation': bool,
            'is_read_only': bool
        }
        """
        rules = self.get_agent_rules(agent_id)
        path = Path(path).resolve()
        path_str = str(path)
        
        result = {
            'allowed': True,
            'reason': 'Path is allowed',
            'requires_confirmation': False,
            'is_read_only': False
        }
        
        # Check restricted paths first
        for restricted in rules.get('restricted_paths', []):
            if self._path_matches(path_str, restricted):
                result['allowed'] = False
                result['reason'] = f"Path is restricted: {restricted}"
                return result
        
        # Check if in allowed paths
        in_allowed = False
        for allowed in rules.get('allowed_paths', []):
            if self._path_matches(path_str, allowed):
                in_allowed = True
                break
        
        if not in_allowed and rules.get('allowed_paths'):
            result['allowed'] = False
            result['reason'] = "Path is not in allowed directories"
            return result
        
        # Check read-only paths
        for read_only in rules.get('read_only_paths', []):
            if self._path_matches(path_str, read_only):
                if operation in ['write', 'delete', 'modify']:
                    result['allowed'] = False
                    result['reason'] = "Path is read-only"
                    return result
                result['is_read_only'] = True
        
        # Check confirmation required
        for confirm_path in rules.get('require_confirmation', []):
            if self._path_matches(path_str, confirm_path):
                result['requires_confirmation'] = True
                result['reason'] = "Path requires confirmation for operations"
        
        return result
    
    def _path_matches(self, path: str, pattern: str) -> bool:
        """Check if path matches pattern (supports wildcards)"""
        # Normalize paths for comparison
        path = path.replace('/', '\\').lower()
        pattern = pattern.replace('/', '\\').lower()
        
        # Handle wildcards
        if '*' in pattern:
            import fnmatch
            return fnmatch.fnmatch(path, pattern)
        
        # Check if path is under pattern directory
        try:
            Path(path).relative_to(Path(pattern))
            return True
        except ValueError:
            return path == pattern
    
    def request_confirmation(self, agent_id: str, operation: str, path: str, 
                           details: Optional[str] = None) -> bool:
        """
        Request user confirmation for operation
        In production, this would interact with UI
        """
        cache_key = f"{agent_id}:{operation}:{path}"
        
        # Check cache
        if cache_key in self.confirmation_cache:
            cache_time, confirmed = self.confirmation_cache[cache_key]
            # Cache valid for 5 minutes
            if (datetime.now() - cache_time).seconds < 300:
                return confirmed
        
        # Log confirmation request
        logger.warning(f"[CONFIRMATION REQUIRED] Agent: {agent_id}")
        logger.warning(f"  Operation: {operation}")
        logger.warning(f"  Path: {path}")
        if details:
            logger.warning(f"  Details: {details}")
        
        # In production, this would show UI dialog
        # For now, check if in auto-accept mode
        auto_accept_file = Path(r'C:\Jarvis\AI Workspace\Super Agent\memory\context\jarvis\auto_accept_mode.json')
        if auto_accept_file.exists():
            try:
                with open(auto_accept_file, 'r') as f:
                    settings = json.load(f)
                    if settings.get('directory_operations', {}).get('auto_confirm', False):
                        logger.info("[AUTO-CONFIRMED] Directory operation auto-accepted")
                        confirmed = True
                    else:
                        confirmed = False
            except:
                confirmed = False
        else:
            confirmed = False
        
        # Cache result
        self.confirmation_cache[cache_key] = (datetime.now(), confirmed)
        
        return confirmed
    
    def add_allowed_path(self, agent_id: str, path: str):
        """Add a path to agent's allowed paths"""
        rules = self.get_agent_rules(agent_id)
        if 'allowed_paths' not in rules:
            rules['allowed_paths'] = []
        
        path = str(Path(path).resolve())
        if path not in rules['allowed_paths']:
            rules['allowed_paths'].append(path)
            
            # Update config
            if agent_id not in self.config:
                self.config[agent_id] = rules
            else:
                self.config[agent_id] = rules
            
            self._save_config(self.config)
            logger.info(f"Added allowed path for {agent_id}: {path}")
    
    def get_safe_working_directory(self, agent_id: str, requested_dir: Optional[str] = None) -> str:
        """Get a safe working directory for agent"""
        rules = self.get_agent_rules(agent_id)
        
        if requested_dir:
            permission = self.check_path_permission(agent_id, requested_dir, 'read')
            if permission['allowed'] and not permission['requires_confirmation']:
                return requested_dir
        
        # Return first allowed path
        allowed_paths = rules.get('allowed_paths', [])
        if allowed_paths:
            return allowed_paths[0]
        
        # Default to Super Agent directory
        return r"C:\Jarvis\AI Workspace\Super Agent"


class DirectoryConfirmationUI:
    """UI integration for directory confirmations (placeholder)"""
    
    @staticmethod
    def show_confirmation_dialog(agent_id: str, operation: str, path: str, 
                               details: Optional[str] = None) -> bool:
        """
        Show confirmation dialog to user
        This is a placeholder - in production would show actual UI
        """
        message = f"""
Directory Operation Confirmation Required

Agent: {agent_id}
Operation: {operation}
Path: {path}
{f'Details: {details}' if details else ''}

This operation requires manual confirmation for safety.
"""
        logger.info(message)
        
        # In production, this would show a dialog
        # For now, return False to be safe
        return False


def main():
    """Test directory configuration"""
    config = AgentDirectoryConfig()
    
    # Test scenarios
    test_cases = [
        ("agent-orchestrator-001", r"C:\Jarvis\AI Workspace\Super Agent\shared\config\test.json", "write"),
        ("agent-development-001", r"C:\Jarvis\AI Workspace\Super Agent\projects\test.py", "write"),
        ("agent-housekeeper-001", r"C:\Jarvis\AI Workspace\Super Agent\logs\cleanup.log", "delete"),
        ("agent-architect-001", r"C:\Windows\System32\config.sys", "read"),
        ("agent-quality-001", r"C:\Jarvis\AI Workspace\Super Agent\.git\config", "write"),
    ]
    
    print("[DIRECTORY PERMISSION TESTS]")
    print("=" * 80)
    
    for agent_id, path, operation in test_cases:
        print(f"\nAgent: {agent_id}")
        print(f"Path: {path}")
        print(f"Operation: {operation}")
        
        result = config.check_path_permission(agent_id, path, operation)
        print(f"Result: {result}")
        
        if result['requires_confirmation']:
            confirmed = config.request_confirmation(agent_id, operation, path)
            print(f"Confirmation: {confirmed}")


if __name__ == "__main__":
    main()