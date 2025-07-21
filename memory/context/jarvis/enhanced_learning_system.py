#!/usr/bin/env python3
"""
Enhanced Learning System for Super Agents
Prevents repetitive errors by building persistent knowledge from every action and solution
"""

import sqlite3
import json
import hashlib
import logging
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from contextlib import contextmanager
import pickle
import re

logger = logging.getLogger(__name__)

@dataclass
class LearningPattern:
    """Pattern learned from agent actions and outcomes"""
    pattern_id: str
    pattern_type: str  # error_solution, coding_pattern, workflow_optimization
    context: Dict[str, Any]
    solution: Dict[str, Any]
    success_rate: float
    confidence_level: float
    agent_id: str
    timestamps: List[str]
    tags: List[str]
    related_patterns: List[str] = None
    
    def __post_init__(self):
        if self.related_patterns is None:
            self.related_patterns = []

class EnhancedLearningSystem:
    """
    Builds persistent knowledge from every Super Agent action:
    - TypeScript/JavaScript error patterns
    - API integration solutions 
    - Workflow optimizations
    - Cross-agent knowledge transfer
    - Context-aware mistake prevention
    """
    
    def __init__(self, base_path: str = "./memory/context/jarvis"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.base_path / "learning_patterns.db"
        self.knowledge_base = {}  # pattern_id -> LearningPattern
        self._db_lock = threading.RLock()
        
        # Pattern categories
        self.pattern_types = {
            'typescript_error': 'TypeScript compilation/type errors',
            'api_integration': 'API endpoint and request patterns',  
            'import_resolution': 'Module import and dependency issues',
            'build_configuration': 'Build tool and config problems',
            'authentication': 'Auth flow and token handling',
            'database_query': 'Database operation patterns',
            'workflow_optimization': 'Task execution improvements',
            'security_vulnerability': 'Security issue resolutions'
        }
        
        # Initialize database
        self._init_database()
        self._load_patterns()
        
        logger.info("Enhanced Learning System initialized")
    
    def _init_database(self):
        """Initialize learning patterns database"""
        with self._get_db_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS learning_patterns (
                    pattern_id TEXT PRIMARY KEY,
                    pattern_type TEXT NOT NULL,
                    context_data BLOB NOT NULL,
                    solution_data BLOB NOT NULL,
                    success_rate REAL DEFAULT 1.0,
                    confidence_level REAL DEFAULT 0.5,
                    agent_id TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    usage_count INTEGER DEFAULT 1,
                    tags TEXT DEFAULT ''
                );
                
                CREATE TABLE IF NOT EXISTS pattern_outcomes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_id TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    context_match_score REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (pattern_id) REFERENCES learning_patterns (pattern_id)
                );
                
                CREATE TABLE IF NOT EXISTS agent_knowledge_transfer (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_agent TEXT NOT NULL,
                    to_agent TEXT NOT NULL,
                    pattern_id TEXT NOT NULL,
                    transfer_type TEXT NOT NULL,
                    success BOOLEAN DEFAULT 1,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (pattern_id) REFERENCES learning_patterns (pattern_id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_patterns_type ON learning_patterns(pattern_type);
                CREATE INDEX IF NOT EXISTS idx_patterns_agent ON learning_patterns(agent_id);  
                CREATE INDEX IF NOT EXISTS idx_outcomes_pattern ON pattern_outcomes(pattern_id);
                CREATE INDEX IF NOT EXISTS idx_transfers_timestamp ON agent_knowledge_transfer(timestamp);
            """)
    
    @contextmanager
    def _get_db_connection(self):
        """Get database connection with proper locking"""
        with self._db_lock:
            conn = None
            try:
                conn = sqlite3.connect(str(self.db_path), timeout=30.0)
                conn.row_factory = sqlite3.Row
                yield conn
                conn.commit()
            except Exception as e:
                if conn:
                    conn.rollback()
                logger.error(f"Database error: {e}")
                raise
            finally:
                if conn:
                    conn.close()
    
    def learn_from_action(self, 
                         action_context: Dict[str, Any],
                         solution: Dict[str, Any], 
                         outcome: str,
                         agent_id: str,
                         pattern_type: str = None) -> str:
        """
        Learn from an agent action and its outcome
        
        Args:
            action_context: The problem/task context
            solution: The solution that was applied
            outcome: 'success' or 'failure' 
            agent_id: ID of the agent that performed the action
            pattern_type: Optional specific pattern type
        
        Returns:
            pattern_id of the learned pattern
        """
        
        # Auto-detect pattern type if not provided
        if not pattern_type:
            pattern_type = self._detect_pattern_type(action_context, solution)
        
        # Generate pattern ID
        context_str = json.dumps(action_context, sort_keys=True)
        solution_str = json.dumps(solution, sort_keys=True)
        pattern_id = hashlib.sha256(
            f"{pattern_type}:{context_str}:{solution_str}".encode()
        ).hexdigest()[:16]
        
        # Check if pattern exists
        existing_pattern = self._get_pattern(pattern_id)
        
        if existing_pattern:
            # Update existing pattern
            self._update_pattern_outcome(pattern_id, outcome)
        else:
            # Create new pattern
            pattern = LearningPattern(
                pattern_id=pattern_id,
                pattern_type=pattern_type,
                context=action_context,
                solution=solution,
                success_rate=1.0 if outcome == 'success' else 0.0,
                confidence_level=0.7,
                agent_id=agent_id,
                timestamps=[datetime.now().isoformat()],
                tags=self._extract_tags(action_context, solution)
            )
            
            self._store_pattern(pattern)
            self.knowledge_base[pattern_id] = pattern
        
        # Record outcome
        self._record_pattern_outcome(pattern_id, outcome)
        
        logger.info(f"Learned pattern {pattern_id} from {agent_id} with {outcome}")
        return pattern_id
    
    def _detect_pattern_type(self, context: Dict[str, Any], solution: Dict[str, Any]) -> str:
        """Auto-detect the pattern type from context and solution"""
        
        # TypeScript errors
        if any(keyword in str(context).lower() for keyword in 
               ['typescript', 'type error', 'property does not exist', 'cannot find module']):
            return 'typescript_error'
        
        # API integration
        if any(keyword in str(context).lower() for keyword in 
               ['api', 'endpoint', 'fetch', 'axios', 'http', 'cors']):
            return 'api_integration'
            
        # Import/module issues  
        if any(keyword in str(context).lower() for keyword in
               ['import', 'require', 'module not found', 'cannot resolve']):
            return 'import_resolution'
        
        # Build issues
        if any(keyword in str(context).lower() for keyword in
               ['build', 'webpack', 'vite', 'compilation', 'bundle']):
            return 'build_configuration'
            
        # Authentication
        if any(keyword in str(context).lower() for keyword in
               ['auth', 'token', 'login', 'firebase', 'jwt']):
            return 'authentication'
            
        # Database
        if any(keyword in str(context).lower() for keyword in
               ['database', 'query', 'sql', 'firestore', 'mongodb']):
            return 'database_query'
            
        # Security
        if any(keyword in str(context).lower() for keyword in
               ['security', 'vulnerability', 'exposed', 'api key']):
            return 'security_vulnerability'
        
        return 'workflow_optimization'
    
    def _extract_tags(self, context: Dict[str, Any], solution: Dict[str, Any]) -> List[str]:
        """Extract relevant tags from context and solution"""
        tags = []
        
        # Extract technology tags
        tech_keywords = [
            'react', 'typescript', 'javascript', 'node', 'express', 
            'firebase', 'python', 'fastapi', 'docker', 'git', 
            'npm', 'vite', 'webpack', 'jest', 'api', 'cors'
        ]
        
        combined_text = f"{json.dumps(context)} {json.dumps(solution)}".lower()
        
        for keyword in tech_keywords:
            if keyword in combined_text:
                tags.append(keyword)
        
        # Extract error patterns
        if 'error' in combined_text:
            tags.append('error-fix')
        if 'optimization' in combined_text:
            tags.append('performance')
        if 'security' in combined_text:
            tags.append('security')
            
        return list(set(tags))  # Remove duplicates
    
    def _store_pattern(self, pattern: LearningPattern):
        """Store pattern in database"""
        with self._get_db_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO learning_patterns
                (pattern_id, pattern_type, context_data, solution_data, 
                 success_rate, confidence_level, agent_id, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pattern.pattern_id,
                pattern.pattern_type,
                pickle.dumps(pattern.context),
                pickle.dumps(pattern.solution),
                pattern.success_rate,
                pattern.confidence_level,
                pattern.agent_id,
                json.dumps(pattern.tags)
            ))
    
    def _get_pattern(self, pattern_id: str) -> Optional[LearningPattern]:
        """Retrieve pattern from database"""
        with self._get_db_connection() as conn:
            row = conn.execute(
                "SELECT * FROM learning_patterns WHERE pattern_id = ?",
                (pattern_id,)
            ).fetchone()
            
            if row:
                return LearningPattern(
                    pattern_id=row['pattern_id'],
                    pattern_type=row['pattern_type'],
                    context=pickle.loads(row['context_data']),
                    solution=pickle.loads(row['solution_data']),
                    success_rate=row['success_rate'],
                    confidence_level=row['confidence_level'],
                    agent_id=row['agent_id'],
                    timestamps=[],  # Will be loaded separately if needed
                    tags=json.loads(row['tags']) if row['tags'] else []
                )
        return None
    
    def _update_pattern_outcome(self, pattern_id: str, outcome: str):
        """Update pattern success rate based on new outcome"""
        with self._get_db_connection() as conn:
            # Get current stats
            row = conn.execute("""
                SELECT success_rate, usage_count FROM learning_patterns 
                WHERE pattern_id = ?
            """, (pattern_id,)).fetchone()
            
            if row:
                current_success_rate = row['success_rate'] 
                usage_count = row['usage_count']
                
                # Calculate new success rate
                if outcome == 'success':
                    new_success_rate = (current_success_rate * usage_count + 1.0) / (usage_count + 1)
                else:
                    new_success_rate = (current_success_rate * usage_count) / (usage_count + 1)
                
                # Update pattern
                conn.execute("""
                    UPDATE learning_patterns 
                    SET success_rate = ?, usage_count = usage_count + 1, 
                        updated_at = CURRENT_TIMESTAMP
                    WHERE pattern_id = ?
                """, (new_success_rate, pattern_id))
    
    def _record_pattern_outcome(self, pattern_id: str, outcome: str, context_match_score: float = 1.0):
        """Record individual pattern outcome"""
        with self._get_db_connection() as conn:
            conn.execute("""
                INSERT INTO pattern_outcomes 
                (pattern_id, outcome, context_match_score)
                VALUES (?, ?, ?)
            """, (pattern_id, outcome, context_match_score))
    
    def find_similar_patterns(self, 
                            current_context: Dict[str, Any], 
                            pattern_type: str = None,
                            min_confidence: float = 0.5,
                            limit: int = 5) -> List[LearningPattern]:
        """Find patterns similar to current context to prevent mistakes"""
        
        patterns = []
        
        with self._get_db_connection() as conn:
            query = """
                SELECT pattern_id, pattern_type, context_data, solution_data,
                       success_rate, confidence_level, agent_id, tags
                FROM learning_patterns
                WHERE success_rate >= ? AND confidence_level >= ?
            """
            params = [0.6, min_confidence]  # Only successful patterns
            
            if pattern_type:
                query += " AND pattern_type = ?"
                params.append(pattern_type)
            
            query += " ORDER BY success_rate DESC, confidence_level DESC LIMIT ?"
            params.append(limit)
            
            rows = conn.execute(query, params).fetchall()
            
            for row in rows:
                pattern_context = pickle.loads(row['context_data'])
                similarity_score = self._calculate_context_similarity(current_context, pattern_context)
                
                if similarity_score > 0.3:  # Minimum similarity threshold
                    pattern = LearningPattern(
                        pattern_id=row['pattern_id'],
                        pattern_type=row['pattern_type'], 
                        context=pattern_context,
                        solution=pickle.loads(row['solution_data']),
                        success_rate=row['success_rate'],
                        confidence_level=row['confidence_level'],
                        agent_id=row['agent_id'],
                        timestamps=[],
                        tags=json.loads(row['tags']) if row['tags'] else []
                    )
                    patterns.append(pattern)
        
        return patterns
    
    def _calculate_context_similarity(self, context1: Dict[str, Any], context2: Dict[str, Any]) -> float:
        """Calculate similarity between two contexts"""
        
        # Convert contexts to comparable strings
        str1 = json.dumps(context1, sort_keys=True).lower()
        str2 = json.dumps(context2, sort_keys=True).lower()
        
        # Simple keyword overlap similarity
        words1 = set(re.findall(r'\w+', str1))
        words2 = set(re.findall(r'\w+', str2))
        
        if not words1 or not words2:
            return 0.0
        
        overlap = len(words1.intersection(words2))
        total = len(words1.union(words2))
        
        return overlap / total if total > 0 else 0.0
    
    def get_preventive_guidance(self, 
                              current_context: Dict[str, Any],
                              agent_id: str) -> Dict[str, Any]:
        """Get preventive guidance based on learned patterns"""
        
        # Auto-detect likely pattern type
        likely_pattern_type = self._detect_pattern_type(current_context, {})
        
        # Find similar patterns
        similar_patterns = self.find_similar_patterns(
            current_context, 
            pattern_type=likely_pattern_type,
            limit=3
        )
        
        guidance = {
            'likely_pattern_type': likely_pattern_type,
            'similar_patterns_found': len(similar_patterns),
            'recommendations': [],
            'warnings': [],
            'suggested_solutions': []
        }
        
        for pattern in similar_patterns:
            # Add recommendations
            if pattern.success_rate > 0.8:
                guidance['recommendations'].append({
                    'pattern_id': pattern.pattern_id,
                    'success_rate': pattern.success_rate,
                    'solution': pattern.solution,
                    'tags': pattern.tags
                })
            
            # Add warnings for known failure patterns
            if pattern.success_rate < 0.5:
                guidance['warnings'].append({
                    'pattern_id': pattern.pattern_id,
                    'common_failure': pattern.solution,
                    'failure_rate': 1.0 - pattern.success_rate
                })
        
        return guidance
    
    def transfer_knowledge(self, from_agent: str, to_agent: str, pattern_types: List[str] = None):
        """Transfer knowledge patterns between agents"""
        
        transfer_count = 0
        
        with self._get_db_connection() as conn:
            query = """
                SELECT pattern_id, pattern_type FROM learning_patterns
                WHERE agent_id = ? AND success_rate >= 0.7
            """
            params = [from_agent]
            
            if pattern_types:
                placeholders = ','.join('?' * len(pattern_types))
                query += f" AND pattern_type IN ({placeholders})"
                params.extend(pattern_types)
            
            patterns = conn.execute(query, params).fetchall()
            
            for pattern in patterns:
                # Record knowledge transfer
                conn.execute("""
                    INSERT INTO agent_knowledge_transfer
                    (from_agent, to_agent, pattern_id, transfer_type)
                    VALUES (?, ?, ?, 'automatic')
                """, (from_agent, to_agent, pattern['pattern_id']))
                
                transfer_count += 1
        
        logger.info(f"Transferred {transfer_count} patterns from {from_agent} to {to_agent}")
        return transfer_count
    
    def _load_patterns(self):
        """Load existing patterns into memory for fast access"""
        with self._get_db_connection() as conn:
            rows = conn.execute("""
                SELECT pattern_id, pattern_type, context_data, solution_data,
                       success_rate, confidence_level, agent_id, tags
                FROM learning_patterns
                WHERE success_rate >= 0.5
            """).fetchall()
            
            for row in rows:
                pattern = LearningPattern(
                    pattern_id=row['pattern_id'],
                    pattern_type=row['pattern_type'],
                    context=pickle.loads(row['context_data']),
                    solution=pickle.loads(row['solution_data']),
                    success_rate=row['success_rate'],
                    confidence_level=row['confidence_level'],
                    agent_id=row['agent_id'],
                    timestamps=[],
                    tags=json.loads(row['tags']) if row['tags'] else []
                )
                self.knowledge_base[pattern['pattern_id']] = pattern
    
    def get_learning_report(self) -> Dict[str, Any]:
        """Generate comprehensive learning report"""
        
        with self._get_db_connection() as conn:
            stats = conn.execute("""
                SELECT 
                    pattern_type,
                    COUNT(*) as pattern_count,
                    AVG(success_rate) as avg_success_rate,
                    AVG(confidence_level) as avg_confidence
                FROM learning_patterns
                GROUP BY pattern_type
                ORDER BY pattern_count DESC
            """).fetchall()
            
            total_patterns = conn.execute("SELECT COUNT(*) FROM learning_patterns").fetchone()[0]
            
            recent_transfers = conn.execute("""
                SELECT from_agent, to_agent, COUNT(*) as transfer_count
                FROM agent_knowledge_transfer
                WHERE timestamp >= datetime('now', '-7 days')
                GROUP BY from_agent, to_agent
                ORDER BY transfer_count DESC
            """).fetchall()
        
        report = {
            'total_patterns': total_patterns,
            'pattern_breakdown': [dict(row) for row in stats],
            'recent_knowledge_transfers': [dict(row) for row in recent_transfers],
            'top_performing_patterns': self._get_top_patterns(),
            'learning_effectiveness': self._calculate_learning_effectiveness()
        }
        
        return report
    
    def _get_top_patterns(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top performing patterns"""
        with self._get_db_connection() as conn:
            rows = conn.execute("""
                SELECT pattern_id, pattern_type, success_rate, usage_count, agent_id
                FROM learning_patterns
                WHERE usage_count >= 3
                ORDER BY success_rate DESC, usage_count DESC
                LIMIT ?
            """, (limit,)).fetchall()
            
            return [dict(row) for row in rows]
    
    def _calculate_learning_effectiveness(self) -> float:
        """Calculate overall learning system effectiveness"""
        with self._get_db_connection() as conn:
            result = conn.execute("""
                SELECT AVG(success_rate) FROM learning_patterns
                WHERE usage_count >= 2
            """).fetchone()
            
            return result[0] if result[0] else 0.0

if __name__ == "__main__":
    # Example usage
    learning_system = EnhancedLearningSystem()
    
    # Example: Learn from a TypeScript error fix
    context = {
        "error_type": "typescript_error",
        "error_message": "Property 'x' does not exist on type 'unknown'",
        "file": "src/components/Dashboard.tsx",
        "line": 42
    }
    
    solution = {
        "fix_type": "type_assertion",
        "solution": "Added type assertion: (data as DashboardData).x",
        "additional_changes": ["Added interface DashboardData"]
    }
    
    pattern_id = learning_system.learn_from_action(
        context, solution, 'success', 'development_agent'
    )
    
    print(f"Learned pattern: {pattern_id}")
    
    # Get preventive guidance for similar context
    similar_context = {
        "error_type": "typescript_error", 
        "error_message": "Property 'y' does not exist on type 'unknown'",
        "file": "src/components/Profile.tsx"
    }
    
    guidance = learning_system.get_preventive_guidance(similar_context, 'development_agent')
    print(f"Preventive guidance: {json.dumps(guidance, indent=2)}")