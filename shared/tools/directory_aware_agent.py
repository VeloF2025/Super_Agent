#!/usr/bin/env python3
"""
Directory-Aware Agent Base Class
Provides directory safety checks for all agent operations
"""

import os
import sys
import logging
from pathlib import Path
from typing import Any, Callable, Optional, Dict
from functools import wraps

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from shared.tools.directory_context_safety import DirectoryContextSafety
from shared.config.agent_directory_config import AgentDirectoryConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def directory_safe(operation_type: str = "read"):
    """
    Decorator to ensure directory safety for file operations
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Extract file path from arguments
            file_path = None
            if args and isinstance(args[0], (str, Path)):
                file_path = str(args[0])
            elif 'file_path' in kwargs:
                file_path = str(kwargs['file_path'])
            elif 'path' in kwargs:
                file_path = str(kwargs['path'])
            
            if file_path and hasattr(self, 'check_directory_permission'):
                if not self.check_directory_permission(file_path, operation_type):
                    raise PermissionError(
                        f"Directory safety check failed for {operation_type} on {file_path}"
                    )
            
            return func(self, *args, **kwargs)
        return wrapper
    return decorator


class DirectoryAwareAgent:
    """Base class for directory-aware agents"""
    
    def __init__(self, agent_id: str, agent_name: str):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.directory_safety = DirectoryContextSafety()
        self.directory_config = AgentDirectoryConfig()
        self.working_directory = os.getcwd()
        self.original_directory = os.getcwd()
        
        # Track directory changes
        self.directory_history = [self.working_directory]
        self.max_directory_history = 10
        
        logger.info(f"Initialized {agent_name} with directory awareness")
        logger.info(f"Working directory: {self.working_directory}")
    
    def check_directory_permission(self, path: str, operation: str = "read") -> bool:
        """Check if agent has permission for path operation"""
        permission = self.directory_config.check_path_permission(
            self.agent_id, path, operation
        )
        
        if not permission['allowed']:
            logger.error(f"[BLOCKED] {operation} on {path}: {permission['reason']}")
            return False
        
        if permission['requires_confirmation']:
            confirmed = self.directory_config.request_confirmation(
                self.agent_id, operation, path
            )
            if not confirmed:
                logger.warning(f"[DENIED] User denied {operation} on {path}")
                return False
        
        if permission['is_read_only'] and operation in ['write', 'delete', 'modify']:
            logger.error(f"[BLOCKED] Cannot {operation} read-only path: {path}")
            return False
        
        # Additional safety check
        current_dir = os.getcwd()
        target_dir = os.path.dirname(path) if os.path.isfile(path) else path
        
        is_safe, risk_level, warnings = self.directory_safety.validate_directory_context(
            self.agent_id, current_dir, target_dir
        )
        
        if risk_level == "high":
            logger.error(f"[HIGH RISK] {operation} on {path}: {', '.join(warnings)}")
            return False
        
        return True
    
    def change_directory(self, new_dir: str) -> bool:
        """Safely change working directory"""
        new_path = Path(new_dir).resolve()
        
        if not new_path.exists():
            logger.error(f"Directory does not exist: {new_dir}")
            return False
        
        if not new_path.is_dir():
            logger.error(f"Path is not a directory: {new_dir}")
            return False
        
        # Check permission
        if not self.check_directory_permission(str(new_path), "navigate"):
            return False
        
        try:
            os.chdir(str(new_path))
            self.working_directory = str(new_path)
            
            # Update history
            self.directory_history.append(self.working_directory)
            if len(self.directory_history) > self.max_directory_history:
                self.directory_history.pop(0)
            
            logger.info(f"Changed directory to: {self.working_directory}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to change directory: {e}")
            return False
    
    def get_safe_path(self, requested_path: str) -> Optional[str]:
        """Get a safe version of the requested path"""
        path = Path(requested_path)
        
        # If relative, make it relative to current working directory
        if not path.is_absolute():
            path = Path(self.working_directory) / path
        
        resolved = path.resolve()
        
        # Check if path is safe
        if self.check_directory_permission(str(resolved), "access"):
            return str(resolved)
        
        return None
    
    @directory_safe("read")
    def read_file(self, file_path: str) -> Optional[str]:
        """Safely read a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return None
    
    @directory_safe("write")
    def write_file(self, file_path: str, content: str) -> bool:
        """Safely write to a file"""
        try:
            # Ensure directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Successfully wrote to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write to {file_path}: {e}")
            return False
    
    @directory_safe("delete")
    def delete_file(self, file_path: str) -> bool:
        """Safely delete a file"""
        try:
            Path(file_path).unlink()
            logger.info(f"Successfully deleted {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete {file_path}: {e}")
            return False
    
    def list_directory(self, dir_path: str = ".") -> Optional[Dict[str, list]]:
        """Safely list directory contents"""
        safe_path = self.get_safe_path(dir_path)
        if not safe_path:
            return None
        
        try:
            path = Path(safe_path)
            if not path.is_dir():
                logger.error(f"Not a directory: {safe_path}")
                return None
            
            files = []
            directories = []
            
            for item in path.iterdir():
                if item.is_file():
                    files.append(item.name)
                elif item.is_dir():
                    directories.append(item.name)
            
            return {
                "files": sorted(files),
                "directories": sorted(directories)
            }
            
        except Exception as e:
            logger.error(f"Failed to list directory {safe_path}: {e}")
            return None
    
    def get_working_directory_info(self) -> Dict[str, Any]:
        """Get information about current working directory"""
        return {
            "current": self.working_directory,
            "original": self.original_directory,
            "history": self.directory_history[-5:],  # Last 5 directories
            "safe_directories": self.directory_config.get_agent_rules(self.agent_id).get('allowed_paths', [])
        }
    
    def reset_to_safe_directory(self):
        """Reset to a known safe directory"""
        safe_dir = self.directory_config.get_safe_working_directory(self.agent_id)
        if self.change_directory(safe_dir):
            logger.info(f"Reset to safe directory: {safe_dir}")
        else:
            logger.error("Failed to reset to safe directory")
    
    def before_operation(self, operation: str, target: str):
        """Hook called before any operation"""
        logger.info(f"[{self.agent_name}] Preparing {operation} on {target}")
        
        # Verify we're in expected directory
        if os.getcwd() != self.working_directory:
            logger.warning("Working directory mismatch detected!")
            self.working_directory = os.getcwd()
    
    def after_operation(self, operation: str, target: str, success: bool):
        """Hook called after any operation"""
        status = "SUCCESS" if success else "FAILED"
        logger.info(f"[{self.agent_name}] {operation} on {target}: {status}")
        
        # Update directory context if needed
        if success and operation in ['write', 'create']:
            self.directory_safety._update_agent_context(self.agent_id, os.path.dirname(target))


