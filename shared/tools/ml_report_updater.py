#!/usr/bin/env python3
"""
ML Report Updater - Automatically updates the Agent ML & Context Improvements Report
Runs periodically to gather latest metrics and update the documentation
"""

import os
import sys
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MLReportUpdater:
    """Updates ML & Context Improvements Report with latest metrics"""
    
    def __init__(self):
        self.base_path = Path(r"C:\Jarvis\AI Workspace\Super Agent")
        self.report_path = self.base_path / "reports" / "AGENT_ML_CONTEXT_IMPROVEMENTS.md"
        self.metrics_db = self.base_path / "memory" / "context" / "jarvis" / "enhanced_learning.db"
        self.auto_accept_db = self.base_path / "memory" / "context" / "jarvis" / "auto_acceptance.db"
        self.context_db = self.base_path / "memory" / "context" / "jarvis" / "jarvis_context.db"
        
        # Agent metrics storage
        self.agent_metrics = {}
        self.last_update = None
    
    def gather_metrics(self) -> Dict:
        """Gather latest metrics from all sources"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'agents': {},
            'system_wide': {},
            'learning_stats': {},
            'collaboration': {}
        }
        
        # Gather from each data source
        self._gather_learning_metrics(metrics)
        self._gather_auto_acceptance_metrics(metrics)
        self._gather_context_metrics(metrics)
        self._gather_heartbeat_metrics(metrics)
        self._gather_decision_logs(metrics)
        
        return metrics
    
    def _gather_learning_metrics(self, metrics: Dict):
        """Gather metrics from enhanced learning system"""
        if not self.metrics_db.exists():
            logger.warning("Enhanced learning database not found")
            return
        
        try:
            conn = sqlite3.connect(str(self.metrics_db))
            cursor = conn.cursor()
            
            # Total patterns learned
            cursor.execute("SELECT COUNT(*) FROM learned_patterns")
            total_patterns = cursor.fetchone()[0]
            metrics['learning_stats']['total_patterns'] = total_patterns
            
            # Success rates by pattern type
            cursor.execute("""
                SELECT pattern_type, 
                       AVG(CAST(success_count AS FLOAT) / (success_count + failure_count)) as success_rate,
                       COUNT(*) as pattern_count
                FROM learned_patterns
                WHERE success_count + failure_count > 0
                GROUP BY pattern_type
            """)
            
            pattern_stats = cursor.fetchall()
            metrics['learning_stats']['pattern_types'] = {
                row[0]: {'success_rate': row[1], 'count': row[2]}
                for row in pattern_stats
            }
            
            # Agent-specific metrics
            cursor.execute("""
                SELECT agent_id,
                       COUNT(*) as patterns,
                       AVG(confidence_level) as avg_confidence,
                       MAX(last_used) as last_activity
                FROM learned_patterns
                GROUP BY agent_id
            """)
            
            for row in cursor.fetchall():
                agent_id = row[0]
                if agent_id not in metrics['agents']:
                    metrics['agents'][agent_id] = {}
                
                metrics['agents'][agent_id]['learned_patterns'] = row[1]
                metrics['agents'][agent_id]['avg_confidence'] = row[2]
                metrics['agents'][agent_id]['last_learning'] = row[3]
            
            # Knowledge transfer metrics
            cursor.execute("""
                SELECT from_agent, to_agent, COUNT(*) as transfers
                FROM knowledge_transfers
                WHERE timestamp > datetime('now', '-7 days')
                GROUP BY from_agent, to_agent
            """)
            
            transfers = cursor.fetchall()
            metrics['collaboration']['knowledge_transfers'] = [
                {'from': row[0], 'to': row[1], 'count': row[2]}
                for row in transfers
            ]
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error gathering learning metrics: {e}")
    
    def _gather_auto_acceptance_metrics(self, metrics: Dict):
        """Gather metrics from auto-acceptance system"""
        if not self.auto_accept_db.exists():
            logger.warning("Auto-acceptance database not found")
            return
        
        try:
            conn = sqlite3.connect(str(self.auto_accept_db))
            cursor = conn.cursor()
            
            # Recent decision statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN auto_accepted = 1 THEN 1 END) as auto_accepted,
                    COUNT(CASE WHEN outcome = 'success' THEN 1 END) as successful,
                    AVG(confidence_score) as avg_confidence
                FROM decision_history
                WHERE timestamp > datetime('now', '-24 hours')
            """)
            
            stats = cursor.fetchone()
            metrics['system_wide']['auto_acceptance'] = {
                'total_decisions_24h': stats[0],
                'auto_accepted_24h': stats[1],
                'successful_24h': stats[2],
                'avg_confidence': stats[3]
            }
            
            # Risk level distribution
            cursor.execute("""
                SELECT risk_level, COUNT(*) as count
                FROM decision_history
                WHERE timestamp > datetime('now', '-7 days')
                GROUP BY risk_level
            """)
            
            risk_dist = cursor.fetchall()
            metrics['system_wide']['risk_distribution'] = {
                f"level_{row[0]}": row[1] for row in risk_dist
            }
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error gathering auto-acceptance metrics: {e}")
    
    def _gather_context_metrics(self, metrics: Dict):
        """Gather metrics from context management system"""
        if not self.context_db.exists():
            logger.warning("Context database not found")
            return
        
        try:
            conn = sqlite3.connect(str(self.context_db))
            cursor = conn.cursor()
            
            # Context retention stats
            cursor.execute("""
                SELECT COUNT(*) as contexts,
                       AVG(LENGTH(context_data)) as avg_size
                FROM context_snapshots
            """)
            
            stats = cursor.fetchone()
            metrics['system_wide']['context_management'] = {
                'total_contexts': stats[0],
                'avg_context_size': stats[1]
            }
            
            # Recovery events
            cursor.execute("""
                SELECT COUNT(*) as recovery_count
                FROM recovery_log
                WHERE timestamp > datetime('now', '-30 days')
            """)
            
            recovery_count = cursor.fetchone()[0]
            metrics['system_wide']['context_management']['recoveries_30d'] = recovery_count
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error gathering context metrics: {e}")
    
    def _gather_heartbeat_metrics(self, metrics: Dict):
        """Gather metrics from agent heartbeats"""
        heartbeat_dir = self.base_path / "shared" / "heartbeats"
        
        if not heartbeat_dir.exists():
            logger.warning("Heartbeat directory not found")
            return
        
        active_agents = 0
        total_agents = 0
        
        for heartbeat_file in heartbeat_dir.glob("*.heartbeat"):
            total_agents += 1
            
            try:
                with open(heartbeat_file, 'r') as f:
                    data = json.load(f)
                    
                    agent_id = data.get('agent_id', 'unknown')
                    if agent_id not in metrics['agents']:
                        metrics['agents'][agent_id] = {}
                    
                    # Check if active (heartbeat within last 2 minutes)
                    timestamp = datetime.fromisoformat(data['timestamp'])
                    is_active = (datetime.now() - timestamp).seconds < 120
                    
                    if is_active:
                        active_agents += 1
                    
                    metrics['agents'][agent_id]['status'] = 'active' if is_active else 'inactive'
                    metrics['agents'][agent_id]['last_heartbeat'] = data['timestamp']
                    metrics['agents'][agent_id]['context_active'] = data.get('context_active', False)
                    
            except Exception as e:
                logger.error(f"Error reading heartbeat {heartbeat_file}: {e}")
        
        metrics['system_wide']['agent_health'] = {
            'total_agents': total_agents,
            'active_agents': active_agents,
            'health_percentage': (active_agents / total_agents * 100) if total_agents > 0 else 0
        }
    
    def _gather_decision_logs(self, metrics: Dict):
        """Gather metrics from decision logs"""
        decision_log = self.base_path / "memory" / "context" / "jarvis" / "decision_audit_trail.jsonl"
        
        if not decision_log.exists():
            return
        
        try:
            recent_decisions = []
            with open(decision_log, 'r') as f:
                for line in f:
                    try:
                        decision = json.loads(line.strip())
                        decision_time = datetime.fromisoformat(decision['timestamp'])
                        
                        # Only last 24 hours
                        if (datetime.now() - decision_time).total_seconds() < 86400:
                            recent_decisions.append(decision)
                    except:
                        continue
            
            if recent_decisions:
                metrics['system_wide']['autonomous_decisions'] = {
                    'count_24h': len(recent_decisions),
                    'agents_involved': len(set(d['agent_id'] for d in recent_decisions)),
                    'avg_confidence': sum(d.get('confidence', 0) for d in recent_decisions) / len(recent_decisions)
                }
                
        except Exception as e:
            logger.error(f"Error gathering decision logs: {e}")
    
    def update_report(self, metrics: Dict):
        """Update the report with new metrics"""
        if not self.report_path.exists():
            logger.error("Report file not found")
            return
        
        # Read current report
        with open(self.report_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update timestamp
        content = re.sub(
            r'Last Updated: .*',
            f'Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            content
        )
        
        # Update system-wide metrics section
        if 'system_wide' in metrics:
            system_metrics = metrics['system_wide']
            
            # Update overall success rate
            if 'auto_acceptance' in system_metrics:
                auto_metrics = system_metrics['auto_acceptance']
                if auto_metrics['total_decisions_24h'] > 0:
                    success_rate = (auto_metrics['successful_24h'] / auto_metrics['auto_accepted_24h'] * 100) if auto_metrics['auto_accepted_24h'] > 0 else 0
                    content = re.sub(
                        r'\*\*Overall Success Rate\*\*: [\d.]+%',
                        f'**Overall Success Rate**: {success_rate:.1f}%',
                        content
                    )
            
            # Update pattern database size
            if 'learning_stats' in metrics:
                pattern_count = metrics['learning_stats'].get('total_patterns', 0)
                content = re.sub(
                    r'\*\*Pattern Database\*\*: [\d,]+ learned patterns',
                    f'**Pattern Database**: {pattern_count:,} learned patterns',
                    content
                )
        
        # Update individual agent metrics
        self._update_agent_sections(content, metrics)
        
        # Add update log
        update_log = self._generate_update_log(metrics)
        
        # Insert update log before conclusion
        if '## Conclusion' in content:
            content = content.replace(
                '## Conclusion',
                f'{update_log}\n\n## Conclusion'
            )
        else:
            content += f'\n\n{update_log}'
        
        # Write updated report
        with open(self.report_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Report updated successfully at {datetime.now()}")
    
    def _update_agent_sections(self, content: str, metrics: Dict):
        """Update individual agent metric sections"""
        # This would update specific agent metrics in the report
        # Implementation depends on exact report format
        pass
    
    def _generate_update_log(self, metrics: Dict) -> str:
        """Generate update log section"""
        log = f"""## Latest Update Log

**Last Updated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

### Recent Metrics
- **Active Agents**: {metrics['system_wide']['agent_health']['active_agents']}/{metrics['system_wide']['agent_health']['total_agents']}
- **System Health**: {metrics['system_wide']['agent_health']['health_percentage']:.1f}%
- **Decisions (24h)**: {metrics['system_wide'].get('auto_acceptance', {}).get('total_decisions_24h', 0)}
- **Learning Patterns**: {metrics['learning_stats'].get('total_patterns', 0)}

### Recent Improvements
"""
        
        # Add pattern type improvements
        if 'pattern_types' in metrics['learning_stats']:
            for ptype, stats in metrics['learning_stats']['pattern_types'].items():
                log += f"- **{ptype}**: {stats['success_rate']*100:.1f}% success rate ({stats['count']} patterns)\n"
        
        return log
    
    def schedule_updates(self, interval_hours: int = 6):
        """Schedule periodic updates"""
        import schedule
        import time
        
        def job():
            logger.info("Starting scheduled ML report update")
            metrics = self.gather_metrics()
            self.update_report(metrics)
        
        # Run immediately
        job()
        
        # Schedule future runs
        schedule.every(interval_hours).hours.do(job)
        
        logger.info(f"ML Report Updater scheduled every {interval_hours} hours")
        
        while True:
            schedule.run_pending()
            time.sleep(60)


def main():
    """Main entry point"""
    updater = MLReportUpdater()
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--once':
            # Run once and exit
            logger.info("Running single update")
            metrics = updater.gather_metrics()
            updater.update_report(metrics)
        elif sys.argv[1] == '--schedule':
            # Run on schedule
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 6
            updater.schedule_updates(interval)
    else:
        # Default: run once
        metrics = updater.gather_metrics()
        updater.update_report(metrics)
        
        # Print summary
        print("[ML REPORT UPDATE COMPLETE]")
        print(f"Timestamp: {datetime.now()}")
        print(f"Active Agents: {metrics['system_wide']['agent_health']['active_agents']}")
        print(f"Total Patterns: {metrics['learning_stats'].get('total_patterns', 0)}")


if __name__ == "__main__":
    main()