"""
Intelligent Task Routing System
Advanced ML-powered task assignment optimization for Super Agent Team
"""

import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pickle
import sqlite3
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
import pandas as pd

class TaskPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class TaskComplexity(Enum):
    SIMPLE = 1
    MODERATE = 2
    COMPLEX = 3
    VERY_COMPLEX = 4

@dataclass
class Task:
    task_id: str
    task_type: str
    description: str
    priority: TaskPriority
    complexity: TaskComplexity
    required_skills: List[str]
    estimated_duration: float  # hours
    deadline: datetime
    dependencies: List[str]
    context: Dict

@dataclass
class Agent:
    agent_id: str
    role: str
    team: str
    skills: Dict[str, float]  # skill -> proficiency (0.0-1.0)
    current_load: float  # 0.0-1.0
    performance_history: Dict[str, float]  # task_type -> success_rate
    availability: bool
    specializations: List[str]

@dataclass
class RoutingDecision:
    primary_agent: str
    backup_agents: List[str]
    confidence: float
    reasoning: str
    estimated_completion_time: float
    risk_assessment: Dict

class SkillMatrix:
    """Manages agent skills and capabilities"""
    
    def __init__(self):
        self.skills_db = {}
        self.skill_categories = {
            "technical": ["programming", "architecture", "debugging", "testing"],
            "research": ["information_gathering", "analysis", "verification", "synthesis"],
            "communication": ["documentation", "presentation", "translation", "coordination"],
            "innovation": ["creativity", "pattern_recognition", "breakthrough_thinking"],
            "quality": ["validation", "optimization", "security", "performance"]
        }
    
    def update_agent_skills(self, agent_id: str, skills: Dict[str, float]):
        """Update agent skill proficiencies"""
        self.skills_db[agent_id] = skills
        self._normalize_skills(agent_id)
    
    def get_skill_match(self, agent_id: str, required_skills: List[str]) -> float:
        """Calculate skill match score for agent and task"""
        if agent_id not in self.skills_db:
            return 0.0
        
        agent_skills = self.skills_db[agent_id]
        total_match = 0.0
        total_weight = 0.0
        
        for skill in required_skills:
            if skill in agent_skills:
                skill_level = agent_skills[skill]
                weight = self._get_skill_weight(skill)
                total_match += skill_level * weight
                total_weight += weight
            else:
                # Penalty for missing critical skills
                total_weight += self._get_skill_weight(skill)
        
        return total_match / total_weight if total_weight > 0 else 0.0
    
    def _normalize_skills(self, agent_id: str):
        """Normalize skill values to 0.0-1.0 range"""
        skills = self.skills_db[agent_id]
        max_val = max(skills.values()) if skills else 1.0
        if max_val > 1.0:
            self.skills_db[agent_id] = {k: v/max_val for k, v in skills.items()}
    
    def _get_skill_weight(self, skill: str) -> float:
        """Get importance weight for skill"""
        critical_skills = ["programming", "architecture", "verification", "innovation"]
        return 1.5 if skill in critical_skills else 1.0

class AvailabilityTracker:
    """Tracks agent availability and current workload"""
    
    def __init__(self):
        self.agent_loads = {}
        self.agent_schedules = {}
        self.performance_metrics = {}
    
    def update_agent_load(self, agent_id: str, current_load: float):
        """Update agent's current workload (0.0-1.0)"""
        self.agent_loads[agent_id] = min(max(current_load, 0.0), 1.0)
    
    def get_current_load(self, agent_id: str) -> float:
        """Get agent's current workload"""
        return self.agent_loads.get(agent_id, 0.0)
    
    def predict_availability(self, agent_id: str, task_duration: float) -> float:
        """Predict agent availability for task duration"""
        current_load = self.get_current_load(agent_id)
        
        # Factor in historical performance
        if agent_id in self.performance_metrics:
            avg_efficiency = self.performance_metrics[agent_id].get("efficiency", 1.0)
            adjusted_duration = task_duration / avg_efficiency
        else:
            adjusted_duration = task_duration
        
        # Calculate availability score
        load_factor = 1.0 - current_load
        duration_factor = max(0.1, 1.0 - (adjusted_duration / 8.0))  # 8 hour workday
        
        return load_factor * duration_factor
    
    def get_load_distribution(self) -> Dict[str, float]:
        """Get current load distribution across all agents"""
        return self.agent_loads.copy()

