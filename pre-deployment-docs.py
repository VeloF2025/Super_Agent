#!/usr/bin/env python3
"""
Pre-Deployment Documentation Automation
Automatically updates all relevant docs before git push or deployment
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

class PreDeploymentDocUpdater:
    def __init__(self):
        self.workspace_root = Path("C:/Jarvis/AI Workspace/Super Agent")
        self.docs_generator = self.workspace_root / "docs-generator.py"
        self.git_hooks_dir = self.workspace_root / ".git" / "hooks"
        
    def run_pre_deployment_check(self):
        """Run comprehensive pre-deployment documentation check"""
        print("\n" + "="*60)
        print("PRE-DEPLOYMENT DOCUMENTATION UPDATE")
        print("="*60)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        results = {
            'checks_passed': [],
            'checks_failed': [],
            'docs_updated': [],
            'warnings': [],
            'ready_for_deployment': False
        }
        
        # 1. Check git status
        print("CHECKING GIT STATUS")
        print("-" * 30)
        git_status = self.check_git_status()
        if git_status['clean']:
            results['checks_passed'].append("Git working directory is clean")
            print("  OK Working directory clean")
        else:
            results['warnings'].append(f"Uncommitted changes: {git_status['changes']}")
            print(f"  WARNING Uncommitted changes found: {git_status['changes']}")
        
        # 2. Update documentation
        print("\nUPDATING DOCUMENTATION")
        print("-" * 30)
        doc_results = self.update_all_documentation()
        results['docs_updated'] = doc_results['updated_files'] + doc_results['created_files']
        
        if doc_results['errors']:
            results['checks_failed'].extend(doc_results['errors'])
            print(f"  ERROR Documentation errors: {len(doc_results['errors'])}")
        else:
            results['checks_passed'].append("Documentation updated successfully")
            print(f"  OK Documentation updated: {len(results['docs_updated'])} files")
        
        # 3. Validate project structure
        print("\nVALIDATING PROJECT STRUCTURE")
        print("-" * 30)
        structure_check = self.validate_project_structure()
        if structure_check['valid']:
            results['checks_passed'].append("Project structure is valid")
            print("  OK Project structure valid")
        else:
            results['checks_failed'].extend(structure_check['issues'])
            print(f"  ERROR Structure issues: {len(structure_check['issues'])}")
        
        # 4. Check dependencies
        print("\nCHECKING DEPENDENCIES")
        print("-" * 30)
        deps_check = self.check_dependencies()
        if deps_check['satisfied']:
            results['checks_passed'].append("All dependencies satisfied")
            print("  OK Dependencies satisfied")
        else:
            results['checks_failed'].extend(deps_check['missing'])
            print(f"  ERROR Missing dependencies: {len(deps_check['missing'])}")
        
        # 5. Run system health check
        print("\nSYSTEM HEALTH CHECK")
        print("-" * 30)
        health_check = self.run_system_health_check()
        if health_check['healthy']:
            results['checks_passed'].append("System health check passed")
            print("  OK System healthy")
        else:
            results['checks_failed'].extend(health_check['issues'])
            print(f"  ERROR Health issues: {len(health_check['issues'])}")
        
        # 6. Generate deployment checklist
        print("\nGENERATING DEPLOYMENT CHECKLIST")
        print("-" * 30)
        checklist = self.generate_deployment_checklist(results)
        print(f"  OK Checklist created: {checklist}")
        
        # 7. Determine deployment readiness
        results['ready_for_deployment'] = len(results['checks_failed']) == 0
        
        # 8. Generate final report
        self.generate_pre_deployment_report(results)
        
        # 9. Summary
        self.print_summary(results)
        
        return results
    
    def check_git_status(self):
        """Check git repository status"""
        try:
            # Check if we're in a git repository
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, cwd=self.workspace_root)
            
            if result.returncode == 0:
                changes = result.stdout.strip()
                return {
                    'clean': len(changes) == 0,
                    'changes': len(changes.split('\n')) if changes else 0,
                    'details': changes
                }
            else:
                return {'clean': False, 'changes': 'Git check failed', 'details': result.stderr}
                
        except Exception as e:
            return {'clean': False, 'changes': f'Error: {e}', 'details': str(e)}
    
    def update_all_documentation(self):
        """Update all project documentation"""
        try:
            if not self.docs_generator.exists():
                return {
                    'updated_files': [],
                    'created_files': [],
                    'errors': ['Documentation generator not found']
                }
            
            # Run documentation generator
            result = subprocess.run([
                sys.executable, str(self.docs_generator), 'all'
            ], capture_output=True, text=True, cwd=self.workspace_root)
            
            if result.returncode == 0:
                # Parse output for updated/created files
                output_lines = result.stdout.split('\n')
                updated_files = []
                created_files = []
                
                for line in output_lines:
                    if 'updated' in line.lower():
                        updated_files.append(line.strip())
                    elif 'created' in line.lower() or 'generated' in line.lower():
                        created_files.append(line.strip())
                
                return {
                    'updated_files': updated_files,
                    'created_files': created_files,
                    'errors': []
                }
            else:
                return {
                    'updated_files': [],
                    'created_files': [],
                    'errors': [f'Documentation generator failed: {result.stderr}']
                }
                
        except Exception as e:
            return {
                'updated_files': [],
                'created_files': [],
                'errors': [f'Documentation update error: {e}']
            }
    
    def validate_project_structure(self):
        """Validate project structure for deployment"""
        required_files = [
            'README.md',
            'daily-ops/morning-standup.py',
            'daily-ops/evening-shutdown.py',
            'agent-dashboard/package.json',
            'housekeeper/oa-interface.py'
        ]
        
        required_dirs = [
            'agents',
            'communication',
            'memory',
            'docs'
        ]
        
        issues = []
        
        # Check required files
        for file_path in required_files:
            full_path = self.workspace_root / file_path
            if not full_path.exists():
                issues.append(f"Missing required file: {file_path}")
        
        # Check required directories
        for dir_path in required_dirs:
            full_path = self.workspace_root / dir_path
            if not full_path.exists():
                issues.append(f"Missing required directory: {dir_path}")
        
        # Check for common issues
        if (self.workspace_root / "node_modules").exists():
            issues.append("node_modules directory found in root (should be in subdirectories)")
        
        # Check file sizes (detect any huge files)
        for file_path in self.workspace_root.rglob('*'):
            if file_path.is_file():
                try:
                    size_mb = file_path.stat().st_size / (1024 * 1024)
                    if size_mb > 100:  # Files larger than 100MB
                        issues.append(f"Large file detected: {file_path.relative_to(self.workspace_root)} ({size_mb:.1f}MB)")
                except:
                    pass
        
        return {
            'valid': len(issues) == 0,
            'issues': issues
        }
    
    def check_dependencies(self):
        """Check system dependencies"""
        missing = []
        
        # Check Python
        try:
            python_version = subprocess.run([sys.executable, '--version'], 
                                          capture_output=True, text=True)
            if python_version.returncode != 0:
                missing.append("Python interpreter not working")
        except:
            missing.append("Python not found")
        
        # Check Node.js (for dashboard)
        try:
            node_version = subprocess.run(['node', '--version'], 
                                        capture_output=True, text=True)
            if node_version.returncode != 0:
                missing.append("Node.js not found")
        except:
            missing.append("Node.js not available")
        
        # Check required Python packages
        required_packages = ['schedule', 'watchdog']
        for package in required_packages:
            try:
                subprocess.run([sys.executable, '-c', f'import {package}'], 
                             capture_output=True, check=True)
            except:
                missing.append(f"Python package missing: {package}")
        
        # Check dashboard dependencies
        dashboard_package_json = self.workspace_root / "agent-dashboard" / "package.json"
        if dashboard_package_json.exists():
            node_modules = self.workspace_root / "agent-dashboard" / "node_modules"
            if not node_modules.exists():
                missing.append("Dashboard dependencies not installed (run npm install)")
        
        return {
            'satisfied': len(missing) == 0,
            'missing': missing
        }
    
    def run_system_health_check(self):
        """Run comprehensive system health check"""
        issues = []
        
        try:
            # Check disk space
            import shutil
            total, used, free = shutil.disk_usage(self.workspace_root)
            free_gb = free / (1024**3)
            if free_gb < 1:  # Less than 1GB free
                issues.append(f"Low disk space: {free_gb:.1f}GB free")
            
            # Check communication system
            comm_dir = self.workspace_root / "communication"
            if comm_dir.exists():
                queue_dir = comm_dir / "queue"
                if queue_dir.exists():
                    queue_files = list(queue_dir.glob("*.json"))
                    if len(queue_files) > 100:
                        issues.append(f"Communication queue backlog: {len(queue_files)} messages")
            
            # Check log files for errors
            logs_dir = self.workspace_root / "logs"
            if logs_dir.exists():
                recent_errors = self.check_recent_errors(logs_dir)
                if recent_errors > 10:
                    issues.append(f"High error count in logs: {recent_errors} recent errors")
            
            # Check agent status
            agents_dir = self.workspace_root.parent / "agents"
            if agents_dir.exists():
                agent_dirs = list(agents_dir.glob("agent-*"))
                if len(agent_dirs) == 0:
                    issues.append("No agent directories found")
            
            # Check memory usage
            memory_dir = self.workspace_root / "memory"
            if memory_dir.exists():
                memory_size = sum(f.stat().st_size for f in memory_dir.rglob('*') if f.is_file())
                memory_mb = memory_size / (1024**2)
                if memory_mb > 1000:  # More than 1GB
                    issues.append(f"Large memory usage: {memory_mb:.1f}MB")
            
        except Exception as e:
            issues.append(f"Health check error: {e}")
        
        return {
            'healthy': len(issues) == 0,
            'issues': issues
        }
    
    def check_recent_errors(self, logs_dir):
        """Check for recent errors in log files"""
        error_count = 0
        try:
            from datetime import timedelta
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            for log_file in logs_dir.rglob("*.log"):
                try:
                    mod_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if mod_time > cutoff_time:
                        with open(log_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            error_count += content.lower().count('error')
                            error_count += content.lower().count('failed')
                            error_count += content.lower().count('exception')
                except:
                    pass
        except:
            pass
        
        return error_count
    
    def generate_deployment_checklist(self, results):
        """Generate deployment checklist"""
        checklist_content = f"""# Pre-Deployment Checklist

