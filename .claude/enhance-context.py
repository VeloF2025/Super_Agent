#!/usr/bin/env python3
"""
Context Enhancement Tool for Super Agent System
Improves existing CLAUDE.md files without overwriting
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

class ContextEnhancer:
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root)
        self.claude_dir = self.workspace_root / ".claude"
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """Load configuration from .claude/config.json"""
        config_path = self.claude_dir / "config.json"
        if config_path.exists():
            return json.loads(config_path.read_text())
        return {}
    
    def enhance_claude_md(self, file_path: Path) -> Dict[str, str]:
        """
        Enhances an existing CLAUDE.md file with:
        - Privacy separation markers
        - Context inheritance references
        - Standardized sections
        - Git-friendly formatting
        """
        if not file_path.exists():
            return {"error": f"File {file_path} not found"}
        
        original_content = file_path.read_text()
        enhanced_content = original_content
        
        # Check for missing standard sections
        standard_sections = {
            "## Context Inheritance": self._get_inheritance_section(file_path),
            "## Privacy Notice": self._get_privacy_notice(),
            "## Integration Points": self._get_integration_section(file_path),
        }
        
        # Add missing sections
        for section, content in standard_sections.items():
            if section not in enhanced_content and content:
                enhanced_content += f"\n\n{content}"
        
        # Extract and separate private information
        private_data = self._extract_private_info(enhanced_content)
        
        if private_data["has_private"]:
            # Create private context file
            private_path = self.claude_dir / "contexts" / "private" / f"{file_path.parent.name}.md"
            private_path.parent.mkdir(parents=True, exist_ok=True)
            
            private_content = self._create_private_context(file_path.parent.name, private_data["extracted"])
            private_path.write_text(private_content)
            
            # Update public file with references
            enhanced_content = private_data["public_content"]
            enhanced_content = enhanced_content.replace(
                "## Performance Metrics", 
                "## Performance Metrics\n_See private context for detailed metrics_\n"
            )
        
        # Ensure consistent formatting
        enhanced_content = self._standardize_formatting(enhanced_content)
        
        return {
            "enhanced": enhanced_content,
            "private_created": private_data["has_private"],
            "private_path": str(private_path) if private_data["has_private"] else None,
            "changes": self._get_changes_summary(original_content, enhanced_content)
        }
    
    def _get_inheritance_section(self, file_path: Path) -> str:
        """Generate context inheritance section"""
        relative_path = file_path.relative_to(self.workspace_root)
        agent_type = self._detect_agent_type(file_path)
        
        if not agent_type:
            return ""
        
        return f"""## Context Inheritance
- **Base Context**: `/.claude/contexts/base.md`
- **Agent Type**: {agent_type}
- **Scope**: {relative_path.parent}
- **Inherits From**: Root → Workspace → Agent"""
    
    def _get_privacy_notice(self) -> str:
        """Generate privacy notice section"""
        return """## Privacy Notice
This file contains only public, shareable information.
Private instance data is stored in `.claude/contexts/private/`"""
    
    def _get_integration_section(self, file_path: Path) -> str:
        """Generate integration points section"""
        agent_dir = file_path.parent
        sop_files = list(agent_dir.glob("sop/*.md"))
        
        if not sop_files:
            return ""
        
        integration = "## Integration Points\n"
        for sop in sop_files[:5]:  # Limit to 5 files
            integration += f"- `./sop/{sop.name}`\n"
        
        if len(sop_files) > 5:
            integration += f"- _...and {len(sop_files) - 5} more SOPs_\n"
        
        return integration
    
    def _extract_private_info(self, content: str) -> Dict:
        """Extract private information from content"""
        private_patterns = [
            (r'Agent ID.*?:\s*([^\n]+)', 'agent_id'),
            (r'Working Directory.*?:\s*([^\n]+)', 'working_dir'),
            (r'API.*?Key.*?:\s*([^\n]+)', 'api_key'),
            (r'Personal.*?:\s*([^\n]+)', 'personal'),
            (r'C:\\[^\s\n]+', 'absolute_path'),
            (r'/home/[^\s\n]+', 'home_path'),
        ]
        
        extracted = {}
        public_content = content
        has_private = False
        
        for pattern, key in private_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                has_private = True
                extracted[key] = matches
                # Replace with placeholder
                for match in set(matches):
                    public_content = public_content.replace(match, f"[See private context: {key}]")
        
        return {
            "has_private": has_private,
            "extracted": extracted,
            "public_content": public_content
        }
    
    def _create_private_context(self, agent_name: str, private_data: Dict) -> str:
        """Create private context file content"""
        content = f"""# Private Context for {agent_name}