class SafeFileOperations:
    """Mixin class providing safe file operations"""
    
    def __init__(self, agent: DirectoryAwareAgent):
        self.agent = agent
    
    def safe_read(self, file_path: str) -> Optional[str]:
        """Read file with full safety checks"""
        self.agent.before_operation("read", file_path)
        result = self.agent.read_file(file_path)
        self.agent.after_operation("read", file_path, result is not None)
        return result
    
    def safe_write(self, file_path: str, content: str) -> bool:
        """Write file with full safety checks"""
        self.agent.before_operation("write", file_path)
        result = self.agent.write_file(file_path, content)
        self.agent.after_operation("write", file_path, result)
        return result
    
    def safe_delete(self, file_path: str) -> bool:
        """Delete file with full safety checks"""
        self.agent.before_operation("delete", file_path)
        result = self.agent.delete_file(file_path)
        self.agent.after_operation("delete", file_path, result)
        return result
    
    def safe_copy(self, source: str, destination: str) -> bool:
        """Copy file with full safety checks"""
        # Check both source and destination
        content = self.safe_read(source)
        if content is None:
            return False
        
        return self.safe_write(destination, content)


def main():
    """Test directory-aware agent"""
    # Create test agent
    agent = DirectoryAwareAgent("test-agent-001", "TestAgent")
    
    print(f"[TEST] Agent initialized in: {agent.working_directory}")
    
    # Test operations
    test_file = r"C:\Jarvis\AI Workspace\Super Agent\test_safe_write.txt"
    
    # Test write
    print("\n[TEST] Testing safe write...")
    success = agent.write_file(test_file, "This is a test file")
    print(f"Write result: {success}")
    
    # Test read
    print("\n[TEST] Testing safe read...")
    content = agent.read_file(test_file)
    print(f"Read result: {content[:50] if content else 'Failed'}")
    
    # Test directory listing
    print("\n[TEST] Testing directory listing...")
    contents = agent.list_directory(".")
    if contents:
        print(f"Files: {len(contents['files'])}")
        print(f"Directories: {len(contents['directories'])}")
    
    # Test restricted path
    print("\n[TEST] Testing restricted path...")
    try:
        agent.write_file(r"C:\Windows\test.txt", "Should fail")
    except PermissionError as e:
        print(f"Correctly blocked: {e}")
    
    # Clean up
    if os.path.exists(test_file):
        agent.delete_file(test_file)


if __name__ == "__main__":
    main()