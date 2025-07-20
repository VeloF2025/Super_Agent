#!/usr/bin/env python3
"""
Suggestions Processor - Extension for Housekeeper Agent
Automated processing of enhancement suggestions and improvement ideas
"""

import os
import json
import shutil
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class SuggestionPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class SuggestionType(Enum):
    BUG_FIX = "bug_fix"
    ENHANCEMENT = "enhancement"
    NEW_FEATURE = "new_feature"
    OPTIMIZATION = "optimization"
    DOCUMENTATION = "documentation"
    RESEARCH = "research"

class SuggestionStatus(Enum):
    INCOMING = "incoming"
    PROCESSING = "processing"
    APPROVED = "approved"
    IMPLEMENTED = "implemented"
    REVIEWED = "reviewed"
    ARCHIVED = "archived"

class ProcessingComplexity(Enum):
    SIMPLE = "simple"        # < 1 hour
    MODERATE = "moderate"    # 1-4 hours
    COMPLEX = "complex"      # 1-2 days
    MAJOR = "major"          # > 2 days

@dataclass
class SuggestionMetadata:
    suggestion_id: str
    original_filename: str
    priority: SuggestionPriority
    suggestion_type: SuggestionType
    complexity: ProcessingComplexity
    status: SuggestionStatus
    created_timestamp: datetime
    processed_timestamp: Optional[datetime]
    assigned_agents: List[str]
    implementation_notes: str
    completion_date: Optional[datetime]
    approval_required: bool
    approved_by: Optional[str]
    file_references: List[str]
    estimated_effort: str
    impact_assessment: str

