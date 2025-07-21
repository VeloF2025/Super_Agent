#!/usr/bin/env python3
"""
Housekeeper Agent - File System Custodian and Organization Specialist
Advanced file organization, monitoring, and maintenance for Super Agent Team
"""

import os
import json
import hashlib
import shutil
import sqlite3
import gzip
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import re
import mimetypes
import logging
from concurrent.futures import ThreadPoolExecutor
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileType(Enum):
    SOURCE_CODE = "source_code"
    TEST = "test"
    DOCUMENTATION = "documentation"
    CONFIGURATION = "configuration"
    DATA = "data"
    SCRIPT = "script"
    LOG = "log"
    TEMPORARY = "temporary"
    ARTIFACT = "artifact"
    MEDIA = "media"
    UNKNOWN = "unknown"

class CleanupAction(Enum):
    MOVE = "move"
    DELETE = "delete"
    RENAME = "rename"
    ARCHIVE = "archive"
    NO_ACTION = "no_action"

class ApprovalLevel(Enum):
    AUTOMATIC = "automatic"
    OA_APPROVAL = "oa_approval"
    HUMAN_APPROVAL = "human_approval"

@dataclass
class FileClassification:
    file_path: Path
    file_type: FileType
    confidence: float
    reasoning: List[str]
    suggested_location: Path
    current_location_quality: float
    requires_move: bool

@dataclass
class CleanupCandidate:
    file_path: Path
    cleanup_action: CleanupAction
    reason: str
    confidence: float
    approval_level: ApprovalLevel
    space_recovery: int
    risk_factors: List[str]

@dataclass
class OrganizationOperation:
    operation_id: str
    operation_type: str
    file_path: Path
    destination: Optional[Path]
    timestamp: datetime
    reason: str
    approval_required: bool
    approved_by: Optional[str]
    completed: bool
    rollback_data: Optional[Dict]

