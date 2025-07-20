"""
Time-Travel Debugging System
Advanced debugging by replaying exact conditions for Super Agent Team
"""

import json
import pickle
import gzip
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import hashlib
import copy
import logging
from collections import deque, OrderedDict
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventType(Enum):
    AGENT_STATE_CHANGE = "agent_state_change"
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    DECISION_MADE = "decision_made"
    ERROR_OCCURRED = "error_occurred"
    EXTERNAL_CALL = "external_call"
    SYSTEM_EVENT = "system_event"
    PERFORMANCE_METRIC = "performance_metric"

class ReplaySpeed(Enum):
    ULTRA_SLOW = 0.01
    SLOW = 0.1
    NORMAL = 1.0
    FAST = 2.0
    ULTRA_FAST = 10.0

@dataclass
class StateSnapshot:
    timestamp: datetime
    agent_id: str
    state_data: Dict[str, Any]
    state_hash: str
    metadata: Dict[str, Any]

@dataclass
class SystemEvent:
    event_id: str
    timestamp: datetime
    event_type: EventType
    source_agent: str
    target_agent: Optional[str]
    event_data: Dict[str, Any]
    context: Dict[str, Any]
    sequence_number: int

@dataclass
class DebugBreakpoint:
    breakpoint_id: str
    condition: str
    agent_filter: Optional[str]
    event_type_filter: Optional[EventType]
    active: bool
    hit_count: int
    created_at: datetime

@dataclass
class ReplaySession:
    session_id: str
    start_time: datetime
    end_time: datetime
    focus_agent: Optional[str]
    replay_speed: ReplaySpeed
    breakpoints: List[DebugBreakpoint]
    status: str
    current_position: datetime
    events_processed: int
    total_events: int

