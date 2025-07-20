# File Organization Rules - Housekeeper Agent SOP

## Version Information
- **Version**: 1.0
- **Created**: 2025-07-20
- **Agent**: Housekeeper Agent (HOUSE-001)
- **Purpose**: Comprehensive file organization standards and procedures

---

## Core Organization Principles

### 1. Safety-First Philosophy
- **Data preservation is paramount**: Never risk data loss for organization
- **Approval before action**: Always request approval for operations affecting other agents
- **Backup before bulk operations**: Create recovery points for major changes
- **Dependency preservation**: Never break file references or import chains
- **Audit everything**: Maintain complete operation history for transparency

### 2. Intelligent Classification Standards
- **Content over extension**: Analyze file contents rather than relying solely on extensions
- **Context awareness**: Consider creator agent, creation time, and usage patterns
- **Purpose inference**: Determine file role in project structure through analysis
- **Relationship mapping**: Understand file dependencies and cross-references
- **Pattern recognition**: Learn from successful organization patterns

## Directory Structure Rules

### Primary Organization Hierarchy
```
project-root/
├── src/                          # Source code (organized by language/module)
│   ├── python/                   # Python source files
│   ├── javascript/               # JavaScript/TypeScript files
│   ├── shared/                   # Cross-language shared utilities
│   └── agents/                   # Agent-specific source code
├── tests/                        # Test files (mirror source structure)
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   └── e2e/                      # End-to-end tests
├── docs/                         # Documentation
│   ├── api/                      # API documentation
│   ├── user/                     # User guides
│   ├── dev/                      # Developer documentation
│   └── sop/                      # Standard Operating Procedures
├── config/                       # Configuration files
│   ├── environments/             # Environment-specific configs
│   ├── agents/                   # Agent-specific configurations
│   └── shared/                   # Shared configuration
├── data/                         # Data files
│   ├── raw/                      # Raw input data
│   ├── processed/                # Processed datasets
│   ├── temp/                     # Temporary data files
│   └── exports/                  # Generated data exports
├── scripts/                      # Executable scripts
│   ├── deployment/               # Deployment scripts
│   ├── maintenance/              # Maintenance utilities
│   └── development/              # Development helpers
├── logs/                         # Log files
│   ├── agents/                   # Agent-specific logs
│   ├── system/                   # System logs
│   └── archived/                 # Archived log files
├── artifacts/                    # Build outputs and generated files
│   ├── builds/                   # Compiled applications
│   ├── packages/                 # Distribution packages
│   └── reports/                  # Generated reports
├── temp/                         # Temporary files (auto-cleanup)
├── .recycle_bin/                # Housekeeper recycle bin
└── shared/                       # Shared resources
    ├── communication/            # Inter-agent communication
    ├── memory/                   # Collective memory
    ├── standards/                # Standards and protocols
    ├── resources/                # Shared resources
    └── tools/                    # Shared utilities
```

### Agent-Specific Directory Structure
```
agents/agent-{specialty}/
├── .agent-config.json           # Agent configuration
├── CLAUDE.md                    # Agent memory and context
├── .cursorrules                 # Agent-specific rules
├── commands/                    # Custom commands
├── sop/                         # Standard Operating Procedures
├── templates/                   # Code/output templates
├── knowledge/                   # Domain knowledge
├── validation/                  # Quality assurance
├── learning/                    # Continuous improvement
├── responsibilities/            # Role-specific dirs (for meta-agents)
├── capabilities/                # Capability-specific dirs
└── work/                        # Active work directory
    ├── current/                 # Current tasks
    ├── completed/               # Completed work
    └── drafts/                  # Work in progress
```

## File Classification and Placement Rules

### 1. Source Code Files

#### Python Files (`.py`)
- **Location**: `src/python/{module}/` or `agents/agent-{name}/`
- **Naming**: `snake_case.py` or `PascalCase.py` for classes
- **Classification criteria**:
  - Contains `import` statements for Python modules
  - Has Python syntax and structure
  - Contains function or class definitions

#### JavaScript/TypeScript Files (`.js`, `.ts`, `.jsx`, `.tsx`)
- **Location**: `src/javascript/{module}/` or frontend-specific directories
- **Naming**: `camelCase.js`, `PascalCase.tsx` for React components
- **Classification criteria**:
  - Contains JavaScript/TypeScript syntax
  - Has `import`/`require` statements for JS modules
  - Contains function, class, or component definitions

#### Configuration Files (`.json`, `.yaml`, `.yml`, `.toml`, `.*rc`)
- **Location**: `config/{category}/` or agent-specific config directories
- **Naming**: `lowercase-with-hyphens.yaml`
- **Classification criteria**:
  - Contains configuration key-value pairs
  - Referenced by other files or applications
  - Has configuration-specific file extensions

### 2. Documentation Files