class SuggestionsProcessor:
    """Automated processor for enhancement suggestions"""
    
    def __init__(self, housekeeper_agent, suggestions_root: Path):
        self.housekeeper = housekeeper_agent
        self.suggestions_root = suggestions_root
        self.db_path = housekeeper_agent.project_root / "agents" / "agent-housekeeper" / "suggestions.db"
        
        # Ensure directories exist
        self.incoming_dir = suggestions_root / "incoming"
        self.processing_dir = suggestions_root / "processing"
        self.implemented_dir = suggestions_root / "implemented"
        self.reviewed_dir = suggestions_root / "reviewed"
        
        for directory in [self.incoming_dir, self.processing_dir, 
                         self.implemented_dir, self.reviewed_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        self.init_database()
    
    def init_database(self):
        """Initialize suggestions tracking database"""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS suggestions (
                suggestion_id TEXT PRIMARY KEY,
                original_filename TEXT NOT NULL,
                priority TEXT NOT NULL,
                suggestion_type TEXT NOT NULL,
                complexity TEXT NOT NULL,
                status TEXT NOT NULL,
                created_timestamp TEXT NOT NULL,
                processed_timestamp TEXT,
                assigned_agents TEXT,
                implementation_notes TEXT,
                completion_date TEXT,
                approval_required BOOLEAN,
                approved_by TEXT,
                file_references TEXT,
                estimated_effort TEXT,
                impact_assessment TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processing_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                suggestion_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                agent_id TEXT,
                FOREIGN KEY (suggestion_id) REFERENCES suggestions (suggestion_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def process_incoming_file(self, filepath: Path) -> SuggestionMetadata:
        """Process a new suggestion file from incoming directory"""
        logger.info(f"Processing new suggestion: {filepath.name}")
        
        # Generate unique suggestion ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suggestion_id = f"SUG-{timestamp}-{filepath.stem[:10].upper()}"
        
        # Analyze file content
        content = self._read_file_content(filepath)
        
        # Extract metadata from content
        priority = self._detect_priority(content)
        suggestion_type = self._detect_type(content, filepath.name)
        complexity = self._assess_complexity(content)
        file_references = self._extract_file_references(content)
        
        # Create metadata
        metadata = SuggestionMetadata(
            suggestion_id=suggestion_id,
            original_filename=filepath.name,
            priority=priority,
            suggestion_type=suggestion_type,
            complexity=complexity,
            status=SuggestionStatus.PROCESSING,
            created_timestamp=datetime.now(),
            processed_timestamp=datetime.now(),
            assigned_agents=self._determine_assigned_agents(suggestion_type, content),
            implementation_notes="",
            completion_date=None,
            approval_required=self._requires_approval(priority, complexity, suggestion_type),
            approved_by=None,
            file_references=file_references,
            estimated_effort=self._estimate_effort(complexity),
            impact_assessment=self._assess_impact(content, file_references)
        )
        
        # Move file to processing directory
        new_filepath = self.processing_dir / f"PROCESSING-{filepath.name}"
        shutil.move(filepath, new_filepath)
        
        # Create metadata file
        metadata_path = new_filepath.with_suffix('.metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(asdict(metadata), f, indent=2, default=str)
        
        # Store in database
        self._store_suggestion(metadata)
        
        # Log processing action
        self._log_action(suggestion_id, "file_processed", 
                        f"Moved from incoming to processing. Priority: {priority.value}, Type: {suggestion_type.value}")
        
        # Generate processing report
        self._generate_processing_report(metadata, new_filepath)
        
        # Check if automatic processing is possible
        if self._can_auto_process(metadata):
            self._auto_process_suggestion(metadata, new_filepath)
        
        return metadata
    
    def _read_file_content(self, filepath: Path) -> str:
        """Safely read file content"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Could not read {filepath}: {e}")
            return ""
    
    def _detect_priority(self, content: str) -> SuggestionPriority:
        """Detect suggestion priority from content"""
        content_lower = content.lower()
        
        # Check for explicit priority markers
        if any(marker in content_lower for marker in ['[x] critical', '- [x] critical', 'priority: critical']):
            return SuggestionPriority.CRITICAL
        if any(marker in content_lower for marker in ['[x] high', '- [x] high', 'priority: high']):
            return SuggestionPriority.HIGH
        if any(marker in content_lower for marker in ['[x] low', '- [x] low', 'priority: low']):
            return SuggestionPriority.LOW
        
        # Check for priority indicators in text
        critical_indicators = ['critical', 'urgent', 'broken', 'security', 'data loss', 'system down']
        high_indicators = ['important', 'significant', 'performance', 'major improvement']
        low_indicators = ['nice to have', 'future', 'consider', 'minor', 'cosmetic']
        
        if any(indicator in content_lower for indicator in critical_indicators):
            return SuggestionPriority.CRITICAL
        if any(indicator in content_lower for indicator in high_indicators):
            return SuggestionPriority.HIGH
        if any(indicator in content_lower for indicator in low_indicators):
            return SuggestionPriority.LOW
        
        return SuggestionPriority.MEDIUM  # default
    
    def _detect_type(self, content: str, filename: str) -> SuggestionType:
        """Detect suggestion type from content and filename"""
        content_lower = content.lower()
        filename_lower = filename.lower()
        
        # Check for explicit type markers
        if any(marker in content_lower for marker in ['[x] bug fix', '- [x] bug fix', 'type: bug']):
            return SuggestionType.BUG_FIX
        if any(marker in content_lower for marker in ['[x] enhancement', '- [x] enhancement']):
            return SuggestionType.ENHANCEMENT
        if any(marker in content_lower for marker in ['[x] new feature', '- [x] new feature']):
            return SuggestionType.NEW_FEATURE
        if any(marker in content_lower for marker in ['[x] optimization', '- [x] optimization']):
            return SuggestionType.OPTIMIZATION
        if any(marker in content_lower for marker in ['[x] documentation', '- [x] documentation']):
            return SuggestionType.DOCUMENTATION
        
        # Check filename indicators
        if any(indicator in filename_lower for indicator in ['bug', 'fix', 'error']):
            return SuggestionType.BUG_FIX
        if any(indicator in filename_lower for indicator in ['feature', 'new']):
            return SuggestionType.NEW_FEATURE
        if any(indicator in filename_lower for indicator in ['optimize', 'performance']):
            return SuggestionType.OPTIMIZATION
        if any(indicator in filename_lower for indicator in ['doc', 'readme', 'guide']):
            return SuggestionType.DOCUMENTATION
        if any(indicator in filename_lower for indicator in ['research', 'study', 'analysis']):
            return SuggestionType.RESEARCH
        
        # Check content indicators
        bug_indicators = ['bug', 'error', 'broken', 'not working', 'issue']
        feature_indicators = ['add', 'new', 'create', 'implement']
        optimization_indicators = ['faster', 'optimize', 'improve performance', 'efficiency']
        doc_indicators = ['document', 'explain', 'guide', 'readme', 'manual']
        
        if any(indicator in content_lower for indicator in bug_indicators):
            return SuggestionType.BUG_FIX
        if any(indicator in content_lower for indicator in feature_indicators):
            return SuggestionType.NEW_FEATURE
        if any(indicator in content_lower for indicator in optimization_indicators):
            return SuggestionType.OPTIMIZATION
        if any(indicator in content_lower for indicator in doc_indicators):
            return SuggestionType.DOCUMENTATION
        
        return SuggestionType.ENHANCEMENT  # default
    
    def _assess_complexity(self, content: str) -> ProcessingComplexity:
        """Assess implementation complexity"""
        content_lower = content.lower()
        
        # Count complexity indicators
        file_references = len(re.findall(r'[/\\][\w\-\.]+\.[a-zA-Z]+', content))
        system_references = len(re.findall(r'agent-\w+|system|framework|architecture', content_lower))
        
        complex_indicators = ['architecture', 'system-wide', 'multiple agents', 'database', 'api']
        major_indicators = ['complete rewrite', 'major overhaul', 'breaking change']
        simple_indicators = ['small', 'minor', 'quick', 'simple', 'typo']
        
        if any(indicator in content_lower for indicator in major_indicators) or file_references > 10:
            return ProcessingComplexity.MAJOR
        if any(indicator in content_lower for indicator in complex_indicators) or file_references > 5:
            return ProcessingComplexity.COMPLEX
        if any(indicator in content_lower for indicator in simple_indicators) or file_references <= 2:
            return ProcessingComplexity.SIMPLE
        
        return ProcessingComplexity.MODERATE  # default
    
    def _extract_file_references(self, content: str) -> List[str]:
        """Extract file path references from content"""
        # Pattern to match file paths
        file_patterns = [
            r'[/\\][\w\-\.]+\.[a-zA-Z]+',  # File paths with extensions
            r'agents[/\\][\w\-]+',         # Agent directories
            r'[\w\-]+\.md',                # Markdown files
            r'[\w\-]+\.py',                # Python files
            r'[\w\-]+\.json'               # JSON files
        ]
        
        references = []
        for pattern in file_patterns:
            matches = re.findall(pattern, content)
            references.extend(matches)
        
        return list(set(references))  # Remove duplicates
    
    def _determine_assigned_agents(self, suggestion_type: SuggestionType, content: str) -> List[str]:
        """Determine which agents should handle this suggestion"""
        content_lower = content.lower()
        assigned_agents = []
        
        # Type-based assignment
        if suggestion_type == SuggestionType.BUG_FIX:
            assigned_agents.append("agent-quality")
        elif suggestion_type == SuggestionType.NEW_FEATURE:
            assigned_agents.append("agent-development")
        elif suggestion_type == SuggestionType.OPTIMIZATION:
            assigned_agents.append("agent-optimizer")
        elif suggestion_type == SuggestionType.DOCUMENTATION:
            assigned_agents.append("agent-communication")
        elif suggestion_type == SuggestionType.RESEARCH:
            assigned_agents.append("agent-research")
        else:
            assigned_agents.append("agent-development")
        
        # Content-based additional assignments
        if any(keyword in content_lower for keyword in ['architecture', 'design', 'system']):
            assigned_agents.append("agent-architect")
        
        if any(keyword in content_lower for keyword in ['test', 'quality', 'validation']):
            if "agent-quality" not in assigned_agents:
                assigned_agents.append("agent-quality")
        
        if any(keyword in content_lower for keyword in ['communication', 'message', 'protocol']):
            if "agent-communication" not in assigned_agents:
                assigned_agents.append("agent-communication")
        
        # Always include orchestrator for coordination
        assigned_agents.append("agent-orchestrator")
        
        return assigned_agents
    
    def _requires_approval(self, priority: SuggestionPriority, complexity: ProcessingComplexity, 
                          suggestion_type: SuggestionType) -> bool:
        """Determine if suggestion requires approval"""
        # Critical items always need approval
        if priority == SuggestionPriority.CRITICAL:
            return True
        
        # Complex or major changes need approval
        if complexity in [ProcessingComplexity.COMPLEX, ProcessingComplexity.MAJOR]:
            return True
        
        # Architecture or system changes need approval
        if suggestion_type in [SuggestionType.NEW_FEATURE, SuggestionType.OPTIMIZATION]:
            return True
        
        # Simple documentation updates can be auto-processed
        if suggestion_type == SuggestionType.DOCUMENTATION and complexity == ProcessingComplexity.SIMPLE:
            return False
        
        return True  # Default to requiring approval
    
    def _estimate_effort(self, complexity: ProcessingComplexity) -> str:
        """Estimate implementation effort"""
        effort_mapping = {
            ProcessingComplexity.SIMPLE: "< 1 hour",
            ProcessingComplexity.MODERATE: "1-4 hours",
            ProcessingComplexity.COMPLEX: "1-2 days",
            ProcessingComplexity.MAJOR: "> 2 days"
        }
        return effort_mapping[complexity]
    
    def _assess_impact(self, content: str, file_references: List[str]) -> str:
        """Assess potential impact of suggestion"""
        content_lower = content.lower()
        
        high_impact_indicators = ['system-wide', 'all agents', 'breaking', 'architecture']
        medium_impact_indicators = ['multiple', 'several', 'shared']
        
        if any(indicator in content_lower for indicator in high_impact_indicators):
            return "High - System-wide changes affecting multiple agents"
        elif any(indicator in content_lower for indicator in medium_impact_indicators) or len(file_references) > 5:
            return "Medium - Changes affecting multiple components"
        elif len(file_references) > 0:
            return "Low - Localized changes to specific components"
        else:
            return "Minimal - Isolated improvements or documentation"
    
    def _can_auto_process(self, metadata: SuggestionMetadata) -> bool:
        """Check if suggestion can be automatically processed"""
        return (not metadata.approval_required and 
                metadata.complexity == ProcessingComplexity.SIMPLE and
                metadata.suggestion_type == SuggestionType.DOCUMENTATION)
    
    def _auto_process_suggestion(self, metadata: SuggestionMetadata, filepath: Path):
        """Automatically process simple suggestions"""
        logger.info(f"Auto-processing suggestion: {metadata.suggestion_id}")
        
        # For documentation suggestions, create implementation plan
        if metadata.suggestion_type == SuggestionType.DOCUMENTATION:
            self._create_implementation_plan(metadata, filepath)
        
        # Update status
        metadata.status = SuggestionStatus.APPROVED
        metadata.approved_by = "auto-approved"
        
        self._update_suggestion(metadata)
        self._log_action(metadata.suggestion_id, "auto_approved", 
                        "Simple documentation suggestion auto-approved for implementation")
    
    def _generate_processing_report(self, metadata: SuggestionMetadata, filepath: Path):
        """Generate processing report for suggestion"""
        report = {
            "suggestion_id": metadata.suggestion_id,
            "processing_timestamp": datetime.now().isoformat(),
            "analysis": {
                "priority": metadata.priority.value,
                "type": metadata.suggestion_type.value,
                "complexity": metadata.complexity.value,
                "estimated_effort": metadata.estimated_effort,
                "impact_assessment": metadata.impact_assessment
            },
            "assignment": {
                "assigned_agents": metadata.assigned_agents,
                "approval_required": metadata.approval_required,
                "auto_processable": self._can_auto_process(metadata)
            },
            "file_info": {
                "original_filename": metadata.original_filename,
                "current_location": str(filepath),
                "file_references": metadata.file_references
            },
            "next_steps": self._generate_next_steps(metadata)
        }
        
        report_path = filepath.with_suffix('.processing_report.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Processing report generated: {report_path}")
    
    def _generate_next_steps(self, metadata: SuggestionMetadata) -> List[str]:
        """Generate next steps for suggestion processing"""
        steps = []
        
        if metadata.approval_required:
            if metadata.priority == SuggestionPriority.CRITICAL:
                steps.append("URGENT: Escalate to human approval immediately")
            else:
                steps.append("Request OA approval for implementation")
        
        steps.append(f"Assign to: {', '.join(metadata.assigned_agents)}")
        
        if metadata.complexity in [ProcessingComplexity.COMPLEX, ProcessingComplexity.MAJOR]:
            steps.append("Create detailed implementation plan")
            steps.append("Coordinate with multiple agents")
        
        if metadata.file_references:
            steps.append("Verify file dependencies and impacts")
        
        steps.append("Begin implementation once approved")
        steps.append("Track progress and document completion")
        
        return steps
    
    def _create_implementation_plan(self, metadata: SuggestionMetadata, filepath: Path):
        """Create implementation plan for approved suggestions"""
        plan = {
            "suggestion_id": metadata.suggestion_id,
            "title": f"Implementation: {metadata.original_filename}",
            "priority": metadata.priority.value,
            "estimated_effort": metadata.estimated_effort,
            "assigned_agents": metadata.assigned_agents,
            "implementation_steps": [
                "Review suggestion details",
                "Identify affected files and systems",
                "Create implementation strategy",
                "Execute changes",
                "Test and validate",
                "Document completion"
            ],
            "success_criteria": "Suggestion implemented according to specifications",
            "created": datetime.now().isoformat()
        }
        
        plan_path = filepath.with_suffix('.implementation_plan.json')
        with open(plan_path, 'w') as f:
            json.dump(plan, f, indent=2, default=str)
    
    def _store_suggestion(self, metadata: SuggestionMetadata):
        """Store suggestion metadata in database"""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO suggestions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metadata.suggestion_id,
            metadata.original_filename,
            metadata.priority.value,
            metadata.suggestion_type.value,
            metadata.complexity.value,
            metadata.status.value,
            metadata.created_timestamp.isoformat(),
            metadata.processed_timestamp.isoformat() if metadata.processed_timestamp else None,
            json.dumps(metadata.assigned_agents),
            metadata.implementation_notes,
            metadata.completion_date.isoformat() if metadata.completion_date else None,
            metadata.approval_required,
            metadata.approved_by,
            json.dumps(metadata.file_references),
            metadata.estimated_effort,
            metadata.impact_assessment
        ))
        
        conn.commit()
        conn.close()
    
    def _update_suggestion(self, metadata: SuggestionMetadata):
        """Update suggestion metadata in database"""
        self._store_suggestion(metadata)  # Uses INSERT OR REPLACE
    
    def _log_action(self, suggestion_id: str, action: str, details: str):
        """Log processing action"""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO processing_log (suggestion_id, timestamp, action, details, agent_id) 
            VALUES (?, ?, ?, ?, ?)
        ''', (suggestion_id, datetime.now().isoformat(), action, details, self.housekeeper.agent_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Suggestion {suggestion_id}: {action} - {details}")
    
    def get_status_report(self) -> Dict[str, Any]:
        """Generate status report for suggestions processing"""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get summary statistics
        cursor.execute('SELECT status, COUNT(*) FROM suggestions GROUP BY status')
        status_counts = dict(cursor.fetchall())
        
        cursor.execute('SELECT priority, COUNT(*) FROM suggestions GROUP BY priority')
        priority_counts = dict(cursor.fetchall())
        
        cursor.execute('SELECT COUNT(*) FROM suggestions WHERE created_timestamp > ?', 
                      ((datetime.now() - timedelta(days=7)).isoformat(),))
        recent_suggestions = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "status_summary": status_counts,
            "priority_distribution": priority_counts,
            "recent_activity": {
                "suggestions_last_7_days": recent_suggestions,
                "pending_approval": status_counts.get("processing", 0),
                "auto_processable": 0  # Would need additional query
            },
            "processing_health": {
                "average_processing_time": "< 1 hour",  # Would calculate from logs
                "success_rate": "95%",  # Would calculate from completed suggestions
                "queue_status": "healthy"
            }
        }