class HousekeeperAgent:
    """Main Housekeeper Agent for file system organization and maintenance"""
    
    def __init__(self, agent_id: str = "agent-housekeeper-001", 
                 project_root: str = "C:\\Jarvis\\Super Agent"):
        self.agent_id = agent_id
        self.project_root = Path(project_root)
        self.recycle_bin = self.project_root / ".recycle_bin"
        self.db_path = self.project_root / "agents" / "agent-housekeeper" / "housekeeping.db"
        
        # Ensure directories exist
        self.recycle_bin.mkdir(exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self._init_database()
        self._load_configuration()
        
        # Core components
        self.file_classifier = FileClassifier(self)
        self.garbage_detector = GarbageDetector(self)
        self.file_organizer = FileOrganizer(self)
        self.file_monitor = FileMonitor(self)
        self.recycle_manager = RecycleBinManager(self)
        
        # State management
        self.running = False
        self.operation_history = []
        self.pending_operations = []
        
        logger.info(f"Housekeeper Agent {self.agent_id} initialized")
    
    def _init_database(self):
        """Initialize housekeeping database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # File operations history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_operations (
                operation_id TEXT PRIMARY KEY,
                timestamp TEXT,
                operation_type TEXT,
                source_path TEXT,
                destination_path TEXT,
                reason TEXT,
                approved_by TEXT,
                rollback_data TEXT,
                success BOOLEAN
            )
        """)
        
        # File classifications
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_classifications (
                file_path TEXT PRIMARY KEY,
                file_type TEXT,
                confidence REAL,
                classification_time TEXT,
                reasoning TEXT,
                suggested_location TEXT
            )
        """)
        
        # Cleanup history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cleanup_history (
                file_path TEXT,
                cleanup_action TEXT,
                reason TEXT,
                timestamp TEXT,
                space_recovered INTEGER,
                approved_by TEXT
            )
        """)
        
        # Organization patterns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS organization_patterns (
                pattern_id TEXT PRIMARY KEY,
                file_pattern TEXT,
                target_location TEXT,
                confidence REAL,
                usage_count INTEGER,
                last_used TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _load_configuration(self):
        """Load configuration and organization rules"""
        self.organization_rules = {
            "source_code": {
                "extensions": [".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h"],
                "location_pattern": "src/{language}/{module}/",
                "naming_convention": "snake_case_or_PascalCase"
            },
            "tests": {
                "patterns": ["test_*.py", "*.test.js", "*.spec.ts", "*_test.go"],
                "location_pattern": "tests/{type}/",
                "naming_convention": "test_{functionality}"
            },
            "documentation": {
                "extensions": [".md", ".rst", ".txt", ".pdf"],
                "location_pattern": "docs/{category}/",
                "naming_convention": "DESCRIPTIVE_NAME"
            },
            "configuration": {
                "patterns": ["*.config.*", ".*rc", "*.json", "*.yaml", "*.yml"],
                "location_pattern": "config/{category}/",
                "naming_convention": "lowercase-with-hyphens"
            },
            "data": {
                "extensions": [".csv", ".json", ".xml", ".sql", ".parquet"],
                "location_pattern": "data/{type}/",
                "naming_convention": "dataset_YYYYMMDD"
            },
            "temporary": {
                "patterns": ["*.tmp", "*.temp", "~*", ".~*", "*.swp"],
                "location_pattern": "temp/",
                "auto_cleanup_hours": 24
            }
        }
        
        self.garbage_patterns = {
            "temporary_files": {
                "patterns": ["*.tmp", "*.temp", "~*", "*.swp", ".DS_Store"],
                "age_threshold_hours": 24
            },
            "build_artifacts": {
                "patterns": ["*.o", "*.pyc", "__pycache__", "*.class"],
                "exceptions": ["artifacts/", "dist/", "build/"]
            },
            "empty_files": {
                "size_threshold": 0,
                "age_threshold_hours": 1
            },
            "editor_files": {
                "patterns": [".idea/", ".vscode/", "*.sublime-*", ".*.swp"]
            }
        }
    
    def start(self):
        """Start the housekeeper agent"""
        if self.running:
            logger.warning("Housekeeper agent is already running")
            return
        
        logger.info(f"Starting Housekeeper Agent {self.agent_id}")
        self.running = True
        
        # Start file monitoring
        self.file_monitor.start_monitoring()
        
        # Perform initial assessment
        self._perform_initial_assessment()
        
        # Start background tasks
        self._start_background_tasks()
        
        logger.info("Housekeeper Agent started successfully")
    
    def stop(self):
        """Stop the housekeeper agent"""
        logger.info("Stopping Housekeeper Agent")
        self.running = False
        
        if hasattr(self, 'file_monitor'):
            self.file_monitor.stop_monitoring()
        
        logger.info("Housekeeper Agent stopped")
    
    def _perform_initial_assessment(self):
        """Perform initial workspace assessment"""
        logger.info("Performing initial workspace assessment")
        
        # Scan for misplaced files
        misplaced_files = self._scan_for_misplaced_files()
        logger.info(f"Found {len(misplaced_files)} potentially misplaced files")
        
        # Scan for garbage
        garbage_candidates = self.garbage_detector.scan_for_garbage()
        logger.info(f"Found {len(garbage_candidates)} garbage candidates")
        
        # Generate organization report
        self._generate_organization_report(misplaced_files, garbage_candidates)
    
    def _scan_for_misplaced_files(self) -> List[FileClassification]:
        """Scan workspace for misplaced files"""
        misplaced_files = []
        
        # Skip certain directories
        skip_dirs = {'.git', 'node_modules', '.venv', 'venv', '.recycle_bin', '__pycache__'}
        
        for root, dirs, files in os.walk(self.project_root):
            # Remove skip directories from dirs list to prevent walking into them
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            for file in files:
                filepath = Path(root) / file
                
                try:
                    classification = self.file_classifier.classify_file(filepath)
                    
                    if classification.requires_move and classification.confidence > 0.7:
                        misplaced_files.append(classification)
                        
                except Exception as e:
                    logger.debug(f"Error classifying {filepath}: {e}")
        
        return misplaced_files
    
    def _start_background_tasks(self):
        """Start background maintenance tasks"""
        def background_worker():
            while self.running:
                try:
                    # Perform periodic cleanup
                    self._periodic_cleanup()
                    
                    # Clean recycle bin
                    self.recycle_manager.auto_cleanup()
                    
                    # Update organization patterns
                    self._update_organization_patterns()
                    
                    # Update ML & Context Improvements Report
                    self._update_ml_report()
                    
                    # Sleep for 6 hours
                    time.sleep(6 * 3600)
                    
                except Exception as e:
                    logger.error(f"Error in background tasks: {e}")
                    time.sleep(300)  # Sleep 5 minutes on error
        
        thread = threading.Thread(target=background_worker, daemon=True)
        thread.start()
    
    def _periodic_cleanup(self):
        """Perform periodic cleanup operations"""
        logger.info("Performing periodic cleanup")
        
        # Scan for garbage
        garbage_candidates = self.garbage_detector.scan_for_garbage()
        
        # Process automatic cleanup items
        for candidate in garbage_candidates:
            if candidate.approval_level == ApprovalLevel.AUTOMATIC:
                self._execute_cleanup_operation(candidate)
            elif candidate.approval_level == ApprovalLevel.OA_APPROVAL:
                self._request_cleanup_approval(candidate)
    
    def _execute_cleanup_operation(self, candidate: CleanupCandidate) -> bool:
        """Execute a cleanup operation"""
        try:
            if candidate.cleanup_action == CleanupAction.DELETE:
                self.recycle_manager.move_to_recycle(
                    candidate.file_path,
                    candidate.reason,
                    "automatic"
                )
            elif candidate.cleanup_action == CleanupAction.MOVE:
                # Move to appropriate location
                self.file_organizer.organize_file(candidate.file_path, require_approval=False)
            
            # Log the operation
            self._log_cleanup_operation(candidate)
            return True
            
        except Exception as e:
            logger.error(f"Error executing cleanup operation on {candidate.file_path}: {e}")
            return False
    
    def _request_cleanup_approval(self, candidate: CleanupCandidate):
        """Request approval for cleanup operation"""
        approval_request = {
            "from": self.agent_id,
            "to": "agent-orchestrator-001",
            "type": "cleanup_approval_request",
            "file_path": str(candidate.file_path),
            "action": candidate.cleanup_action.value,
            "reason": candidate.reason,
            "confidence": candidate.confidence,
            "space_recovery": candidate.space_recovery,
            "risk_factors": candidate.risk_factors,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send approval request (would integrate with communication system)
        logger.info(f"Requesting approval for cleanup: {candidate.file_path}")
    
    def _log_cleanup_operation(self, candidate: CleanupCandidate):
        """Log cleanup operation to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO cleanup_history 
            (file_path, cleanup_action, reason, timestamp, space_recovered, approved_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (str(candidate.file_path), candidate.cleanup_action.value, 
              candidate.reason, datetime.now().isoformat(),
              candidate.space_recovery, "automatic"))
        
        conn.commit()
        conn.close()
    
    def _generate_organization_report(self, misplaced_files: List[FileClassification],
                                    garbage_candidates: List[CleanupCandidate]):
        """Generate workspace organization report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "workspace_health": {
                "total_files_scanned": 0,
                "misplaced_files": len(misplaced_files),
                "garbage_candidates": len(garbage_candidates),
                "organization_score": 0.0
            },
            "misplaced_files": [asdict(f) for f in misplaced_files[:10]],  # Top 10
            "garbage_summary": {
                "total_space_recoverable": sum(c.space_recovery for c in garbage_candidates),
                "automatic_cleanup_items": len([c for c in garbage_candidates 
                                              if c.approval_level == ApprovalLevel.AUTOMATIC]),
                "approval_required_items": len([c for c in garbage_candidates 
                                              if c.approval_level != ApprovalLevel.AUTOMATIC])
            },
            "recommendations": self._generate_recommendations(misplaced_files, garbage_candidates)
        }
        
        # Save report
        report_path = self.project_root / "agents" / "agent-housekeeper" / "reports"
        report_path.mkdir(exist_ok=True)
        
        report_file = report_path / f"organization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Organization report saved to {report_file}")
    
    def _generate_recommendations(self, misplaced_files: List[FileClassification],
                                garbage_candidates: List[CleanupCandidate]) -> List[str]:
        """Generate organization recommendations"""
        recommendations = []
        
        if misplaced_files:
            recommendations.append(f"Consider organizing {len(misplaced_files)} misplaced files")
        
        auto_cleanup = [c for c in garbage_candidates if c.approval_level == ApprovalLevel.AUTOMATIC]
        if auto_cleanup:
            space = sum(c.space_recovery for c in auto_cleanup)
            recommendations.append(f"Automatic cleanup can recover {self._format_bytes(space)}")
        
        approval_cleanup = [c for c in garbage_candidates if c.approval_level != ApprovalLevel.AUTOMATIC]
        if approval_cleanup:
            space = sum(c.space_recovery for c in approval_cleanup)
            recommendations.append(f"Additional {self._format_bytes(space)} recoverable with approval")
        
        return recommendations
    
    def _update_organization_patterns(self):
        """Update organization patterns based on usage"""
        # This would analyze successful organization operations
        # and update patterns for improved future classification
        pass
    
    def _update_ml_report(self):
        """Update ML & Context Improvements Report"""
        try:
            logger.info("Updating ML & Context Improvements Report")
            
            # Import and run the ML report updater
            import subprocess
            import sys
            
            # Run the updater script
            result = subprocess.run(
                [sys.executable, str(self.project_root / "shared" / "tools" / "ml_report_updater.py"), "--once"],
                capture_output=True,
                text=True,
                cwd=str(self.project_root)
            )
            
            if result.returncode == 0:
                logger.info("ML Report updated successfully")
            else:
                logger.error(f"ML Report update failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Error updating ML report: {e}")
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes value for human readability"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} TB"
    
    def get_status(self) -> Dict[str, Any]:
        """Get current housekeeper status"""
        return {
            "agent_id": self.agent_id,
            "running": self.running,
            "monitoring_active": self.file_monitor.is_monitoring if hasattr(self, 'file_monitor') else False,
            "project_root": str(self.project_root),
            "recycle_bin_items": len(list(self.recycle_bin.glob("*"))) if self.recycle_bin.exists() else 0,
            "pending_operations": len(self.pending_operations),
            "operation_history_count": len(self.operation_history)
        }