class StateRecorder:
    """Records all agent state changes with high precision"""
    
    def __init__(self, db_path: str = "state_records.db", max_memory_snapshots: int = 10000):
        self.db_path = db_path
        self.max_memory_snapshots = max_memory_snapshots
        self.memory_snapshots = OrderedDict()
        self.recording_active = True
        self.compression_enabled = True
        self.state_lock = threading.RLock()
        self._init_database()
        
    def _init_database(self):
        """Initialize state recording database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_states (
                timestamp TEXT,
                agent_id TEXT,
                state_hash TEXT,
                state_data BLOB,
                metadata TEXT,
                PRIMARY KEY (timestamp, agent_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS state_deltas (
                timestamp TEXT,
                agent_id TEXT,
                previous_hash TEXT,
                current_hash TEXT,
                delta_data BLOB,
                change_description TEXT
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_states_timestamp 
            ON agent_states(timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_states_agent_id 
            ON agent_states(agent_id)
        """)
        
        conn.commit()
        conn.close()
    
    def capture_agent_state(self, agent_id: str, state_data: Dict[str, Any], 
                           metadata: Optional[Dict[str, Any]] = None) -> StateSnapshot:
        """Capture complete state of an agent"""
        if not self.recording_active:
            return None
        
        timestamp = datetime.now()
        metadata = metadata or {}
        
        # Create state hash for change detection
        state_json = json.dumps(state_data, sort_keys=True, default=str)
        state_hash = hashlib.sha256(state_json.encode()).hexdigest()
        
        snapshot = StateSnapshot(
            timestamp=timestamp,
            agent_id=agent_id,
            state_data=state_data,
            state_hash=state_hash,
            metadata=metadata
        )
        
        with self.state_lock:
            # Store in memory for quick access
            memory_key = f"{agent_id}_{timestamp.isoformat()}"
            self.memory_snapshots[memory_key] = snapshot
            
            # Maintain memory limit
            if len(self.memory_snapshots) > self.max_memory_snapshots:
                self.memory_snapshots.popitem(last=False)
            
            # Store in database asynchronously
            self._store_state_async(snapshot)
        
        return snapshot
    
    def capture_all_agents(self, agent_states: Dict[str, Dict[str, Any]]) -> Dict[str, StateSnapshot]:
        """Capture states of all agents simultaneously"""
        snapshots = {}
        timestamp = datetime.now()
        
        for agent_id, state_data in agent_states.items():
            snapshot = StateSnapshot(
                timestamp=timestamp,
                agent_id=agent_id,
                state_data=state_data,
                state_hash=hashlib.sha256(
                    json.dumps(state_data, sort_keys=True, default=str).encode()
                ).hexdigest(),
                metadata={"batch_capture": True}
            )
            snapshots[agent_id] = snapshot
            
            # Store in memory
            memory_key = f"{agent_id}_{timestamp.isoformat()}"
            self.memory_snapshots[memory_key] = snapshot
        
        # Store all in database
        self._store_batch_states_async(list(snapshots.values()))
        
        return snapshots
    
    def get_state_at_time(self, agent_id: str, timestamp: datetime) -> Optional[StateSnapshot]:
        """Get agent state at specific time"""
        # First check memory
        with self.state_lock:
            for key, snapshot in reversed(self.memory_snapshots.items()):
                if (snapshot.agent_id == agent_id and 
                    snapshot.timestamp <= timestamp):
                    return snapshot
        
        # Query database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT timestamp, state_hash, state_data, metadata
            FROM agent_states
            WHERE agent_id = ? AND timestamp <= ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (agent_id, timestamp.isoformat()))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            state_data = self._decompress_data(result[2]) if self.compression_enabled else pickle.loads(result[2])
            metadata = json.loads(result[3]) if result[3] else {}
            
            return StateSnapshot(
                timestamp=datetime.fromisoformat(result[0]),
                agent_id=agent_id,
                state_data=state_data,
                state_hash=result[1],
                metadata=metadata
            )
        
        return None
    
    def get_state_changes(self, agent_id: str, start_time: datetime, 
                         end_time: datetime) -> List[StateSnapshot]:
        """Get all state changes for agent within time range"""
        changes = []
        
        # Check memory first
        with self.state_lock:
            for snapshot in self.memory_snapshots.values():
                if (snapshot.agent_id == agent_id and 
                    start_time <= snapshot.timestamp <= end_time):
                    changes.append(snapshot)
        
        # Query database for additional data
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT timestamp, state_hash, state_data, metadata
            FROM agent_states
            WHERE agent_id = ? AND timestamp BETWEEN ? AND ?
            ORDER BY timestamp
        """, (agent_id, start_time.isoformat(), end_time.isoformat()))
        
        for row in cursor.fetchall():
            # Avoid duplicates from memory
            timestamp = datetime.fromisoformat(row[0])
            if not any(c.timestamp == timestamp for c in changes):
                state_data = self._decompress_data(row[2]) if self.compression_enabled else pickle.loads(row[2])
                metadata = json.loads(row[3]) if row[3] else {}
                
                changes.append(StateSnapshot(
                    timestamp=timestamp,
                    agent_id=agent_id,
                    state_data=state_data,
                    state_hash=row[1],
                    metadata=metadata
                ))
        
        conn.close()
        
        return sorted(changes, key=lambda x: x.timestamp)
    
    def _store_state_async(self, snapshot: StateSnapshot):
        """Store state snapshot asynchronously"""
        def store():
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Compress state data if enabled
                state_blob = self._compress_data(snapshot.state_data) if self.compression_enabled else pickle.dumps(snapshot.state_data)
                
                cursor.execute("""
                    INSERT OR REPLACE INTO agent_states
                    (timestamp, agent_id, state_hash, state_data, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (snapshot.timestamp.isoformat(), snapshot.agent_id, 
                      snapshot.state_hash, state_blob, json.dumps(snapshot.metadata)))
                
                conn.commit()
                conn.close()
            except Exception as e:
                logger.error(f"Error storing state: {e}")
        
        # Run in background thread
        threading.Thread(target=store, daemon=True).start()
    
    def _store_batch_states_async(self, snapshots: List[StateSnapshot]):
        """Store multiple state snapshots asynchronously"""
        def store_batch():
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                data_to_insert = []
                for snapshot in snapshots:
                    state_blob = self._compress_data(snapshot.state_data) if self.compression_enabled else pickle.dumps(snapshot.state_data)
                    data_to_insert.append((
                        snapshot.timestamp.isoformat(),
                        snapshot.agent_id,
                        snapshot.state_hash,
                        state_blob,
                        json.dumps(snapshot.metadata)
                    ))
                
                cursor.executemany("""
                    INSERT OR REPLACE INTO agent_states
                    (timestamp, agent_id, state_hash, state_data, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, data_to_insert)
                
                conn.commit()
                conn.close()
            except Exception as e:
                logger.error(f"Error storing batch states: {e}")
        
        threading.Thread(target=store_batch, daemon=True).start()
    
    def _compress_data(self, data: Any) -> bytes:
        """Compress data using gzip"""
        return gzip.compress(pickle.dumps(data))
    
    def _decompress_data(self, compressed_data: bytes) -> Any:
        """Decompress data using gzip"""
        return pickle.loads(gzip.decompress(compressed_data))

class EventLog:
    """Comprehensive event logging system"""
    
    def __init__(self, db_path: str = "event_log.db", max_memory_events: int = 50000):
        self.db_path = db_path
        self.max_memory_events = max_memory_events
        self.memory_events = deque(maxlen=max_memory_events)
        self.sequence_counter = 0
        self.log_lock = threading.RLock()
        self._init_database()
    
    def _init_database(self):
        """Initialize event logging database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_events (
                event_id TEXT PRIMARY KEY,
                timestamp TEXT,
                event_type TEXT,
                source_agent TEXT,
                target_agent TEXT,
                event_data BLOB,
                context BLOB,
                sequence_number INTEGER
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_timestamp 
            ON system_events(timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_type 
            ON system_events(event_type)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_source 
            ON system_events(source_agent)
        """)
        
        conn.commit()
        conn.close()
    
    def log_event(self, event_type: EventType, source_agent: str, 
                  event_data: Dict[str, Any], target_agent: Optional[str] = None,
                  context: Optional[Dict[str, Any]] = None) -> SystemEvent:
        """Log a system event"""
        timestamp = datetime.now()
        context = context or {}
        
        with self.log_lock:
            self.sequence_counter += 1
            event_id = f"event_{self.sequence_counter}_{int(timestamp.timestamp() * 1000000)}"
        
        event = SystemEvent(
            event_id=event_id,
            timestamp=timestamp,
            event_type=event_type,
            source_agent=source_agent,
            target_agent=target_agent,
            event_data=event_data,
            context=context,
            sequence_number=self.sequence_counter
        )
        
        # Store in memory
        self.memory_events.append(event)
        
        # Store in database asynchronously
        self._store_event_async(event)
        
        return event
    
    def capture_all_messages(self, start_time: datetime, end_time: datetime) -> List[SystemEvent]:
        """Capture all message events in time range"""
        message_events = []
        
        # Check memory first
        for event in self.memory_events:
            if (event.event_type in [EventType.MESSAGE_SENT, EventType.MESSAGE_RECEIVED] and
                start_time <= event.timestamp <= end_time):
                message_events.append(event)
        
        # Query database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT event_id, timestamp, event_type, source_agent, target_agent, 
                   event_data, context, sequence_number
            FROM system_events
            WHERE event_type IN ('message_sent', 'message_received')
            AND timestamp BETWEEN ? AND ?
            ORDER BY timestamp
        """, (start_time.isoformat(), end_time.isoformat()))
        
        for row in cursor.fetchall():
            # Avoid duplicates from memory
            if not any(e.event_id == row[0] for e in message_events):
                event_data = pickle.loads(row[5])
                context = pickle.loads(row[6])
                
                message_events.append(SystemEvent(
                    event_id=row[0],
                    timestamp=datetime.fromisoformat(row[1]),
                    event_type=EventType(row[2]),
                    source_agent=row[3],
                    target_agent=row[4],
                    event_data=event_data,
                    context=context,
                    sequence_number=row[7]
                ))
        
        conn.close()
        
        return sorted(message_events, key=lambda x: x.timestamp)
    
    def capture_all_decisions(self, start_time: datetime, end_time: datetime) -> List[SystemEvent]:
        """Capture all decision events in time range"""
        return self._capture_events_by_type(EventType.DECISION_MADE, start_time, end_time)
    
    def capture_external_calls(self, start_time: datetime, end_time: datetime) -> List[SystemEvent]:
        """Capture all external call events in time range"""
        return self._capture_events_by_type(EventType.EXTERNAL_CALL, start_time, end_time)
    
    def _capture_events_by_type(self, event_type: EventType, 
                               start_time: datetime, end_time: datetime) -> List[SystemEvent]:
        """Capture events of specific type in time range"""
        events = []
        
        # Check memory first
        for event in self.memory_events:
            if (event.event_type == event_type and
                start_time <= event.timestamp <= end_time):
                events.append(event)
        
        # Query database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT event_id, timestamp, source_agent, target_agent, 
                   event_data, context, sequence_number
            FROM system_events
            WHERE event_type = ? AND timestamp BETWEEN ? AND ?
            ORDER BY timestamp
        """, (event_type.value, start_time.isoformat(), end_time.isoformat()))
        
        for row in cursor.fetchall():
            # Avoid duplicates from memory
            if not any(e.event_id == row[0] for e in events):
                event_data = pickle.loads(row[4])
                context = pickle.loads(row[5])
                
                events.append(SystemEvent(
                    event_id=row[0],
                    timestamp=datetime.fromisoformat(row[1]),
                    event_type=event_type,
                    source_agent=row[2],
                    target_agent=row[3],
                    event_data=event_data,
                    context=context,
                    sequence_number=row[6]
                ))
        
        conn.close()
        
        return sorted(events, key=lambda x: x.timestamp)
    
    def _store_event_async(self, event: SystemEvent):
        """Store event asynchronously"""
        def store():
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO system_events
                    (event_id, timestamp, event_type, source_agent, target_agent,
                     event_data, context, sequence_number)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (event.event_id, event.timestamp.isoformat(), event.event_type.value,
                      event.source_agent, event.target_agent, pickle.dumps(event.event_data),
                      pickle.dumps(event.context), event.sequence_number))
                
                conn.commit()
                conn.close()
            except Exception as e:
                logger.error(f"Error storing event: {e}")
        
        threading.Thread(target=store, daemon=True).start()

class ReplayEngine:
    """Engine for replaying recorded scenarios"""
    
    def __init__(self, state_recorder: StateRecorder, event_log: EventLog):
        self.state_recorder = state_recorder
        self.event_log = event_log
        self.active_replays = {}
        self.replay_lock = threading.Lock()
    
    def replay(self, scenario: Dict[str, Any], speed: ReplaySpeed = ReplaySpeed.SLOW,
               breakpoints: Optional[List[DebugBreakpoint]] = None,
               focus_agent: Optional[str] = None) -> ReplaySession:
        """Replay exact scenario for debugging"""
        
        session_id = f"replay_{int(time.time() * 1000)}"
        start_time = datetime.fromisoformat(scenario["start_time"])
        end_time = datetime.fromisoformat(scenario["end_time"])
        
        breakpoints = breakpoints or []
        
        session = ReplaySession(
            session_id=session_id,
            start_time=start_time,
            end_time=end_time,
            focus_agent=focus_agent,
            replay_speed=speed,
            breakpoints=breakpoints,
            status="initializing",
            current_position=start_time,
            events_processed=0,
            total_events=0
        )
        
        with self.replay_lock:
            self.active_replays[session_id] = session
        
        # Start replay in background thread
        replay_thread = threading.Thread(
            target=self._execute_replay,
            args=(session, scenario),
            daemon=True
        )
        replay_thread.start()
        
        return session
    
    def _execute_replay(self, session: ReplaySession, scenario: Dict[str, Any]):
        """Execute the replay scenario"""
        try:
            session.status = "loading_data"
            
            # Load all events in time range
            all_events = self._load_scenario_events(session.start_time, session.end_time)
            session.total_events = len(all_events)
            
            # Filter events if focus agent specified
            if session.focus_agent:
                all_events = [e for e in all_events if 
                             e.source_agent == session.focus_agent or 
                             e.target_agent == session.focus_agent]
            
            session.status = "replaying"
            
            # Replay events
            for event in all_events:
                # Check for breakpoints
                if self._check_breakpoints(event, session.breakpoints):
                    session.status = "breakpoint_hit"
                    logger.info(f"Breakpoint hit during replay: {event.event_id}")
                    # Wait for user interaction or timeout
                    self._wait_for_breakpoint_resume(session)
                
                # Simulate event processing
                self._simulate_event_processing(event, session)
                
                # Update session progress
                session.current_position = event.timestamp
                session.events_processed += 1
                
                # Apply replay speed
                if session.replay_speed != ReplaySpeed.ULTRA_FAST:
                    time.sleep(0.1 / session.replay_speed.value)
                
                # Check if replay should be paused or stopped
                if session.status in ["paused", "stopped"]:
                    break
            
            session.status = "completed"
            
        except Exception as e:
            logger.error(f"Error during replay: {e}")
            session.status = "error"
        finally:
            # Clean up
            with self.replay_lock:
                if session.session_id in self.active_replays:
                    self.active_replays[session.session_id] = session
    
    def _load_scenario_events(self, start_time: datetime, end_time: datetime) -> List[SystemEvent]:
        """Load all events for scenario time range"""
        events = []
        
        # Load different event types
        messages = self.event_log.capture_all_messages(start_time, end_time)
        decisions = self.event_log.capture_all_decisions(start_time, end_time)
        external_calls = self.event_log.capture_external_calls(start_time, end_time)
        
        events.extend(messages)
        events.extend(decisions)
        events.extend(external_calls)
        
        # Sort by timestamp
        return sorted(events, key=lambda x: x.timestamp)
    
    def _check_breakpoints(self, event: SystemEvent, breakpoints: List[DebugBreakpoint]) -> bool:
        """Check if event triggers any breakpoints"""
        for breakpoint in breakpoints:
            if not breakpoint.active:
                continue
            
            # Check event type filter
            if (breakpoint.event_type_filter and 
                event.event_type != breakpoint.event_type_filter):
                continue
            
            # Check agent filter
            if (breakpoint.agent_filter and 
                event.source_agent != breakpoint.agent_filter and
                event.target_agent != breakpoint.agent_filter):
                continue
            
            # Check condition (simplified condition checking)
            if self._evaluate_breakpoint_condition(event, breakpoint.condition):
                breakpoint.hit_count += 1
                return True
        
        return False
    
    def _evaluate_breakpoint_condition(self, event: SystemEvent, condition: str) -> bool:
        """Evaluate breakpoint condition"""
        # Simplified condition evaluation
        if "error" in condition.lower():
            return event.event_type == EventType.ERROR_OCCURRED
        elif "message" in condition.lower():
            return event.event_type in [EventType.MESSAGE_SENT, EventType.MESSAGE_RECEIVED]
        elif "decision" in condition.lower():
            return event.event_type == EventType.DECISION_MADE
        
        return False
    
    def _wait_for_breakpoint_resume(self, session: ReplaySession, timeout: int = 300):
        """Wait for breakpoint to be resumed or timeout"""
        start_wait = time.time()
        while session.status == "breakpoint_hit" and (time.time() - start_wait) < timeout:
            time.sleep(1)
        
        if session.status == "breakpoint_hit":
            session.status = "replaying"  # Auto-resume after timeout
    
    def _simulate_event_processing(self, event: SystemEvent, session: ReplaySession):
        """Simulate processing of event during replay"""
        # This would reconstruct the system state at the time of the event
        # For now, just log the event processing
        logger.debug(f"Replaying event: {event.event_type.value} from {event.source_agent}")
    
    def pause_replay(self, session_id: str):
        """Pause active replay"""
        with self.replay_lock:
            if session_id in self.active_replays:
                self.active_replays[session_id].status = "paused"
    
    def resume_replay(self, session_id: str):
        """Resume paused replay"""
        with self.replay_lock:
            if session_id in self.active_replays:
                session = self.active_replays[session_id]
                if session.status in ["paused", "breakpoint_hit"]:
                    session.status = "replaying"
    
    def stop_replay(self, session_id: str):
        """Stop active replay"""
        with self.replay_lock:
            if session_id in self.active_replays:
                self.active_replays[session_id].status = "stopped"

class TimeTravelDebugger:
    """Main time-travel debugging system"""
    
    def __init__(self, state_db_path: str = "debug_states.db",
                 event_db_path: str = "debug_events.db"):
        self.state_recorder = StateRecorder(state_db_path)
        self.event_log = EventLog(event_db_path)
        self.replay_engine = ReplayEngine(self.state_recorder, self.event_log)
        self.recording_active = True
        self.debug_sessions = {}
    
    def record_everything(self, agent_states: Dict[str, Dict[str, Any]],
                         active_messages: List[Dict[str, Any]],
                         recent_decisions: List[Dict[str, Any]],
                         external_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Record all state changes and events"""
        if not self.recording_active:
            return {"status": "recording_disabled"}
        
        recorded_data = {
            "timestamp": datetime.now().isoformat(),
            "agent_states": {},
            "messages": [],
            "decisions": [],
            "external_calls": [],
            "timeline": []
        }
        
        # Record agent states
        state_snapshots = self.state_recorder.capture_all_agents(agent_states)
        recorded_data["agent_states"] = {
            agent_id: asdict(snapshot) for agent_id, snapshot in state_snapshots.items()
        }
        
        # Record messages
        for message in active_messages:
            event = self.event_log.log_event(
                event_type=EventType.MESSAGE_SENT,
                source_agent=message.get("from_agent", "unknown"),
                target_agent=message.get("to_agent"),
                event_data=message
            )
            recorded_data["messages"].append(asdict(event))
        
        # Record decisions
        for decision in recent_decisions:
            event = self.event_log.log_event(
                event_type=EventType.DECISION_MADE,
                source_agent=decision.get("deciding_agent", "unknown"),
                event_data=decision
            )
            recorded_data["decisions"].append(asdict(event))
        
        # Record external calls
        for call in external_calls:
            event = self.event_log.log_event(
                event_type=EventType.EXTERNAL_CALL,
                source_agent=call.get("calling_agent", "unknown"),
                event_data=call
            )
            recorded_data["external_calls"].append(asdict(event))
        
        # Create timeline
        recorded_data["timeline"] = self._create_timeline(
            list(state_snapshots.values()) + 
            [event for event in recorded_data["messages"]] +
            [event for event in recorded_data["decisions"]] +
            [event for event in recorded_data["external_calls"]]
        )
        
        return recorded_data
    
    def replay_scenario(self, start_time: datetime, end_time: datetime,
                       focus_agent: Optional[str] = None,
                       speed: ReplaySpeed = ReplaySpeed.SLOW,
                       breakpoints: Optional[List[Dict[str, Any]]] = None) -> ReplaySession:
        """Replay exact scenario for debugging"""
        
        # Create scenario dict
        scenario = {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "focus_agent": focus_agent
        }
        
        # Convert breakpoint dicts to DebugBreakpoint objects
        debug_breakpoints = []
        if breakpoints:
            for bp_dict in breakpoints:
                breakpoint = DebugBreakpoint(
                    breakpoint_id=bp_dict.get("id", f"bp_{int(time.time())}"),
                    condition=bp_dict.get("condition", ""),
                    agent_filter=bp_dict.get("agent_filter"),
                    event_type_filter=EventType(bp_dict["event_type"]) if bp_dict.get("event_type") else None,
                    active=bp_dict.get("active", True),
                    hit_count=0,
                    created_at=datetime.now()
                )
                debug_breakpoints.append(breakpoint)
        
        return self.replay_engine.replay(scenario, speed, debug_breakpoints, focus_agent)
    
    def identify_interesting_points(self, scenario: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify interesting points in scenario for breakpoints"""
        start_time = datetime.fromisoformat(scenario["start_time"])
        end_time = datetime.fromisoformat(scenario["end_time"])
        
        interesting_points = []
        
        # Find error events
        error_events = self.event_log._capture_events_by_type(
            EventType.ERROR_OCCURRED, start_time, end_time
        )
        for event in error_events:
            interesting_points.append({
                "type": "error",
                "timestamp": event.timestamp.isoformat(),
                "description": f"Error in {event.source_agent}",
                "event_id": event.event_id
            })
        
        # Find decision points
        decision_events = self.event_log._capture_events_by_type(
            EventType.DECISION_MADE, start_time, end_time
        )
        for event in decision_events:
            interesting_points.append({
                "type": "decision",
                "timestamp": event.timestamp.isoformat(),
                "description": f"Decision made by {event.source_agent}",
                "event_id": event.event_id
            })
        
        # Find state changes (simplified - would analyze actual state deltas)
        interesting_points.append({
            "type": "state_change",
            "timestamp": start_time.isoformat(),
            "description": "Scenario start point"
        })
        
        interesting_points.append({
            "type": "state_change",
            "timestamp": end_time.isoformat(),
            "description": "Scenario end point"
        })
        
        return sorted(interesting_points, key=lambda x: x["timestamp"])
    
    def create_breakpoint(self, condition: str, agent_filter: Optional[str] = None,
                         event_type_filter: Optional[EventType] = None) -> DebugBreakpoint:
        """Create debug breakpoint"""
        breakpoint = DebugBreakpoint(
            breakpoint_id=f"bp_{int(time.time() * 1000)}",
            condition=condition,
            agent_filter=agent_filter,
            event_type_filter=event_type_filter,
            active=True,
            hit_count=0,
            created_at=datetime.now()
        )
        
        return breakpoint
    
    def get_system_state_at_time(self, timestamp: datetime,
                                agent_filter: Optional[str] = None) -> Dict[str, Any]:
        """Get complete system state at specific time"""
        system_state = {
            "timestamp": timestamp.isoformat(),
            "agent_states": {},
            "active_events": [],
            "system_metrics": {}
        }
        
        # Get agent states
        if agent_filter:
            agents_to_check = [agent_filter]
        else:
            # Get all known agents (simplified - would query agent registry)
            agents_to_check = [
                "agent-orchestrator-001",
                "agent-research-001",
                "agent-development-001",
                "agent-quality-001"
            ]
        
        for agent_id in agents_to_check:
            state_snapshot = self.state_recorder.get_state_at_time(agent_id, timestamp)
            if state_snapshot:
                system_state["agent_states"][agent_id] = asdict(state_snapshot)
        
        # Get events around that time
        time_window = timedelta(minutes=5)
        events = self.event_log._capture_events_by_type(
            EventType.SYSTEM_EVENT,
            timestamp - time_window,
            timestamp + time_window
        )
        system_state["active_events"] = [asdict(event) for event in events[:10]]
        
        return system_state
    
    def analyze_timeline(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Analyze timeline for patterns and anomalies"""
        analysis = {
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "duration_minutes": (end_time - start_time).total_seconds() / 60
            },
            "event_summary": {},
            "agent_activity": {},
            "anomalies": [],
            "performance_indicators": {}
        }
        
        # Analyze events by type
        for event_type in EventType:
            events = self.event_log._capture_events_by_type(event_type, start_time, end_time)
            analysis["event_summary"][event_type.value] = {
                "count": len(events),
                "frequency_per_minute": len(events) / max(1, (end_time - start_time).total_seconds() / 60)
            }
        
        # Analyze agent activity
        all_messages = self.event_log.capture_all_messages(start_time, end_time)
        agent_message_counts = {}
        for message in all_messages:
            agent = message.source_agent
            agent_message_counts[agent] = agent_message_counts.get(agent, 0) + 1
        
        analysis["agent_activity"] = agent_message_counts
        
        # Identify anomalies (simplified)
        error_events = self.event_log._capture_events_by_type(
            EventType.ERROR_OCCURRED, start_time, end_time
        )
        for error in error_events:
            analysis["anomalies"].append({
                "type": "error",
                "timestamp": error.timestamp.isoformat(),
                "agent": error.source_agent,
                "description": str(error.event_data)
            })
        
        return analysis
    
    def _create_timeline(self, events: List[Any]) -> List[Dict[str, Any]]:
        """Create timeline from mixed events"""
        timeline_items = []
        
        for item in events:
            if isinstance(item, StateSnapshot):
                timeline_items.append({
                    "timestamp": item.timestamp.isoformat(),
                    "type": "state_change",
                    "agent": item.agent_id,
                    "description": f"State changed for {item.agent_id}"
                })
            elif hasattr(item, 'event_type'):
                timeline_items.append({
                    "timestamp": item.get("timestamp", datetime.now().isoformat()),
                    "type": "event",
                    "event_type": item.get("event_type", "unknown"),
                    "agent": item.get("source_agent", "unknown"),
                    "description": f"Event: {item.get('event_type', 'unknown')}"
                })
        
        return sorted(timeline_items, key=lambda x: x["timestamp"])
    
    def start_recording(self):
        """Start recording system state and events"""
        self.recording_active = True
        self.state_recorder.recording_active = True
        logger.info("Time-travel debugging recording started")
    
    def stop_recording(self):
        """Stop recording system state and events"""
        self.recording_active = False
        self.state_recorder.recording_active = False
        logger.info("Time-travel debugging recording stopped")
    
    def get_debug_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get status of debug session"""
        with self.replay_engine.replay_lock:
            if session_id in self.replay_engine.active_replays:
                session = self.replay_engine.active_replays[session_id]
                return {
                    "session_id": session.session_id,
                    "status": session.status,
                    "progress": {
                        "current_position": session.current_position.isoformat(),
                        "events_processed": session.events_processed,
                        "total_events": session.total_events,
                        "percentage": (session.events_processed / session.total_events * 100) if session.total_events > 0 else 0
                    },
                    "replay_speed": session.replay_speed.value,
                    "focus_agent": session.focus_agent,
                    "breakpoints_active": len([bp for bp in session.breakpoints if bp.active])
                }
        
        return {"error": "Session not found"}

# Example usage
if __name__ == "__main__":
    # Initialize time-travel debugger
    debugger = TimeTravelDebugger()
    
    # Example agent states
    agent_states = {
        "agent-orchestrator-001": {
            "current_tasks": ["task1", "task2"],
            "load": 0.7,
            "status": "active"
        },
        "agent-research-001": {
            "current_research": "AI frameworks",
            "confidence": 0.85,
            "status": "researching"
        }
    }
    
    # Record current state
    recorded_data = debugger.record_everything(
        agent_states=agent_states,
        active_messages=[
            {"from_agent": "orchestrator", "to_agent": "research", "content": "Start research task"}
        ],
        recent_decisions=[
            {"deciding_agent": "orchestrator", "decision": "Assign task to research team"}
        ],
        external_calls=[
            {"calling_agent": "research", "api": "web_search", "query": "AI frameworks 2025"}
        ]
    )
    
    print("Recording completed:")
    print(f"- Agent states captured: {len(recorded_data['agent_states'])}")
    print(f"- Messages recorded: {len(recorded_data['messages'])}")
    print(f"- Decisions recorded: {len(recorded_data['decisions'])}")
    print(f"- External calls recorded: {len(recorded_data['external_calls'])}")
    
    # Create breakpoint
    breakpoint = debugger.create_breakpoint(
        condition="error",
        event_type_filter=EventType.ERROR_OCCURRED
    )
    
    # Simulate replay scenario
    start_time = datetime.now() - timedelta(hours=1)
    end_time = datetime.now()
    
    replay_session = debugger.replay_scenario(
        start_time=start_time,
        end_time=end_time,
        speed=ReplaySpeed.SLOW,
        breakpoints=[asdict(breakpoint)]
    )
    
    print(f"\nReplay session started: {replay_session.session_id}")
    print(f"Status: {replay_session.status}")
    
    # Get timeline analysis
    analysis = debugger.analyze_timeline(start_time, end_time)
    print(f"\nTimeline Analysis:")
    print(f"Duration: {analysis['time_range']['duration_minutes']:.1f} minutes")
    print(f"Event types: {list(analysis['event_summary'].keys())}")
    print(f"Active agents: {list(analysis['agent_activity'].keys())}")