_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}_

## Instance Configuration
"""
        
        for key, values in private_data.items():
            content += f"\n### {key.replace('_', ' ').title()}\n"
            for value in values:
                content += f"- {value}\n"
        
        content += "\n## Development Notes\n_Add your local development notes here_\n"
        
        return content
    
    def _standardize_formatting(self, content: str) -> str:
        """Ensure consistent markdown formatting"""
        # Fix heading spacing
        content = re.sub(r'\n#{1,6}\s+', lambda m: '\n' + m.group(0).strip() + '\n', content)
        
        # Fix list formatting
        content = re.sub(r'\n-\s+', '\n- ', content)
        
        # Remove trailing whitespace
        content = '\n'.join(line.rstrip() for line in content.split('\n'))
        
        # Ensure file ends with newline
        if not content.endswith('\n'):
            content += '\n'
        
        return content
    
    def _detect_agent_type(self, file_path: Path) -> Optional[str]:
        """Detect agent type from path"""
        path_str = str(file_path).lower()
        
        for agent_type in ['orchestrator', 'development', 'research', 'quality', 'architect']:
            if agent_type in path_str:
                return agent_type
        
        return None
    
    def _get_changes_summary(self, original: str, enhanced: str) -> List[str]:
        """Get summary of changes made"""
        changes = []
        
        if "## Context Inheritance" in enhanced and "## Context Inheritance" not in original:
            changes.append("Added context inheritance section")
        
        if "## Privacy Notice" in enhanced and "## Privacy Notice" not in original:
            changes.append("Added privacy notice")
        
        if "[See private context" in enhanced:
            changes.append("Extracted private information")
        
        if len(enhanced) != len(original):
            changes.append(f"Content size changed: {len(original)} → {len(enhanced)} chars")
        
        return changes

    def batch_enhance(self, dry_run: bool = True) -> List[Dict]:
        """Enhance all CLAUDE.md files in workspace"""
        results = []
        
        for claude_file in self.workspace_root.rglob("CLAUDE.md"):
            # Skip private directories
            if ".claude/contexts/private" in str(claude_file):
                continue
            
            print(f"\nProcessing: {claude_file.relative_to(self.workspace_root)}")
            
            result = self.enhance_claude_md(claude_file)
            result["file"] = str(claude_file.relative_to(self.workspace_root))
            
            if not dry_run and "enhanced" in result:
                # Backup original
                backup_path = claude_file.with_suffix(".md.bak")
                backup_path.write_text(claude_file.read_text())
                
                # Write enhanced version
                claude_file.write_text(result["enhanced"])
                print(f"  ✓ Enhanced and backed up to {backup_path.name}")
            else:
                print(f"  → Would make {len(result.get('changes', []))} changes")
            
            results.append(result)
        
        return results


# CLI Interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Claude Context Enhancement Tool")
    parser.add_argument("command", choices=["enhance", "batch", "check"])
    parser.add_argument("--file", help="Specific CLAUDE.md file to enhance")
    parser.add_argument("--workspace", default=".", help="Workspace root directory")
    parser.add_argument("--apply", action="store_true", help="Apply changes (default is dry-run)")
    
    args = parser.parse_args()
    
    enhancer = ContextEnhancer(args.workspace)
    
    if args.command == "enhance" and args.file:
        result = enhancer.enhance_claude_md(Path(args.file))
        print(json.dumps(result, indent=2))
        
        if args.apply and "enhanced" in result:
            Path(args.file).write_text(result["enhanced"])
            print(f"\nEnhanced content written to {args.file}")
    
    elif args.command == "batch":
        results = enhancer.batch_enhance(dry_run=not args.apply)
        print(f"\n\nProcessed {len(results)} files")
        
        if args.apply:
            print("Changes applied! Original files backed up with .bak extension")
    
    elif args.command == "check":
        # Just analyze without making changes
        results = enhancer.batch_enhance(dry_run=True)
        
        print("\n=== Enhancement Opportunities ===")
        for result in results:
            if result.get("changes"):
                print(f"\n{result['file']}:")
                for change in result["changes"]:
                    print(f"  - {change}")