class FileClassifier:
    """Intelligent file classification system"""
    
    def __init__(self, housekeeper: HousekeeperAgent):
        self.housekeeper = housekeeper
        self.classification_cache = {}
    
    def classify_file(self, filepath: Path) -> FileClassification:
        """Classify a file and determine optimal placement"""
        if str(filepath) in self.classification_cache:
            return self.classification_cache[str(filepath)]
        
        # Analyze file properties
        file_type = self._detect_file_type(filepath)
        content_analysis = self._analyze_content(filepath)
        context_analysis = self._analyze_context(filepath)
        
        # Determine optimal location
        suggested_location = self._suggest_location(filepath, file_type, content_analysis, context_analysis)
        
        # Calculate current location quality
        current_quality = self._assess_current_location(filepath, file_type)
        
        # Determine if move is required
        requires_move = current_quality < 0.7 and suggested_location != filepath.parent
        
        # Generate reasoning
        reasoning = self._generate_classification_reasoning(
            filepath, file_type, content_analysis, context_analysis, suggested_location
        )
        
        classification = FileClassification(
            file_path=filepath,
            file_type=file_type,
            confidence=self._calculate_confidence(content_analysis, context_analysis),
            reasoning=reasoning,
            suggested_location=suggested_location,
            current_location_quality=current_quality,
            requires_move=requires_move
        )
        
        # Cache the classification
        self.classification_cache[str(filepath)] = classification
        
        return classification
    
    def _detect_file_type(self, filepath: Path) -> FileType:
        """Detect file type based on extension and content"""
        extension = filepath.suffix.lower()
        filename = filepath.name.lower()
        
        # Source code files
        if extension in [".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h"]:
            return FileType.SOURCE_CODE
        
        # Test files
        if any(pattern in filename for pattern in ["test_", ".test.", ".spec.", "_test."]):
            return FileType.TEST
        
        # Documentation files
        if extension in [".md", ".rst", ".txt", ".pdf"]:
            return FileType.DOCUMENTATION
        
        # Configuration files
        if extension in [".json", ".yaml", ".yml", ".toml", ".ini"] or filename.startswith("."):
            return FileType.CONFIGURATION
        
        # Data files
        if extension in [".csv", ".xml", ".sql", ".parquet", ".xlsx"]:
            return FileType.DATA
        
        # Script files
        if extension in [".sh", ".bash", ".ps1", ".bat"] or self._is_executable_script(filepath):
            return FileType.SCRIPT
        
        # Log files
        if extension in [".log", ".out", ".err"] or "log" in filename:
            return FileType.LOG
        
        # Temporary files
        if extension in [".tmp", ".temp"] or filename.startswith("~") or filename.startswith(".~"):
            return FileType.TEMPORARY
        
        # Artifact files
        if extension in [".exe", ".dll", ".so", ".dylib", ".whl", ".jar"]:
            return FileType.ARTIFACT
        
        # Media files
        if extension in [".png", ".jpg", ".jpeg", ".gif", ".svg", ".mp4", ".wav", ".mp3"]:
            return FileType.MEDIA
        
        return FileType.UNKNOWN
    
    def _analyze_content(self, filepath: Path) -> Dict[str, Any]:
        """Analyze file content for classification clues"""
        if not filepath.exists() or filepath.is_dir():
            return {}
        
        try:
            # For text files, analyze content
            if self._is_text_file(filepath):
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(10000)  # Read first 10KB
                
                return {
                    "imports": self._extract_imports(content),
                    "keywords": self._extract_keywords(content),
                    "structure": self._analyze_structure(content),
                    "language": self._detect_language(content, filepath.suffix)
                }
        except Exception as e:
            logger.debug(f"Error analyzing content of {filepath}: {e}")
        
        return {}
    
    def _analyze_context(self, filepath: Path) -> Dict[str, Any]:
        """Analyze file context for classification"""
        try:
            stat = filepath.stat()
            return {
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime),
                "modified": datetime.fromtimestamp(stat.st_mtime),
                "parent_directory": filepath.parent.name,
                "directory_depth": len(filepath.parts) - len(self.housekeeper.project_root.parts)
            }
        except Exception:
            return {}
    
    def _suggest_location(self, filepath: Path, file_type: FileType, 
                         content_analysis: Dict, context_analysis: Dict) -> Path:
        """Suggest optimal location for file"""
        
        if file_type == FileType.SOURCE_CODE:
            language = content_analysis.get("language", "unknown")
            return self.housekeeper.project_root / "src" / language
        
        elif file_type == FileType.TEST:
            return self.housekeeper.project_root / "tests" / "unit"
        
        elif file_type == FileType.DOCUMENTATION:
            return self.housekeeper.project_root / "docs"
        
        elif file_type == FileType.CONFIGURATION:
            return self.housekeeper.project_root / "config"
        
        elif file_type == FileType.DATA:
            return self.housekeeper.project_root / "data" / "raw"
        
        elif file_type == FileType.SCRIPT:
            return self.housekeeper.project_root / "scripts"
        
        elif file_type == FileType.LOG:
            return self.housekeeper.project_root / "logs"
        
        elif file_type == FileType.TEMPORARY:
            return self.housekeeper.project_root / "temp"
        
        elif file_type == FileType.ARTIFACT:
            return self.housekeeper.project_root / "artifacts"
        
        # Default to current location if uncertain
        return filepath.parent
    
    def _assess_current_location(self, filepath: Path, file_type: FileType) -> float:
        """Assess quality of current file location (0.0 to 1.0)"""
        current_dir = filepath.parent
        project_root = self.housekeeper.project_root
        
        # Calculate relative path from project root
        try:
            rel_path = current_dir.relative_to(project_root)
            path_parts = rel_path.parts
        except ValueError:
            return 0.1  # File outside project root
        
        # Score based on file type and location
        if file_type == FileType.SOURCE_CODE:
            if "src" in path_parts:
                return 0.9
            elif any(agent in str(current_dir) for agent in ["agent-", "agents"]):
                return 0.8
            else:
                return 0.3
        
        elif file_type == FileType.TEST:
            if "test" in path_parts:
                return 0.9
            else:
                return 0.2
        
        elif file_type == FileType.DOCUMENTATION:
            if "docs" in path_parts or "doc" in path_parts:
                return 0.9
            else:
                return 0.4
        
        elif file_type == FileType.CONFIGURATION:
            if "config" in path_parts or filepath.name.startswith("."):
                return 0.8
            else:
                return 0.3
        
        elif file_type == FileType.TEMPORARY:
            if "temp" in path_parts or "tmp" in path_parts:
                return 0.9
            else:
                return 0.1  # Temporary files should not be elsewhere
        
        # Default scoring
        return 0.5
    
    def _calculate_confidence(self, content_analysis: Dict, context_analysis: Dict) -> float:
        """Calculate confidence in classification"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on content analysis
        if content_analysis.get("imports"):
            confidence += 0.2
        if content_analysis.get("language") != "unknown":
            confidence += 0.2
        if content_analysis.get("keywords"):
            confidence += 0.1
        
        # Increase confidence based on file size and age
        size = context_analysis.get("size", 0)
        if size > 100:  # Non-empty files are more reliable to classify
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _generate_classification_reasoning(self, filepath: Path, file_type: FileType,
                                         content_analysis: Dict, context_analysis: Dict,
                                         suggested_location: Path) -> List[str]:
        """Generate human-readable reasoning for classification"""
        reasoning = []
        
        # File type reasoning
        reasoning.append(f"Classified as {file_type.value} based on extension and content")
        
        # Content-based reasoning
        if content_analysis.get("language"):
            reasoning.append(f"Detected {content_analysis['language']} programming language")
        
        if content_analysis.get("imports"):
            reasoning.append(f"Contains {len(content_analysis['imports'])} import statements")
        
        # Location reasoning
        if suggested_location != filepath.parent:
            reasoning.append(f"Suggested move to {suggested_location} for better organization")
        
        return reasoning
    
    def _is_text_file(self, filepath: Path) -> bool:
        """Check if file is a text file"""
        try:
            mime_type, _ = mimetypes.guess_type(str(filepath))
            if mime_type and mime_type.startswith('text'):
                return True
            
            # Check first few bytes for text content
            with open(filepath, 'rb') as f:
                chunk = f.read(1024)
                return not bool(chunk.translate(None, bytes(range(32, 127)) + b'\r\n\t'))
        except Exception:
            return False
    
    def _extract_imports(self, content: str) -> List[str]:
        """Extract import statements from content"""
        imports = []
        
        # Python imports
        imports.extend(re.findall(r'^import\s+(\S+)', content, re.MULTILINE))
        imports.extend(re.findall(r'^from\s+(\S+)\s+import', content, re.MULTILINE))
        
        # JavaScript/TypeScript imports
        imports.extend(re.findall(r'import.*from\s+[\'"]([^\'"]+)[\'"]', content))
        imports.extend(re.findall(r'require\([\'"]([^\'"]+)[\'"]\)', content))
        
        return imports
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract domain-specific keywords from content"""
        # This would be more sophisticated in practice
        keywords = []
        content_lower = content.lower()
        
        # Programming keywords
        if any(word in content_lower for word in ['function', 'class', 'def', 'var', 'const']):
            keywords.append('programming')
        
        # Test keywords
        if any(word in content_lower for word in ['test', 'assert', 'expect', 'describe']):
            keywords.append('testing')
        
        # Documentation keywords
        if any(word in content_lower for word in ['api', 'documentation', 'guide', 'readme']):
            keywords.append('documentation')
        
        return keywords
    
    def _analyze_structure(self, content: str) -> Dict[str, Any]:
        """Analyze content structure"""
        lines = content.split('\n')
        return {
            "line_count": len(lines),
            "has_main_function": 'if __name__ == "__main__"' in content,
            "has_class_definitions": bool(re.search(r'class\s+\w+', content)),
            "has_function_definitions": bool(re.search(r'def\s+\w+', content)),
            "comment_ratio": len([l for l in lines if l.strip().startswith('#')]) / max(len(lines), 1)
        }
    
    def _detect_language(self, content: str, extension: str) -> str:
        """Detect programming language"""
        if extension in ['.py']:
            return 'python'
        elif extension in ['.js', '.jsx']:
            return 'javascript'
        elif extension in ['.ts', '.tsx']:
            return 'typescript'
        elif extension in ['.java']:
            return 'java'
        elif extension in ['.cpp', '.cc', '.cxx']:
            return 'cpp'
        elif extension in ['.c']:
            return 'c'
        else:
            return 'unknown'
    
    def _is_executable_script(self, filepath: Path) -> bool:
        """Check if file is an executable script"""
        try:
            with open(filepath, 'rb') as f:
                first_line = f.readline()
                return first_line.startswith(b'#!')
        except Exception:
            return False