class TaskHistoryAnalyzer:
    """Analyzes historical task performance for optimization"""
    
    def __init__(self, db_path: str = "task_history.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize task history database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_history (
                task_id TEXT PRIMARY KEY,
                agent_id TEXT,
                task_type TEXT,
                complexity INTEGER,
                priority TEXT,
                duration_planned REAL,
                duration_actual REAL,
                quality_score REAL,
                success BOOLEAN,
                timestamp TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_performance (
                agent_id TEXT,
                task_type TEXT,
                success_rate REAL,
                avg_quality REAL,
                avg_efficiency REAL,
                last_updated TEXT,
                PRIMARY KEY (agent_id, task_type)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def record_task_completion(self, task_id: str, agent_id: str, task_type: str,
                             complexity: int, priority: str, duration_planned: float,
                             duration_actual: float, quality_score: float, success: bool):
        """Record completed task for analysis"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO task_history 
            (task_id, agent_id, task_type, complexity, priority, duration_planned, 
             duration_actual, quality_score, success, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (task_id, agent_id, task_type, complexity, priority, duration_planned,
              duration_actual, quality_score, success, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        # Update agent performance metrics
        self._update_agent_performance(agent_id, task_type)
    
    def get_agent_performance(self, agent_id: str, task_type: str = None) -> Dict:
        """Get agent performance metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if task_type:
            cursor.execute("""
                SELECT success_rate, avg_quality, avg_efficiency 
                FROM agent_performance 
                WHERE agent_id = ? AND task_type = ?
            """, (agent_id, task_type))
        else:
            cursor.execute("""
                SELECT task_type, success_rate, avg_quality, avg_efficiency 
                FROM agent_performance 
                WHERE agent_id = ?
            """, (agent_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        if task_type and results:
            return {
                "success_rate": results[0][0],
                "avg_quality": results[0][1],
                "avg_efficiency": results[0][2]
            }
        elif not task_type:
            return {row[0]: {
                "success_rate": row[1],
                "avg_quality": row[2],
                "avg_efficiency": row[3]
            } for row in results}
        else:
            return {"success_rate": 0.8, "avg_quality": 0.85, "avg_efficiency": 1.0}
    
    def _update_agent_performance(self, agent_id: str, task_type: str):
        """Update agent performance metrics based on recent history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate metrics from recent history (last 30 days)
        thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
        
        cursor.execute("""
            SELECT success, quality_score, duration_planned, duration_actual
            FROM task_history 
            WHERE agent_id = ? AND task_type = ? AND timestamp > ?
        """, (agent_id, task_type, thirty_days_ago))
        
        results = cursor.fetchall()
        
        if results:
            successes = [r[0] for r in results]
            qualities = [r[1] for r in results if r[1] is not None]
            efficiencies = [r[2]/r[3] for r in results if r[3] > 0]
            
            success_rate = sum(successes) / len(successes)
            avg_quality = sum(qualities) / len(qualities) if qualities else 0.85
            avg_efficiency = sum(efficiencies) / len(efficiencies) if efficiencies else 1.0
            
            cursor.execute("""
                INSERT OR REPLACE INTO agent_performance 
                (agent_id, task_type, success_rate, avg_quality, avg_efficiency, last_updated)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (agent_id, task_type, success_rate, avg_quality, avg_efficiency, 
                  datetime.now().isoformat()))
        
        conn.commit()
        conn.close()

class MLRoutingEngine:
    """Machine learning engine for intelligent task routing"""
    
    def __init__(self):
        self.skill_predictor = RandomForestRegressor(n_estimators=100, random_state=42)
        self.success_predictor = GradientBoostingClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = []
    
    def train(self, training_data: List[Dict]):
        """Train ML models with historical data"""
        if not training_data:
            return
        
        # Prepare features and targets
        features = []
        skill_targets = []
        success_targets = []
        
        for data in training_data:
            feature_vector = self._extract_features(data)
            features.append(feature_vector)
            skill_targets.append(data["skill_match_score"])
            success_targets.append(1 if data["success"] else 0)
        
        features = np.array(features)
        skill_targets = np.array(skill_targets)
        success_targets = np.array(success_targets)
        
        # Scale features
        features_scaled = self.scaler.fit_transform(features)
        
        # Train models
        self.skill_predictor.fit(features_scaled, skill_targets)
        self.success_predictor.fit(features_scaled, success_targets)
        
        self.is_trained = True
    
    def predict_best_agents(self, task_type: str, required_skills: List[str],
                           complexity: TaskComplexity, deadline: datetime,
                           available_agents: List[Agent]) -> List[Tuple[str, float]]:
        """Predict best agents for task using ML"""
        if not self.is_trained:
            # Fallback to rule-based approach
            return self._rule_based_prediction(task_type, required_skills, 
                                             complexity, available_agents)
        
        agent_scores = []
        
        for agent in available_agents:
            # Extract features for prediction
            features = self._extract_agent_task_features(agent, task_type, 
                                                       required_skills, complexity)
            features_scaled = self.scaler.transform([features])
            
            # Predict skill match and success probability
            skill_score = self.skill_predictor.predict(features_scaled)[0]
            success_prob = self.success_predictor.predict_proba(features_scaled)[0][1]
            
            # Combined score
            combined_score = (skill_score * 0.6) + (success_prob * 0.4)
            agent_scores.append((agent.agent_id, combined_score))
        
        # Sort by score descending
        agent_scores.sort(key=lambda x: x[1], reverse=True)
        return agent_scores[:5]  # Top 5 candidates
    
    def _extract_features(self, data: Dict) -> List[float]:
        """Extract features from training data"""
        return [
            data.get("complexity", 2),
            data.get("agent_load", 0.5),
            data.get("skill_match", 0.7),
            data.get("task_priority", 2),  # Encoded priority
            data.get("agent_experience", 0.8),
            data.get("deadline_pressure", 0.3)
        ]
    
    def _extract_agent_task_features(self, agent: Agent, task_type: str,
                                   required_skills: List[str], 
                                   complexity: TaskComplexity) -> List[float]:
        """Extract features for agent-task pair"""
        skill_match = sum(agent.skills.get(skill, 0) for skill in required_skills) / len(required_skills)
        experience = agent.performance_history.get(task_type, 0.8)
        
        return [
            complexity.value,
            agent.current_load,
            skill_match,
            2,  # Default priority encoding
            experience,
            0.3  # Default deadline pressure
        ]
    
    def _rule_based_prediction(self, task_type: str, required_skills: List[str],
                             complexity: TaskComplexity, 
                             available_agents: List[Agent]) -> List[Tuple[str, float]]:
        """Fallback rule-based agent selection"""
        agent_scores = []
        
        for agent in available_agents:
            # Calculate skill match
            skill_score = sum(agent.skills.get(skill, 0) for skill in required_skills)
            skill_score /= len(required_skills) if required_skills else 1
            
            # Factor in load and performance
            load_factor = 1.0 - agent.current_load
            performance_factor = agent.performance_history.get(task_type, 0.8)
            
            # Combined score
            combined_score = (skill_score * 0.5) + (load_factor * 0.3) + (performance_factor * 0.2)
            agent_scores.append((agent.agent_id, combined_score))
        
        agent_scores.sort(key=lambda x: x[1], reverse=True)
        return agent_scores[:5]

class IntelligentTaskRouter:
    """Main intelligent task routing system"""
    
    def __init__(self):
        self.skill_matrix = SkillMatrix()
        self.availability_tracker = AvailabilityTracker()
        self.task_history = TaskHistoryAnalyzer()
        self.ml_engine = MLRoutingEngine()
        self.agents = {}
        
        # Load trained models if available
        self._load_models()
    
    def register_agent(self, agent: Agent):
        """Register agent in the system"""
        self.agents[agent.agent_id] = agent
        self.skill_matrix.update_agent_skills(agent.agent_id, agent.skills)
        self.availability_tracker.update_agent_load(agent.agent_id, agent.current_load)
    
    def route_task(self, task: Task) -> RoutingDecision:
        """Route task to optimal agent using intelligent algorithms"""
        
        # Get available agents
        available_agents = [agent for agent in self.agents.values() if agent.availability]
        
        if not available_agents:
            return RoutingDecision(
                primary_agent=None,
                backup_agents=[],
                confidence=0.0,
                reasoning="No agents available",
                estimated_completion_time=0.0,
                risk_assessment={"risk_level": "high", "reason": "no_agents"}
            )
        
        # Use ML engine to get agent recommendations
        agent_candidates = self.ml_engine.predict_best_agents(
            task.task_type,
            task.required_skills,
            task.complexity,
            task.deadline,
            available_agents
        )
        
        # Select optimal agent considering multiple factors
        best_agent = self._select_optimal_agent(
            agent_candidates,
            task,
            available_agents
        )
        
        # Identify backup agents
        backup_agents = self._identify_backup_agents(agent_candidates, best_agent[0])
        
        # Calculate confidence and risk assessment
        confidence = self._calculate_confidence(best_agent, task)
        risk_assessment = self._assess_risk(best_agent[0], task)
        
        # Estimate completion time
        estimated_time = self._estimate_completion_time(best_agent[0], task)
        
        return RoutingDecision(
            primary_agent=best_agent[0],
            backup_agents=backup_agents,
            confidence=confidence,
            reasoning=self._generate_reasoning(best_agent, task),
            estimated_completion_time=estimated_time,
            risk_assessment=risk_assessment
        )
    
    def _select_optimal_agent(self, candidates: List[Tuple[str, float]], 
                            task: Task, available_agents: List[Agent]) -> Tuple[str, float]:
        """Select optimal agent from candidates"""
        if not candidates:
            return (available_agents[0].agent_id, 0.5)
        
        # Factor in current load and availability
        adjusted_scores = []
        for agent_id, score in candidates:
            agent = self.agents[agent_id]
            
            # Availability factor
            availability_score = self.availability_tracker.predict_availability(
                agent_id, task.estimated_duration
            )
            
            # Performance history factor
            performance = self.task_history.get_agent_performance(agent_id, task.task_type)
            performance_factor = performance.get("success_rate", 0.8)
            
            # Adjust score
            adjusted_score = score * 0.5 + availability_score * 0.3 + performance_factor * 0.2
            adjusted_scores.append((agent_id, adjusted_score))
        
        # Return best adjusted score
        return max(adjusted_scores, key=lambda x: x[1])
    
    def _identify_backup_agents(self, candidates: List[Tuple[str, float]], 
                              primary_agent: str) -> List[str]:
        """Identify backup agents"""
        backups = [agent_id for agent_id, _ in candidates if agent_id != primary_agent]
        return backups[:3]  # Top 3 backup agents
    
    def _calculate_confidence(self, best_agent: Tuple[str, float], task: Task) -> float:
        """Calculate confidence in routing decision"""
        base_confidence = best_agent[1]
        
        # Adjust based on agent experience with task type
        agent = self.agents[best_agent[0]]
        performance = self.task_history.get_agent_performance(best_agent[0], task.task_type)
        experience_factor = performance.get("success_rate", 0.8)
        
        # Adjust based on current load
        load_factor = 1.0 - agent.current_load
        
        # Calculate final confidence
        confidence = base_confidence * 0.6 + experience_factor * 0.3 + load_factor * 0.1
        return min(confidence, 1.0)
    
    def _assess_risk(self, agent_id: str, task: Task) -> Dict:
        """Assess risk of task assignment"""
        agent = self.agents[agent_id]
        
        risks = []
        risk_level = "low"
        
        # High load risk
        if agent.current_load > 0.8:
            risks.append("high_agent_load")
            risk_level = "medium"
        
        # Skill mismatch risk
        skill_match = self.skill_matrix.get_skill_match(agent_id, task.required_skills)
        if skill_match < 0.7:
            risks.append("skill_mismatch")
            risk_level = "high"
        
        # Deadline pressure risk
        time_to_deadline = (task.deadline - datetime.now()).total_seconds() / 3600
        if time_to_deadline < task.estimated_duration * 1.2:
            risks.append("tight_deadline")
            risk_level = "medium"
        
        return {
            "risk_level": risk_level,
            "risk_factors": risks,
            "mitigation_strategies": self._generate_mitigation_strategies(risks)
        }
    
    def _estimate_completion_time(self, agent_id: str, task: Task) -> float:
        """Estimate task completion time"""
        base_estimate = task.estimated_duration
        
        # Adjust based on agent efficiency
        performance = self.task_history.get_agent_performance(agent_id, task.task_type)
        efficiency = performance.get("avg_efficiency", 1.0)
        
        # Adjust based on current load
        agent = self.agents[agent_id]
        load_factor = 1.0 + (agent.current_load * 0.5)  # Higher load = slower completion
        
        return base_estimate * load_factor / efficiency
    
    def _generate_reasoning(self, best_agent: Tuple[str, float], task: Task) -> str:
        """Generate human-readable reasoning for decision"""
        agent_id, score = best_agent
        agent = self.agents[agent_id]
        
        reasoning_parts = [
            f"Selected {agent.role} ({agent_id}) based on:",
            f"- Skill match score: {score:.2f}",
            f"- Current load: {agent.current_load:.2f}",
            f"- Specializations: {', '.join(agent.specializations)}"
        ]
        
        return " ".join(reasoning_parts)
    
    def _generate_mitigation_strategies(self, risks: List[str]) -> List[str]:
        """Generate risk mitigation strategies"""
        strategies = []
        
        if "high_agent_load" in risks:
            strategies.append("Consider redistributing current tasks")
        if "skill_mismatch" in risks:
            strategies.append("Provide additional training or pair with experienced agent")
        if "tight_deadline" in risks:
            strategies.append("Allocate additional resources or extend deadline")
        
        return strategies
    
    def _load_models(self):
        """Load pre-trained ML models"""
        try:
            # Load models from disk if available
            # This would be implemented with actual model persistence
            pass
        except:
            pass
    
    def update_task_completion(self, task_id: str, agent_id: str, success: bool, 
                             quality_score: float, actual_duration: float):
        """Update system with task completion data"""
        # This would extract task details from the original task
        # For now, using placeholder values
        self.task_history.record_task_completion(
            task_id, agent_id, "unknown", 2, "medium",
            2.0, actual_duration, quality_score, success
        )
        
        # Update agent load
        agent = self.agents.get(agent_id)
        if agent:
            # Decrease load after task completion
            new_load = max(0.0, agent.current_load - 0.1)
            self.availability_tracker.update_agent_load(agent_id, new_load)

# Example usage and testing
if __name__ == "__main__":
    # Initialize router
    router = IntelligentTaskRouter()
    
    # Register some example agents
    agents = [
        Agent(
            agent_id="agent-research-001",
            role="research_specialist",
            team="research_team",
            skills={"research": 0.9, "analysis": 0.8, "verification": 0.95},
            current_load=0.3,
            performance_history={"research": 0.92, "analysis": 0.88},
            availability=True,
            specializations=["truth_verification", "data_analysis"]
        ),
        Agent(
            agent_id="agent-development-001",
            role="development_specialist", 
            team="development_team",
            skills={"programming": 0.95, "architecture": 0.85, "testing": 0.8},
            current_load=0.6,
            performance_history={"development": 0.89, "architecture": 0.91},
            availability=True,
            specializations=["full_stack", "performance_optimization"]
        )
    ]
    
    for agent in agents:
        router.register_agent(agent)
    
    # Create example task
    task = Task(
        task_id="task-001",
        task_type="research",
        description="Analyze AI agent frameworks",
        priority=TaskPriority.HIGH,
        complexity=TaskComplexity.MODERATE,
        required_skills=["research", "analysis", "verification"],
        estimated_duration=3.0,
        deadline=datetime.now() + timedelta(hours=8),
        dependencies=[],
        context={}
    )
    
    # Route task
    decision = router.route_task(task)
    
    print(f"Routing Decision:")
    print(f"Primary Agent: {decision.primary_agent}")
    print(f"Backup Agents: {decision.backup_agents}")
    print(f"Confidence: {decision.confidence:.2f}")
    print(f"Reasoning: {decision.reasoning}")
    print(f"Estimated Completion: {decision.estimated_completion_time:.1f} hours")
    print(f"Risk Assessment: {decision.risk_assessment}")