*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## ✅ Completed Checks
{chr(10).join(f"- [x] {check}" for check in results['checks_passed'])}

## ❌ Failed Checks
{chr(10).join(f"- [ ] {check}" for check in results['checks_failed'])}

## ⚠️ Warnings
{chr(10).join(f"- {warning}" for warning in results['warnings'])}

## 📚 Documentation Updates
{chr(10).join(f"- {doc}" for doc in results['docs_updated'])}

## 🚀 Deployment Status
**Ready for Deployment**: {'✅ YES' if results['ready_for_deployment'] else '❌ NO'}

## Pre-Deployment Actions Required

### If Ready for Deployment:
1. Commit any documentation updates
2. Tag the release version
3. Push to remote repository
4. Run deployment scripts
5. Monitor system after deployment

### If NOT Ready for Deployment:
1. Address all failed checks
2. Resolve warnings if critical
3. Re-run pre-deployment check
4. Repeat until all checks pass

## Manual Verification Steps
- [ ] Dashboard accessible at http://localhost:3000
- [ ] All agents responding to health checks
- [ ] Communication system working
- [ ] Housekeeper service running
- [ ] Daily operations scheduled
- [ ] Git repository clean and up to date

## Post-Deployment Verification
- [ ] System startup successful
- [ ] All services operational
- [ ] Monitoring alerts configured
- [ ] Backup systems verified
- [ ] Documentation accessible