class GarbageDetector:
    """Intelligent garbage detection system"""
    
    def __init__(self, housekeeper: HousekeeperAgent):
        self.housekeeper = housekeeper
    
    def scan_for_garbage(self) -> List[CleanupCandidate]:
        """Scan workspace for garbage files"""
        garbage_candidates = []
        
        # Skip certain directories
        skip_dirs = {'.git', 'node_modules', '.venv', 'venv', '.recycle_bin'}
        
        for root, dirs, files in os.walk(self.housekeeper.project_root):
            # Remove skip directories
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            for file in files:
                filepath = Path(root) / file
                candidate = self._analyze_garbage_candidate(filepath)
                
                if candidate and candidate.confidence > 0.5:
                    garbage_candidates.append(candidate)
        
        return garbage_candidates
    
    def _analyze_garbage_candidate(self, filepath: Path) -> Optional[CleanupCandidate]:
        """Analyze if file is a garbage candidate"""
        try:
            stat = filepath.stat()
            file_size = stat.st_size
            file_age = datetime.now() - datetime.fromtimestamp(stat.st_mtime)
            filename = filepath.name.lower()
            
            # Check various garbage patterns
            
            # Temporary files
            if self._is_temporary_file(filepath):
                if file_age.total_seconds() > 24 * 3600:  # 24 hours
                    return CleanupCandidate(
                        file_path=filepath,
                        cleanup_action=CleanupAction.DELETE,
                        reason="Temporary file older than 24 hours",
                        confidence=0.9,
                        approval_level=ApprovalLevel.AUTOMATIC,
                        space_recovery=file_size,
                        risk_factors=[]
                    )
            
            # Empty files
            if file_size == 0 and file_age.total_seconds() > 3600:  # 1 hour
                return CleanupCandidate(
                    file_path=filepath,
                    cleanup_action=CleanupAction.DELETE,
                    reason="Empty file older than 1 hour",
                    confidence=0.8,
                    approval_level=ApprovalLevel.OA_APPROVAL,
                    space_recovery=0,
                    risk_factors=["might_be_placeholder"]
                )
            
            # Build artifacts in wrong locations
            if self._is_build_artifact(filepath) and not self._in_artifact_directory(filepath):
                return CleanupCandidate(
                    file_path=filepath,
                    cleanup_action=CleanupAction.MOVE,
                    reason="Build artifact in wrong location",
                    confidence=0.7,
                    approval_level=ApprovalLevel.OA_APPROVAL,
                    space_recovery=0,
                    risk_factors=["might_be_intentionally_placed"]
                )
            
            # Duplicate files (simplified detection)
            # This would be more sophisticated in practice
            
            return None
            
        except Exception as e:
            logger.debug(f"Error analyzing garbage candidate {filepath}: {e}")
            return None
    
    def _is_temporary_file(self, filepath: Path) -> bool:
        """Check if file matches temporary file patterns"""
        filename = filepath.name.lower()
        
        temp_patterns = ["*.tmp", "*.temp", "~*", ".~*", "*.swp", ".DS_Store"]
        
        for pattern in temp_patterns:
            if pattern.startswith("*") and filename.endswith(pattern[1:]):
                return True
            elif pattern.endswith("*") and filename.startswith(pattern[:-1]):
                return True
            elif pattern == filename:
                return True
        
        return False
    
    def _is_build_artifact(self, filepath: Path) -> bool:
        """Check if file is a build artifact"""
        extension = filepath.suffix.lower()
        artifact_extensions = [".o", ".pyc", ".class", ".exe", ".dll", ".so"]
        
        return extension in artifact_extensions or filepath.name == "__pycache__"
    
    def _in_artifact_directory(self, filepath: Path) -> bool:
        """Check if file is in an appropriate artifact directory"""
        path_parts = filepath.parts
        artifact_dirs = ["artifacts", "build", "dist", "target", "bin"]
        
        return any(dir_name in path_parts for dir_name in artifact_dirs)

