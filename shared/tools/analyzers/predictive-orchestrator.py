"""
Predictive Orchestration System
Advanced predictive analytics and workload forecasting for Super Agent Team
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_absolute_error
import pickle
import logging
from concurrent.futures import ThreadPoolExecutor
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WorkloadType(Enum):
    RESEARCH = "research"
    DEVELOPMENT = "development"
    QUALITY = "quality"
    COMMUNICATION = "communication"
    ARCHITECTURE = "architecture"
    INNOVATION = "innovation"

class ScalingAction(Enum):
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    MAINTAIN = "maintain"
    REDISTRIBUTE = "redistribute"

@dataclass
class WorkloadPrediction:
    timestamp: datetime
    workload_type: WorkloadType
    predicted_load: float
    confidence: float
    contributing_factors: List[str]
    recommended_agents: int

@dataclass
class TaskPrediction:
    task_type: str
    estimated_start: datetime
    estimated_duration: float
    required_resources: Dict[str, Any]
    confidence: float
    triggers: List[str]

@dataclass
class ScalingPlan:
    action: ScalingAction
    target_agents: List[str]
    justification: str
    expected_impact: Dict[str, float]
    implementation_time: datetime
    rollback_plan: Optional[str]

@dataclass
class ResourceAllocation:
    agent_id: str
    allocated_capacity: float
    task_types: List[str]
    priority_level: int
    allocation_duration: timedelta

class PatternPredictor:
    """Predicts future task patterns based on historical data"""
    
    def __init__(self, db_path: str = "pattern_data.db"):
        self.db_path = db_path
        self.models = {}
        self.scalers = {}
        self.label_encoders = {}
        self.is_trained = False
        self._init_database()
        
    def _init_database(self):
        """Initialize pattern tracking database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id TEXT,
                step_sequence TEXT,
                timestamp TEXT,
                duration REAL,
                success BOOLEAN,
                context_factors TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS external_factors (
                timestamp TEXT PRIMARY KEY,
                day_of_week INTEGER,
                hour_of_day INTEGER,
                business_priority TEXT,
                system_load REAL,
                user_activity REAL,
                external_events TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_sequences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                current_task TEXT,
                next_task TEXT,
                transition_probability REAL,
                avg_transition_time REAL,
                last_updated TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def record_workflow_pattern(self, workflow_id: str, step_sequence: List[str],
                               duration: float, success: bool, context: Dict):
        """Record workflow pattern for learning"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO workflow_patterns 
            (workflow_id, step_sequence, timestamp, duration, success, context_factors)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (workflow_id, json.dumps(step_sequence), datetime.now().isoformat(),
              duration, success, json.dumps(context)))
        
        conn.commit()
        conn.close()
        
        # Update task transition patterns
        self._update_task_transitions(step_sequence)
    
    def record_external_factors(self, business_priority: str, system_load: float,
                               user_activity: float, external_events: List[str]):
        """Record external factors affecting patterns"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now()
        cursor.execute("""
            INSERT OR REPLACE INTO external_factors 
            (timestamp, day_of_week, hour_of_day, business_priority, 
             system_load, user_activity, external_events)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (now.isoformat(), now.weekday(), now.hour, business_priority,
              system_load, user_activity, json.dumps(external_events)))
        
        conn.commit()
        conn.close()
    
    def predict(self, current_workflow: List[str], historical_patterns: List[Dict],
                external_factors: Dict) -> List[TaskPrediction]:
        """Predict next tasks based on patterns"""
        if not self.is_trained:
            self._train_models()
        
        predictions = []
        
        # Get task transition probabilities
        current_task = current_workflow[-1] if current_workflow else ""
        possible_next_tasks = self._get_possible_next_tasks(current_task)
        
        for next_task, probability in possible_next_tasks.items():
            if probability > 0.3:  # Only consider likely transitions
                # Predict timing and resources
                timing_prediction = self._predict_task_timing(
                    current_task, next_task, external_factors
                )
                
                resource_prediction = self._predict_resource_requirements(
                    next_task, external_factors
                )
                
                # Identify triggers
                triggers = self._identify_triggers(current_workflow, next_task)
                
                predictions.append(TaskPrediction(
                    task_type=next_task,
                    estimated_start=timing_prediction["start_time"],
                    estimated_duration=timing_prediction["duration"],
                    required_resources=resource_prediction,
                    confidence=probability * timing_prediction["confidence"],
                    triggers=triggers
                ))
        
        return sorted(predictions, key=lambda x: x.confidence, reverse=True)
    
    def _update_task_transitions(self, step_sequence: List[str]):
        """Update task transition probabilities"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for i in range(len(step_sequence) - 1):
            current_task = step_sequence[i]
            next_task = step_sequence[i + 1]
            
            # Get current data
            cursor.execute("""
                SELECT transition_probability, avg_transition_time
                FROM task_sequences 
                WHERE current_task = ? AND next_task = ?
            """, (current_task, next_task))
            
            result = cursor.fetchone()
            
            if result:
                # Update existing transition
                new_prob = min(1.0, result[0] + 0.05)  # Increase probability
                cursor.execute("""
                    UPDATE task_sequences 
                    SET transition_probability = ?, last_updated = ?
                    WHERE current_task = ? AND next_task = ?
                """, (new_prob, datetime.now().isoformat(), current_task, next_task))
            else:
                # Create new transition
                cursor.execute("""
                    INSERT INTO task_sequences 
                    (current_task, next_task, transition_probability, 
                     avg_transition_time, last_updated)
                    VALUES (?, ?, ?, ?, ?)
                """, (current_task, next_task, 0.3, 1.0, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def _get_possible_next_tasks(self, current_task: str) -> Dict[str, float]:
        """Get possible next tasks with probabilities"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT next_task, transition_probability
            FROM task_sequences 
            WHERE current_task = ?
            ORDER BY transition_probability DESC
        """, (current_task,))
        
        results = cursor.fetchall()
        conn.close()
        
        return {row[0]: row[1] for row in results}
    
    def _predict_task_timing(self, current_task: str, next_task: str,
                           external_factors: Dict) -> Dict:
        """Predict when next task will start and how long it will take"""
        # This would use trained ML models
        # For now, using simple heuristics
        
        base_delay = 0.5  # Base delay in hours
        
        # Adjust based on system load
        system_load = external_factors.get("system_load", 0.5)
        load_factor = 1.0 + system_load
        
        # Adjust based on time of day
        hour = datetime.now().hour
        if 9 <= hour <= 17:  # Business hours
            time_factor = 1.0
        else:
            time_factor = 1.5
        
        estimated_delay = base_delay * load_factor * time_factor
        estimated_start = datetime.now() + timedelta(hours=estimated_delay)
        
        return {
            "start_time": estimated_start,
            "duration": 2.0,  # Default 2 hours
            "confidence": 0.7
        }
    
    def _predict_resource_requirements(self, task_type: str, 
                                     external_factors: Dict) -> Dict:
        """Predict resource requirements for task"""
        # Base resource requirements by task type
        base_requirements = {
            "research": {"agents": 1, "memory": "2GB", "cpu": "medium"},
            "development": {"agents": 2, "memory": "4GB", "cpu": "high"},
            "quality": {"agents": 1, "memory": "1GB", "cpu": "low"},
            "communication": {"agents": 1, "memory": "1GB", "cpu": "low"}
        }
        
        return base_requirements.get(task_type, {"agents": 1, "memory": "1GB", "cpu": "medium"})
    
    def _identify_triggers(self, current_workflow: List[str], next_task: str) -> List[str]:
        """Identify what triggers the next task"""
        triggers = []
        
        if current_workflow:
            last_task = current_workflow[-1]
            if "research" in last_task and "development" in next_task:
                triggers.append("research_completion")
            elif "development" in last_task and "quality" in next_task:
                triggers.append("development_completion")
        
        return triggers
    
    def _train_models(self):
        """Train ML models for pattern prediction"""
        # This would implement actual ML training
        # For now, marking as trained
        self.is_trained = True
        logger.info("Pattern prediction models trained")

class WorkloadForecaster:
    """Forecasts future workload patterns"""
    
    def __init__(self, db_path: str = "workload_data.db"):
        self.db_path = db_path
        self.forecast_models = {}
        self.feature_scalers = {}
        self._init_database()
        
    def _init_database(self):
        """Initialize workload tracking database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workload_history (
                timestamp TEXT,
                workload_type TEXT,
                active_agents INTEGER,
                task_queue_size INTEGER,
                avg_response_time REAL,
                success_rate REAL,
                system_utilization REAL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS capacity_events (
                timestamp TEXT,
                event_type TEXT,
                description TEXT,
                impact_factor REAL,
                duration_hours REAL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def record_workload_metrics(self, workload_type: WorkloadType, active_agents: int,
                               queue_size: int, response_time: float, success_rate: float,
                               utilization: float):
        """Record current workload metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO workload_history 
            (timestamp, workload_type, active_agents, task_queue_size, 
             avg_response_time, success_rate, system_utilization)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (datetime.now().isoformat(), workload_type.value, active_agents,
              queue_size, response_time, success_rate, utilization))
        
        conn.commit()
        conn.close()
    
    def forecast(self, time_horizon: str = "1h") -> Dict[WorkloadType, WorkloadPrediction]:
        """Forecast workload for specified time horizon"""
        horizon_hours = self._parse_time_horizon(time_horizon)
        target_time = datetime.now() + timedelta(hours=horizon_hours)
        
        forecasts = {}
        
        for workload_type in WorkloadType:
            # Get historical data
            historical_data = self._get_historical_data(workload_type, days=30)
            
            if len(historical_data) > 10:  # Need sufficient data
                prediction = self._generate_forecast(
                    workload_type, historical_data, target_time
                )
                forecasts[workload_type] = prediction
            else:
                # Use fallback prediction for insufficient data
                forecasts[workload_type] = self._fallback_forecast(
                    workload_type, target_time
                )
        
        return forecasts
    
    def _parse_time_horizon(self, horizon: str) -> float:
        """Parse time horizon string to hours"""
        if horizon.endswith('h'):
            return float(horizon[:-1])
        elif horizon.endswith('d'):
            return float(horizon[:-1]) * 24
        elif horizon.endswith('w'):
            return float(horizon[:-1]) * 24 * 7
        else:
            return 1.0  # Default 1 hour
    
    def _get_historical_data(self, workload_type: WorkloadType, days: int) -> pd.DataFrame:
        """Get historical workload data"""
        conn = sqlite3.connect(self.db_path)
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        query = """
            SELECT timestamp, active_agents, task_queue_size, avg_response_time,
                   success_rate, system_utilization
            FROM workload_history 
            WHERE workload_type = ? AND timestamp > ?
            ORDER BY timestamp
        """
        
        df = pd.read_sql_query(query, conn, params=(workload_type.value, cutoff_date))
        conn.close()
        
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp')
        
        return df
    
    def _generate_forecast(self, workload_type: WorkloadType, 
                          historical_data: pd.DataFrame, 
                          target_time: datetime) -> WorkloadPrediction:
        """Generate forecast using ML models"""
        
        # Prepare features
        features = self._extract_time_features(historical_data)
        
        # Simple moving average for now (would use more sophisticated models)
        recent_load = historical_data['system_utilization'].tail(10).mean()
        recent_agents = historical_data['active_agents'].tail(10).mean()
        
        # Adjust for time of day patterns
        hour_factor = self._get_hour_factor(target_time.hour)
        day_factor = self._get_day_factor(target_time.weekday())
        
        predicted_load = recent_load * hour_factor * day_factor
        recommended_agents = max(1, int(recent_agents * (predicted_load / recent_load)))
        
        # Identify contributing factors
        factors = self._identify_factors(historical_data, predicted_load)
        
        return WorkloadPrediction(
            timestamp=target_time,
            workload_type=workload_type,
            predicted_load=predicted_load,
            confidence=0.75,
            contributing_factors=factors,
            recommended_agents=recommended_agents
        )
    
    def _fallback_forecast(self, workload_type: WorkloadType, 
                          target_time: datetime) -> WorkloadPrediction:
        """Fallback forecast when insufficient historical data"""
        # Default predictions based on workload type
        defaults = {
            WorkloadType.RESEARCH: {"load": 0.3, "agents": 1},
            WorkloadType.DEVELOPMENT: {"load": 0.6, "agents": 2},
            WorkloadType.QUALITY: {"load": 0.4, "agents": 1},
            WorkloadType.COMMUNICATION: {"load": 0.2, "agents": 1},
            WorkloadType.ARCHITECTURE: {"load": 0.3, "agents": 1},
            WorkloadType.INNOVATION: {"load": 0.2, "agents": 1}
        }
        
        default = defaults[workload_type]
        
        return WorkloadPrediction(
            timestamp=target_time,
            workload_type=workload_type,
            predicted_load=default["load"],
            confidence=0.5,
            contributing_factors=["insufficient_historical_data"],
            recommended_agents=default["agents"]
        )
    
    def _extract_time_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Extract time-based features for forecasting"""
        features = pd.DataFrame(index=data.index)
        features['hour'] = data.index.hour
        features['day_of_week'] = data.index.dayofweek
        features['is_weekend'] = features['day_of_week'].isin([5, 6])
        features['is_business_hours'] = features['hour'].between(9, 17)
        
        return features
    
    def _get_hour_factor(self, hour: int) -> float:
        """Get load factor based on hour of day"""
        if 9 <= hour <= 17:  # Business hours
            return 1.2
        elif 6 <= hour <= 9 or 17 <= hour <= 22:  # Extended hours
            return 0.8
        else:  # Night hours
            return 0.3
    
    def _get_day_factor(self, weekday: int) -> float:
        """Get load factor based on day of week"""
        if weekday < 5:  # Weekdays
            return 1.0
        else:  # Weekends
            return 0.4
    
    def _identify_factors(self, data: pd.DataFrame, predicted_load: float) -> List[str]:
        """Identify factors contributing to predicted load"""
        factors = []
        
        if predicted_load > 0.8:
            factors.append("high_demand_period")
        elif predicted_load < 0.3:
            factors.append("low_demand_period")
        
        # Analyze recent trends
        if len(data) >= 5:
            recent_trend = data['system_utilization'].tail(5).pct_change().mean()
            if recent_trend > 0.1:
                factors.append("increasing_trend")
            elif recent_trend < -0.1:
                factors.append("decreasing_trend")
        
        return factors

class ResourcePlanner:
    """Plans resource allocation and scaling decisions"""
    
    def __init__(self):
        self.current_allocations = {}
        self.scaling_history = []
        self.performance_thresholds = {
            "high_load": 0.85,
            "low_load": 0.3,
            "response_time_max": 5.0,  # seconds
            "success_rate_min": 0.95
        }
    
    def pre_allocate(self, task_type: str, estimated_start: datetime,
                    required_resources: Dict):
        """Pre-allocate resources for predicted tasks"""
        allocation_id = f"prealloc_{len(self.current_allocations)}"
        
        allocation = ResourceAllocation(
            agent_id=f"reserved_for_{task_type}",
            allocated_capacity=required_resources.get("agents", 1) * 0.1,  # 10% capacity
            task_types=[task_type],
            priority_level=2,  # Medium priority for pre-allocation
            allocation_duration=timedelta(hours=2)
        )
        
        self.current_allocations[allocation_id] = allocation
        
        logger.info(f"Pre-allocated resources for {task_type} starting at {estimated_start}")
        
        return allocation_id
    
    def create_scaling_plan(self, current_agents: List[str], 
                           forecasted_load: Dict[WorkloadType, WorkloadPrediction],
                           sla_requirements: Dict) -> List[ScalingPlan]:
        """Create scaling plan based on forecasted load"""
        scaling_plans = []
        
        for workload_type, prediction in forecasted_load.items():
            current_count = len([a for a in current_agents if workload_type.value in a])
            recommended_count = prediction.recommended_agents
            
            if recommended_count > current_count:
                # Scale up needed
                plan = ScalingPlan(
                    action=ScalingAction.SCALE_UP,
                    target_agents=[f"agent-{workload_type.value}-{i+current_count+1:03d}" 
                                 for i in range(recommended_count - current_count)],
                    justification=f"Predicted load increase to {prediction.predicted_load:.2f}",
                    expected_impact={
                        "load_reduction": 0.2,
                        "response_time_improvement": 0.3,
                        "capacity_increase": (recommended_count - current_count) / current_count if current_count > 0 else 1.0
                    },
                    implementation_time=prediction.timestamp - timedelta(minutes=15),
                    rollback_plan=f"Scale down to {current_count} agents if load doesn't materialize"
                )
                scaling_plans.append(plan)
                
            elif recommended_count < current_count and current_count > 1:
                # Scale down possible
                plan = ScalingPlan(
                    action=ScalingAction.SCALE_DOWN,
                    target_agents=[f"agent-{workload_type.value}-{current_count:03d}"],
                    justification=f"Predicted load decrease to {prediction.predicted_load:.2f}",
                    expected_impact={
                        "cost_reduction": 0.15,
                        "resource_optimization": 0.1
                    },
                    implementation_time=prediction.timestamp,
                    rollback_plan=f"Scale back up if performance degrades"
                )
                scaling_plans.append(plan)
        
        return self._prioritize_scaling_plans(scaling_plans)
    
    def _prioritize_scaling_plans(self, plans: List[ScalingPlan]) -> List[ScalingPlan]:
        """Prioritize scaling plans by impact and urgency"""
        def priority_score(plan):
            score = 0
            if plan.action == ScalingAction.SCALE_UP:
                score += 10  # Higher priority for scaling up
            
            # Add impact scores
            for impact_type, value in plan.expected_impact.items():
                if "improvement" in impact_type or "increase" in impact_type:
                    score += value * 5
            
            return score
        
        return sorted(plans, key=priority_score, reverse=True)

class PredictiveOrchestrator:
    """Main predictive orchestration system"""
    
    def __init__(self):
        self.pattern_predictor = PatternPredictor()
        self.workload_forecaster = WorkloadForecaster()
        self.resource_planner = ResourcePlanner()
        self.prediction_cache = {}
        self.lock = threading.Lock()
        
        # Start background prediction updates
        self._start_prediction_loop()
    
    def predict_next_tasks(self, current_context: Dict) -> List[TaskPrediction]:
        """Predict what tasks will be needed next"""
        cache_key = f"tasks_{datetime.now().strftime('%Y%m%d_%H')}"
        
        with self.lock:
            if cache_key in self.prediction_cache:
                return self.prediction_cache[cache_key]
        
        # Get predictions
        predictions = self.pattern_predictor.predict(
            current_workflow=current_context.get("workflow", []),
            historical_patterns=self._get_historical_patterns(),
            external_factors=self._get_external_factors()
        )
        
        # Pre-allocate resources for high-confidence predictions
        for prediction in predictions:
            if prediction.confidence > 0.8:
                self.resource_planner.pre_allocate(
                    task_type=prediction.task_type,
                    estimated_start=prediction.estimated_start,
                    required_resources=prediction.required_resources
                )
        
        # Cache results
        with self.lock:
            self.prediction_cache[cache_key] = predictions
        
        return predictions
    
    def auto_scale_agents(self, time_horizon: str = "1h") -> List[ScalingPlan]:
        """Automatically scale agent pool based on predictions"""
        # Get workload forecast
        forecast = self.workload_forecaster.forecast(time_horizon)
        
        # Get current agents (this would come from the agent registry)
        current_agents = self._get_active_agents()
        
        # Get SLA requirements
        sla_requirements = self._get_sla_requirements()
        
        # Create scaling plan
        scaling_plan = self.resource_planner.create_scaling_plan(
            current_agents=current_agents,
            forecasted_load=forecast,
            sla_requirements=sla_requirements
        )
        
        return scaling_plan
    
    def execute_scaling_plan(self, scaling_plan: List[ScalingPlan]) -> Dict[str, bool]:
        """Execute scaling plan with safety checks"""
        results = {}
        
        for plan in scaling_plan:
            try:
                # Safety checks
                if self._validate_scaling_plan(plan):
                    success = self._implement_scaling_action(plan)
                    results[f"{plan.action.value}_{len(plan.target_agents)}"] = success
                    
                    if success:
                        logger.info(f"Successfully executed scaling plan: {plan.action.value}")
                    else:
                        logger.error(f"Failed to execute scaling plan: {plan.action.value}")
                else:
                    logger.warning(f"Scaling plan failed validation: {plan.action.value}")
                    results[f"{plan.action.value}_{len(plan.target_agents)}"] = False
                    
            except Exception as e:
                logger.error(f"Error executing scaling plan: {e}")
                results[f"{plan.action.value}_{len(plan.target_agents)}"] = False
        
        return results
    
    def _get_historical_patterns(self) -> List[Dict]:
        """Get historical workflow patterns"""
        # This would query the pattern database
        return []
    
    def _get_external_factors(self) -> Dict:
        """Get current external factors affecting workload"""
        now = datetime.now()
        return {
            "time_of_day": now.hour,
            "day_of_week": now.weekday(),
            "system_load": 0.5,  # Would get from monitoring
            "business_priority": "normal"
        }
    
    def _get_active_agents(self) -> List[str]:
        """Get list of currently active agents"""
        # This would come from the agent registry
        return [
            "agent-orchestrator-001",
            "agent-research-001", 
            "agent-development-001",
            "agent-quality-001",
            "agent-communication-001"
        ]
    
    def _get_sla_requirements(self) -> Dict:
        """Get SLA requirements for the system"""
        return {
            "max_response_time": 30,  # seconds
            "min_success_rate": 0.98,
            "max_queue_size": 10
        }
    
    def _validate_scaling_plan(self, plan: ScalingPlan) -> bool:
        """Validate scaling plan before execution"""
        # Check if timing is appropriate
        if plan.implementation_time < datetime.now():
            return False
        
        # Check if action is reasonable
        if plan.action == ScalingAction.SCALE_DOWN and len(plan.target_agents) == 0:
            return False
        
        # Additional safety checks would go here
        return True
    
    def _implement_scaling_action(self, plan: ScalingPlan) -> bool:
        """Implement the actual scaling action"""
        # This would interface with the agent management system
        logger.info(f"Implementing scaling action: {plan.action.value}")
        logger.info(f"Target agents: {plan.target_agents}")
        logger.info(f"Justification: {plan.justification}")
        
        # For now, just simulate success
        return True
    
    def _start_prediction_loop(self):
        """Start background thread for continuous predictions"""
        def prediction_loop():
            while True:
                try:
                    # Update predictions every 15 minutes
                    self.predict_next_tasks({"workflow": []})
                    threading.Event().wait(900)  # 15 minutes
                except Exception as e:
                    logger.error(f"Error in prediction loop: {e}")
                    threading.Event().wait(300)  # 5 minutes on error
        
        thread = threading.Thread(target=prediction_loop, daemon=True)
        thread.start()
    
    def get_prediction_summary(self) -> Dict:
        """Get summary of current predictions"""
        # Get latest predictions
        predictions = self.predict_next_tasks({"workflow": []})
        forecast = self.workload_forecaster.forecast("1h")
        scaling_plans = self.auto_scale_agents("1h")
        
        return {
            "task_predictions": [asdict(p) for p in predictions[:5]],
            "workload_forecast": {k.value: asdict(v) for k, v in forecast.items()},
            "scaling_recommendations": [asdict(p) for p in scaling_plans],
            "last_updated": datetime.now().isoformat(),
            "prediction_confidence": sum(p.confidence for p in predictions) / len(predictions) if predictions else 0
        }

# Example usage
if __name__ == "__main__":
    # Initialize predictive orchestrator
    orchestrator = PredictiveOrchestrator()
    
    # Record some sample workload data
    orchestrator.workload_forecaster.record_workload_metrics(
        WorkloadType.DEVELOPMENT, 2, 5, 2.5, 0.95, 0.7
    )
    
    # Get predictions
    context = {
        "workflow": ["research", "analysis"],
        "current_time": datetime.now()
    }
    
    task_predictions = orchestrator.predict_next_tasks(context)
    print("Task Predictions:")
    for pred in task_predictions:
        print(f"  {pred.task_type}: {pred.confidence:.2f} confidence")
    
    # Get scaling recommendations
    scaling_plans = orchestrator.auto_scale_agents("2h")
    print(f"\nScaling Recommendations: {len(scaling_plans)} plans")
    for plan in scaling_plans:
        print(f"  {plan.action.value}: {plan.justification}")
    
    # Get summary
    summary = orchestrator.get_prediction_summary()
    print(f"\nPrediction Summary:")
    print(f"  Predictions: {len(summary['task_predictions'])}")
    print(f"  Workload Types: {len(summary['workload_forecast'])}")
    print(f"  Overall Confidence: {summary['prediction_confidence']:.2f}")