---
*Jarvis Pre-Deployment Check System*
"""
        
        checklist_file = self.workspace_root / "DEPLOYMENT_CHECKLIST.md"
        with open(checklist_file, 'w', encoding='utf-8') as f:
            f.write(checklist_content)
        
        return checklist_file
    
    def generate_pre_deployment_report(self, results):
        """Generate comprehensive pre-deployment report"""
        report_content = f"""# Pre-Deployment Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**System**: Jarvis Super Agent System
**Deployment Status**: {'✅ READY' if results['ready_for_deployment'] else '❌ NOT READY'}

## Executive Summary

{self.generate_executive_summary(results)}

## Detailed Results

### ✅ Passed Checks ({len(results['checks_passed'])})
{chr(10).join(f"- {check}" for check in results['checks_passed'])}

### ❌ Failed Checks ({len(results['checks_failed'])})
{chr(10).join(f"- {check}" for check in results['checks_failed'])}

### ⚠️ Warnings ({len(results['warnings'])})
{chr(10).join(f"- {warning}" for warning in results['warnings'])}

### 📚 Documentation Updates ({len(results['docs_updated'])})
{chr(10).join(f"- {doc}" for doc in results['docs_updated'])}

## System Overview

- **Total Checks Run**: {len(results['checks_passed']) + len(results['checks_failed'])}
- **Success Rate**: {len(results['checks_passed']) / (len(results['checks_passed']) + len(results['checks_failed'])) * 100:.1f}%
- **Critical Issues**: {len([check for check in results['checks_failed'] if 'critical' in check.lower()])}
- **Documentation Files Updated**: {len(results['docs_updated'])}