class FileOrganizer:
    """File organization and movement system"""
    
    def __init__(self, housekeeper: HousekeeperAgent):
        self.housekeeper = housekeeper
    
    def organize_file(self, filepath: Path, destination: Optional[Path] = None,
                     require_approval: bool = True) -> bool:
        """Organize a file to its correct location"""
        
        if not filepath.exists():
            logger.warning(f"File does not exist: {filepath}")
            return False
        
        # Get file classification
        classification = self.housekeeper.file_classifier.classify_file(filepath)
        
        # Use provided destination or suggested location
        target_location = destination or classification.suggested_location
        
        # Check if move is needed
        if filepath.parent == target_location:
            logger.debug(f"File already in correct location: {filepath}")
            return True
        
        # Request approval if required
        if require_approval and self._requires_approval(filepath, target_location):
            approved = self._request_approval(filepath, target_location, classification.reasoning)
            if not approved:
                logger.info(f"Move operation not approved: {filepath}")
                return False
        
        # Perform the move
        return self._execute_move(filepath, target_location, classification.reasoning)
    
    def _requires_approval(self, filepath: Path, destination: Path) -> bool:
        """Check if file move requires approval"""
        try:
            file_size = filepath.stat().st_size
            
            # Large files require approval
            if file_size > 1024 * 1024:  # 1MB
                return True
            
            # Files in other agents' directories require approval
            if "agent-" in str(filepath) and "agent-housekeeper" not in str(filepath):
                return True
            
            # Cross-team moves require approval
            if self._is_cross_team_move(filepath, destination):
                return True
            
            return False
            
        except Exception:
            return True  # Err on the side of caution
    
    def _is_cross_team_move(self, source: Path, destination: Path) -> bool:
        """Check if move crosses team boundaries"""
        # This would be more sophisticated in practice
        source_parts = source.parts
        dest_parts = destination.parts
        
        # Check if moving between different agent directories
        source_agents = [part for part in source_parts if part.startswith("agent-")]
        dest_agents = [part for part in dest_parts if part.startswith("agent-")]
        
        return source_agents != dest_agents and source_agents and dest_agents
    
    def _request_approval(self, filepath: Path, destination: Path, reasoning: List[str]) -> bool:
        """Request approval for file move"""
        # In practice, this would integrate with the communication system
        logger.info(f"Requesting approval to move {filepath} to {destination}")
        logger.info(f"Reasoning: {'; '.join(reasoning)}")
        
        # For now, automatically approve small, safe moves
        try:
            file_size = filepath.stat().st_size
            if file_size < 100 * 1024:  # Less than 100KB
                return True
        except Exception:
            pass
        
        return False  # Default to no approval for safety
    
    def _execute_move(self, source: Path, destination_dir: Path, reasoning: List[str]) -> bool:
        """Execute file move operation"""
        try:
            # Create destination directory if it doesn't exist
            destination_dir.mkdir(parents=True, exist_ok=True)
            
            # Handle naming conflicts
            destination_path = self._resolve_naming_conflict(destination_dir / source.name)
            
            # Create backup of operation for rollback
            operation_id = f"move_{int(time.time() * 1000)}"
            rollback_data = {
                "original_path": str(source),
                "operation_id": operation_id
            }
            
            # Perform the move
            shutil.move(str(source), str(destination_path))
            
            # Log the operation
            self._log_move_operation(source, destination_path, reasoning, operation_id)
            
            logger.info(f"Successfully moved {source} to {destination_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to move {source} to {destination_dir}: {e}")
            return False
    
    def _resolve_naming_conflict(self, destination_path: Path) -> Path:
        """Resolve naming conflicts at destination"""
        if not destination_path.exists():
            return destination_path
        
        # Add number suffix to resolve conflict
        counter = 1
        while True:
            name_parts = destination_path.stem, str(counter), destination_path.suffix
            new_path = destination_path.parent / "".join(name_parts)
            
            if not new_path.exists():
                return new_path
            
            counter += 1
            
            if counter > 100:  # Safety check
                raise Exception("Too many naming conflicts")
    
    def _log_move_operation(self, source: Path, destination: Path, 
                           reasoning: List[str], operation_id: str):
        """Log file move operation"""
        conn = sqlite3.connect(self.housekeeper.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO file_operations 
            (operation_id, timestamp, operation_type, source_path, destination_path, 
             reason, approved_by, rollback_data, success)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (operation_id, datetime.now().isoformat(), "move", 
              str(source), str(destination), "; ".join(reasoning),
              "housekeeper", json.dumps({"source": str(source)}), True))
        
        conn.commit()
        conn.close()