#### Markdown Files (`.md`)
- **Location**: `docs/{category}/` or agent-specific documentation
- **Naming**: `CLEAR_DESCRIPTIVE_NAMES.md`
- **Classification criteria**:
  - Contains markdown syntax
  - Has documentation-style content structure
  - Referenced as documentation by other files

#### API Documentation
- **Location**: `docs/api/{service}/`
- **Naming**: `{service}_api.md` or `{endpoint}_spec.md`
- **Classification criteria**:
  - Contains API endpoint descriptions
  - Has request/response examples
  - References HTTP methods and status codes

### 3. Test Files

#### Python Tests
- **Location**: `tests/{type}/` mirroring source structure
- **Naming**: `test_{functionality}.py`
- **Classification criteria**:
  - Contains `test_` prefixed functions
  - Imports testing frameworks (pytest, unittest)
  - Located in test directories or named with test patterns

#### JavaScript Tests
- **Location**: `tests/{type}/` mirroring source structure
- **Naming**: `{functionality}.test.js` or `{functionality}.spec.ts`
- **Classification criteria**:
  - Contains test framework imports (Jest, Mocha, etc.)
  - Has test/describe/it function calls
  - Follows test file naming patterns

### 4. Data Files

#### Raw Data
- **Location**: `data/raw/{source}/`
- **Naming**: `{dataset}_{YYYYMMDD}.{ext}`
- **Classification criteria**:
  - Contains structured data (CSV, JSON, XML)
  - No processing or transformation applied
  - Referenced by data processing scripts

#### Processed Data
- **Location**: `data/processed/{type}/`
- **Naming**: `{dataset}_processed_{YYYYMMDD}.{ext}`
- **Classification criteria**:
  - Contains transformed or cleaned data
  - Generated by processing scripts
  - Used as input for analysis or applications

### 5. Temporary and Generated Files

#### Temporary Files
- **Location**: `temp/`
- **Auto-cleanup**: Files older than 24 hours
- **Patterns**: `*.tmp`, `*.temp`, `~*`, `.~*`
- **Classification criteria**:
  - Has temporary file extensions
  - Created by applications as working files
  - No references from other permanent files

#### Build Artifacts
- **Location**: `artifacts/{type}/`
- **Naming**: `{name}_v{version}_{platform}.{ext}`
- **Classification criteria**:
  - Generated by build processes
  - Has executable or library file extensions
  - Located in build output directories

## Naming Convention Standards

### General Naming Rules
1. **No spaces**: Use underscores, hyphens, or camelCase
2. **Descriptive names**: File purpose should be clear from name
3. **Consistent patterns**: Follow established patterns within categories
4. **Version indicators**: Include version numbers for releases
5. **Date stamps**: Include dates for time-sensitive files

### Specific Conventions

#### Source Code
- **Python**: `snake_case.py`, `PascalCase.py` for classes
- **JavaScript**: `camelCase.js`, `PascalCase.jsx` for components
- **TypeScript**: `camelCase.ts`, `PascalCase.tsx` for components
- **Constants**: `UPPER_SNAKE_CASE.py`

#### Documentation
- **General**: `DESCRIPTIVE_NAME.md`
- **API docs**: `{service}_api.md`
- **SOPs**: `{topic}-sop.md`
- **Guides**: `{topic}-guide.md`

#### Configuration
- **Environment**: `{env}-config.yaml`
- **Agent config**: `{agent}-config.json`
- **Service config**: `{service}.config.{ext}`

#### Scripts
- **Deployment**: `deploy_{target}.sh`
- **Maintenance**: `cleanup_{task}.py`
- **Development**: `dev_{purpose}.sh`

#### Data Files
- **Raw**: `{source}_raw_{YYYYMMDD}.{ext}`
- **Processed**: `{dataset}_processed_{YYYYMMDD}.{ext}`
- **Exports**: `{report}_export_{YYYYMMDD}.{ext}`

## File Placement Decision Algorithm

### Step 1: Content Analysis
```python
def analyze_file_content(filepath):
    content_indicators = {
        'imports': extract_import_statements(filepath),
        'syntax': detect_programming_language(filepath),
        'keywords': extract_domain_keywords(filepath),
        'structure': analyze_file_structure(filepath),
        'references': find_external_references(filepath)
    }
    return content_indicators
```

### Step 2: Context Analysis
```python
def analyze_creation_context(filepath):
    context = {
        'creator_agent': identify_creator_agent(filepath),
        'creation_time': get_creation_timestamp(filepath),
        'file_size': get_file_size(filepath),
        'modification_pattern': analyze_modification_history(filepath),
        'access_pattern': analyze_access_history(filepath)
    }
    return context
```

### Step 3: Relationship Analysis
```python
def analyze_file_relationships(filepath):
    relationships = {
        'dependencies': find_files_this_depends_on(filepath),
        'dependents': find_files_depending_on_this(filepath),
        'related_files': find_similar_purpose_files(filepath),
        'project_role': determine_role_in_project(filepath)
    }
    return relationships
```