## Next Steps

{self.generate_next_steps(results)}

## Risk Assessment

{self.generate_risk_assessment(results)}

---
*Generated by Jarvis Pre-Deployment System*
"""
        
        report_file = self.workspace_root / "PRE_DEPLOYMENT_REPORT.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return report_file
    
    def generate_executive_summary(self, results):
        """Generate executive summary"""
        if results['ready_for_deployment']:
            return """The system has passed all pre-deployment checks and is ready for deployment. 
All documentation has been updated, dependencies are satisfied, and system health checks have passed.
The deployment can proceed with confidence."""
        else:
            critical_issues = len(results['checks_failed'])
            return f"""The system is NOT ready for deployment. {critical_issues} critical issues must be 
resolved before deployment can proceed. Address all failed checks and re-run the pre-deployment 
verification to ensure system readiness."""
    
    def generate_next_steps(self, results):
        """Generate next steps based on results"""
        if results['ready_for_deployment']:
            return """1. Commit any pending documentation updates
2. Create a release tag with appropriate version number
3. Push changes to remote repository
4. Execute deployment scripts
5. Monitor system health post-deployment
6. Verify all services are operational"""
        else:
            return """1. Address all failed checks listed above
2. Resolve critical warnings
3. Re-run pre-deployment check
4. Verify all issues are resolved
5. Repeat until deployment readiness is achieved"""
    
    def generate_risk_assessment(self, results):
        """Generate risk assessment"""
        risk_level = "LOW"
        if results['checks_failed']:
            risk_level = "HIGH"
        elif results['warnings']:
            risk_level = "MEDIUM"
        
        risk_factors = []
        if not results['ready_for_deployment']:
            risk_factors.append("System not ready for deployment")
        if results['warnings']:
            risk_factors.append(f"{len(results['warnings'])} warnings identified")
        
        return f"""**Risk Level**: {risk_level}

**Risk Factors**:
{chr(10).join(f"- {factor}" for factor in risk_factors) if risk_factors else "- No significant risk factors identified"}