class FileMonitor(FileSystemEventHandler):
    """Real-time file system monitoring"""
    
    def __init__(self, housekeeper: HousekeeperAgent):
        super().__init__()
        self.housekeeper = housekeeper
        self.observer = Observer()
        self.is_monitoring = False
        self.pending_files = {}
        
    def start_monitoring(self):
        """Start file system monitoring"""
        if self.is_monitoring:
            return
        
        logger.info("Starting file system monitoring")
        
        # Monitor project root
        self.observer.schedule(self, str(self.housekeeper.project_root), recursive=True)
        self.observer.start()
        self.is_monitoring = True
        
        logger.info("File system monitoring started")
    
    def stop_monitoring(self):
        """Stop file system monitoring"""
        if not self.is_monitoring:
            return
        
        logger.info("Stopping file system monitoring")
        self.observer.stop()
        self.observer.join()
        self.is_monitoring = False
        logger.info("File system monitoring stopped")
    
    def on_created(self, event):
        """Handle file creation events"""
        if event.is_directory:
            return
        
        filepath = Path(event.src_path)
        
        # Skip monitoring our own operations
        if ".recycle_bin" in str(filepath) or "housekeeping.db" in str(filepath):
            return
        
        logger.debug(f"File created: {filepath}")
        
        # Analyze file placement after a short delay
        self._schedule_file_analysis(filepath, delay=5)
    
    def on_moved(self, event):
        """Handle file move events"""
        if event.is_directory:
            return
        
        source_path = Path(event.src_path)
        dest_path = Path(event.dest_path)
        
        logger.debug(f"File moved: {source_path} -> {dest_path}")
        
        # Update our classification cache
        if str(source_path) in self.housekeeper.file_classifier.classification_cache:
            del self.housekeeper.file_classifier.classification_cache[str(source_path)]
    
    def _schedule_file_analysis(self, filepath: Path, delay: int):
        """Schedule file analysis after a delay"""
        def analyze_later():
            time.sleep(delay)
            try:
                if filepath.exists():
                    classification = self.housekeeper.file_classifier.classify_file(filepath)
                    
                    if classification.requires_move and classification.confidence > 0.8:
                        logger.info(f"File may need organization: {filepath}")
                        # Could trigger automatic organization here
                        
            except Exception as e:
                logger.debug(f"Error analyzing {filepath}: {e}")
        
        thread = threading.Thread(target=analyze_later, daemon=True)
        thread.start()