### Step 4: Placement Decision
```python
def determine_optimal_placement(filepath):
    content = analyze_file_content(filepath)
    context = analyze_creation_context(filepath)
    relationships = analyze_file_relationships(filepath)
    
    placement_scores = {}
    
    for potential_location in get_possible_locations():
        score = calculate_placement_score(
            potential_location, content, context, relationships
        )
        placement_scores[potential_location] = score
    
    best_location = max(placement_scores, key=placement_scores.get)
    confidence = placement_scores[best_location]
    
    return {
        'recommended_location': best_location,
        'confidence': confidence,
        'reasoning': generate_placement_reasoning(
            best_location, content, context, relationships
        ),
        'alternatives': get_alternative_locations(placement_scores)
    }
```

## Garbage Detection Rules

### Automatic Cleanup Categories

#### 1. Temporary Files
- **Patterns**: `*.tmp`, `*.temp`, `~*`, `.~*`, `*.swp`
- **Age threshold**: 24 hours
- **Approval required**: No (automatic)
- **Action**: Move to recycle bin

#### 2. Empty Files
- **Condition**: File size == 0 bytes
- **Age threshold**: 1 hour
- **Approval required**: Yes (if recently created)
- **Action**: Move to recycle bin

#### 3. Build Artifacts (Outside Build Directories)
- **Patterns**: `*.o`, `*.pyc`, `__pycache__/`, `*.class`, `*.exe` (in wrong locations)
- **Condition**: Not in designated artifact directories
- **Approval required**: No (automatic cleanup)
- **Action**: Move to proper artifact directory or recycle bin

#### 4. Duplicate Files
- **Detection**: Identical file hashes
- **Selection criteria**: Keep file in better location or with better name
- **Approval required**: Yes (for manual review)
- **Action**: Move duplicates to recycle bin

#### 5. Outdated Backups
- **Patterns**: `*.backup`, `*.bak`, `*.old`
- **Age threshold**: 7 days
- **Approval required**: Yes
- **Action**: Move to recycle bin

### Manual Review Categories

#### 1. Large Files
- **Threshold**: Files > 10MB
- **Action**: Always require human or OA approval
- **Analysis**: Provide usage analysis and space impact

#### 2. Recently Modified Files
- **Threshold**: Modified within last hour
- **Action**: Never suggest for cleanup without explicit approval
- **Exception**: Known temporary file patterns

#### 3. Referenced Files
- **Condition**: File is imported or referenced by other files
- **Action**: Never suggest for deletion
- **Analysis**: Provide dependency impact analysis

## Approval Workflows

### Automatic Approval (No Review Required)
- Moving files to correct locations within same category
- Fixing naming convention violations
- Cleaning up confirmed temporary files
- Removing empty directories after file moves
- Creating missing directories for proper organization

### Orchestrator Agent Approval Required
- Deleting or moving files over 1MB
- Operations affecting multiple agents' workspaces
- Bulk cleanup operations (>10 files)
- Creating new top-level directories
- Moving files that might break dependencies

### Human Approval Required
- Deleting files with uncertain purpose
- Major directory restructuring
- Cleanup operations with low confidence scores
- Operations affecting critical system files
- Any operation flagged as high-risk by dependency analysis

## Safety Protocols

### Pre-Operation Safety Checks
1. **Dependency Analysis**: Verify no other files will be broken
2. **Size Verification**: Check file size against approval thresholds
3. **Age Verification**: Ensure file is not too recently created/modified
4. **Reference Check**: Confirm file is not referenced by active processes
5. **Backup Verification**: Ensure backup exists for critical operations

### Operation Safety Measures
1. **Atomic Operations**: All operations are transaction-safe
2. **Progress Logging**: Real-time logging of operation steps
3. **Rollback Capability**: Ability to reverse any operation
4. **Error Handling**: Graceful failure with automatic rollback
5. **Verification**: Post-operation verification of success

### Post-Operation Validation
1. **Integrity Check**: Verify all files are accessible and uncorrupted
2. **Reference Update**: Update any internal references if needed
3. **Audit Logging**: Complete operation audit trail
4. **Performance Impact**: Monitor for any negative performance effects
5. **Agent Notification**: Inform affected agents of changes

## Monitoring and Reporting

### Real-Time Monitoring
- File system event monitoring with immediate response
- Continuous directory structure validation
- Real-time dependency analysis for new files
- Automatic placement suggestion generation
- Live workspace health assessment

### Daily Reports
- Files organized and moved
- Space recovered through cleanup
- Naming violations corrected
- Approval requests pending
- System health metrics

### Weekly Analysis
- Organization pattern effectiveness
- Agent workspace evolution
- Cleanup efficiency metrics
- Approval workflow analysis
- Optimization opportunities identified

---

**Implementation Priority**: CRITICAL - All file operations must follow these rules  
**Quality Standard**: 99%+ accuracy in file placement and safety  
**Safety Requirement**: Zero data loss tolerance with complete audit trails  
**Approval Integration**: Seamless workflow with Orchestrator Agent for critical decisions