**Mitigation**:
- Complete all pre-deployment checks before deployment
- Monitor system closely during and after deployment
- Have rollback procedures ready
- Maintain communication with development team"""
    
    def print_summary(self, results):
        """Print deployment readiness summary"""
        print("\n" + "="*60)
        print("PRE-DEPLOYMENT SUMMARY")
        print("="*60)
        
        status_icon = "OK" if results['ready_for_deployment'] else "ERROR"
        status_text = "READY FOR DEPLOYMENT" if results['ready_for_deployment'] else "NOT READY"
        
        print(f"Status: {status_icon} {status_text}")
        print(f"Checks Passed: {len(results['checks_passed'])}")
        print(f"Checks Failed: {len(results['checks_failed'])}")
        print(f"Warnings: {len(results['warnings'])}")
        print(f"Docs Updated: {len(results['docs_updated'])}")
        
        if results['checks_failed']:
            print("\nCRITICAL ISSUES TO RESOLVE:")
            for issue in results['checks_failed']:
                print(f"   • {issue}")
        
        if results['warnings']:
            print("\nWARNINGS:")
            for warning in results['warnings']:
                print(f"   • {warning}")
        
        print(f"\nReports generated:")
        print(f"   • DEPLOYMENT_CHECKLIST.md")
        print(f"   • PRE_DEPLOYMENT_REPORT.md")
        
        print("\n" + "="*60)
    
    def install_git_hooks(self):
        """Install git pre-commit and pre-push hooks"""
        if not self.git_hooks_dir.exists():
            print("ERROR Not a git repository or hooks directory not found")
            return False
        
        # Pre-commit hook
        pre_commit_hook = f"""#!/usr/bin/env python3
# Jarvis Pre-Commit Hook
import subprocess
import sys
from pathlib import Path

workspace_root = Path(__file__).parent.parent.parent
pre_deployment_script = workspace_root / "pre-deployment-docs.py"

print("Running Jarvis pre-commit documentation check...")

result = subprocess.run([
    sys.executable, str(pre_deployment_script), "quick"
], cwd=workspace_root)

if result.returncode != 0:
    print("ERROR Pre-commit check failed")
    print("Run 'python pre-deployment-docs.py' to see details")
    sys.exit(1)

print("OK Pre-commit check passed")
"""
        
        # Pre-push hook
        pre_push_hook = f"""#!/usr/bin/env python3
# Jarvis Pre-Push Hook
import subprocess
import sys
from pathlib import Path

workspace_root = Path(__file__).parent.parent.parent
pre_deployment_script = workspace_root / "pre-deployment-docs.py"

print("Running Jarvis pre-push deployment readiness check...")

result = subprocess.run([
    sys.executable, str(pre_deployment_script)
], cwd=workspace_root)

if result.returncode != 0:
    print("ERROR Deployment readiness check failed")
    print("System is not ready for deployment")
    sys.exit(1)

print("OK System ready for deployment")
"""
        
        # Write hooks
        pre_commit_file = self.git_hooks_dir / "pre-commit"
        pre_push_file = self.git_hooks_dir / "pre-push"
        
        with open(pre_commit_file, 'w') as f:
            f.write(pre_commit_hook)
        
        with open(pre_push_file, 'w') as f:
            f.write(pre_push_hook)
        
        # Make executable (on Unix systems)
        try:
            pre_commit_file.chmod(0o755)
            pre_push_file.chmod(0o755)
        except:
            pass
        
        print("OK Git hooks installed successfully")
        print("   • pre-commit: Quick documentation check")
        print("   • pre-push: Full deployment readiness check")
        
        return True


def main():
    """Main function for command line usage"""
    import sys
    
    updater = PreDeploymentDocUpdater()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "quick":
            # Quick check (for pre-commit hook)
            results = updater.update_all_documentation()
            if results['errors']:
                print("ERROR Documentation update failed")
                sys.exit(1)
            else:
                print("OK Documentation updated")
                sys.exit(0)
        
        elif command == "install-hooks":
            success = updater.install_git_hooks()
            sys.exit(0 if success else 1)
        
        elif command == "docs-only":
            results = updater.update_all_documentation()
            print(f"Updated: {len(results['updated_files'])} files")
            print(f"Created: {len(results['created_files'])} files")
            print(f"Errors: {len(results['errors'])}")
            sys.exit(0 if not results['errors'] else 1)
        
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    else:
        # Full pre-deployment check
        results = updater.run_pre_deployment_check()
        sys.exit(0 if results['ready_for_deployment'] else 1)


if __name__ == "__main__":
    main()