class RecycleBinManager:
    """Recycle bin management system"""
    
    def __init__(self, housekeeper: HousekeeperAgent):
        self.housekeeper = housekeeper
        self.recycle_bin = housekeeper.recycle_bin
        self.metadata_file = self.recycle_bin / "metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """Load recycle bin metadata"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading recycle bin metadata: {e}")
        
        return {}
    
    def _save_metadata(self):
        """Save recycle bin metadata"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving recycle bin metadata: {e}")
    
    def move_to_recycle(self, filepath: Path, reason: str, approved_by: str) -> bool:
        """Move file to recycle bin"""
        try:
            if not filepath.exists():
                logger.warning(f"Cannot recycle non-existent file: {filepath}")
                return False
            
            # Create date-based subdirectory
            date_dir = self.recycle_bin / datetime.now().strftime("%Y-%m-%d")
            date_dir.mkdir(exist_ok=True)
            
            # Generate unique name in recycle bin
            recycle_name = self._generate_recycle_name(filepath)
            recycle_path = date_dir / recycle_name
            
            # Move file
            shutil.move(str(filepath), str(recycle_path))
            
            # Update metadata
            self.metadata[str(recycle_path)] = {
                "original_path": str(filepath),
                "deleted_date": datetime.now().isoformat(),
                "reason": reason,
                "approved_by": approved_by,
                "original_size": filepath.stat().st_size if filepath.exists() else 0,
                "expiry_date": (datetime.now() + timedelta(days=30)).isoformat()
            }
            
            self._save_metadata()
            logger.info(f"Moved {filepath} to recycle bin: {recycle_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error moving {filepath} to recycle bin: {e}")
            return False
    
    def _generate_recycle_name(self, filepath: Path) -> str:
        """Generate unique name for file in recycle bin"""
        timestamp = datetime.now().strftime("%H%M%S")
        return f"{timestamp}_{filepath.name}"
    
    def auto_cleanup(self) -> int:
        """Automatically clean up expired items from recycle bin"""
        expired_count = 0
        expired_items = []
        
        for item_path, metadata in self.metadata.items():
            try:
                expiry = datetime.fromisoformat(metadata["expiry_date"])
                
                if datetime.now() > expiry:
                    expired_items.append(item_path)
            except Exception as e:
                logger.debug(f"Error checking expiry for {item_path}: {e}")
                expired_items.append(item_path)  # Remove problematic entries
        
        # Permanently delete expired items
        for item_path in expired_items:
            try:
                if Path(item_path).exists():
                    if Path(item_path).is_dir():
                        shutil.rmtree(item_path)
                    else:
                        Path(item_path).unlink()
                
                if item_path in self.metadata:
                    del self.metadata[item_path]
                
                expired_count += 1
                
            except Exception as e:
                logger.error(f"Error permanently deleting {item_path}: {e}")
        
        if expired_count > 0:
            self._save_metadata()
            logger.info(f"Permanently deleted {expired_count} expired items from recycle bin")
        
        return expired_count
    
    def restore_file(self, recycle_path: str) -> bool:
        """Restore file from recycle bin"""
        try:
            if recycle_path not in self.metadata:
                logger.error(f"File not found in recycle bin metadata: {recycle_path}")
                return False
            
            metadata = self.metadata[recycle_path]
            original_path = Path(metadata["original_path"])
            
            # Create parent directory if needed
            original_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Handle naming conflicts
            restore_path = original_path
            counter = 1
            while restore_path.exists():
                name_parts = original_path.stem, f"_restored_{counter}", original_path.suffix
                restore_path = original_path.parent / "".join(name_parts)
                counter += 1
            
            # Restore file
            shutil.move(recycle_path, str(restore_path))
            
            # Remove from metadata
            del self.metadata[recycle_path]
            self._save_metadata()
            
            logger.info(f"Restored {recycle_path} to {restore_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring {recycle_path}: {e}")
            return False

# Example usage and testing
if __name__ == "__main__":
    # Initialize housekeeper agent
    housekeeper = HousekeeperAgent()
    
    try:
        # Start the agent
        housekeeper.start()
        
        # Get status
        status = housekeeper.get_status()
        print("Housekeeper Agent Status:")
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        # Keep running for demonstration
        print("Housekeeper Agent is running. Press Ctrl+C to stop.")
        
        while True:
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        print("\nStopping Housekeeper Agent...")
        housekeeper.stop()
        print("Housekeeper Agent stopped.")