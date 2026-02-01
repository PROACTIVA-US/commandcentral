---
status: active
name: damage-control
description: Implement safety hooks to prevent destructive commands in agentic AI
  workflows. Use when running autonomous agents, configuring Claude Code hooks, or
  setting up guardrails for long-running executions.
category: safety
keywords:
- safety
- hooks
- protection
- destructive
- guardrails
- permissions
contract:
  version: '1.0'
  inputs:
    required:
    - name: task_description
      type: string
      description: Description of the task to perform
    optional: []
  outputs:
  - name: result
    type: object
    properties:
      success:
        type: boolean
      summary:
        type: string
  errors:
  - code: SKILL_EXECUTION_FAILED
    description: Skill execution encountered an error
    recoverable: true
  side_effects:
  - type: file_write
    description: May modify files
  - type: git_commit
    description: May create git commits
  - type: api_call
    description: May call external APIs
  - type: database_write
    description: May modify database
  auth_scopes:
  - scope: file:write
    required: true
  - scope: git:commit
    required: false
  timeouts:
    default_ms: 30000
    max_ms: 180000
---
# Damage Control

Prevent catastrophic, irreversible, career-impacting consequences from agentic AI execution.

## Why This Matters

A single incorrect command can destroy months of work:
- `rm -rf /` - Wipe filesystem
- `git push --force origin main` - Destroy git history
- `DROP DATABASE production;` - Delete production data

Agentic AI can hallucinate or misinterpret prompts. This skill provides the safety net.

## Protection Mechanisms

### 1. Deterministic Command Blocking

Block known high-risk commands with regex patterns. **Primary defense** - instant, reliable.

```yaml
# patterns.yaml
bash_tool_patterns:
  - 'rm\s+-rf\s+/'              # Recursive delete from root
  - 'rm\s+-rf\s+\*'             # Recursive delete all
  - 'git\s+push\s+--force'      # Force push (destroys history)
  - 'git\s+reset\s+--hard'      # Hard reset (loses commits)
  - 'DROP\s+DATABASE'           # Database deletion
  - 'DROP\s+TABLE'              # Table deletion
  - 'truncate\s+table'          # Table truncation
  - ':(){:|:&};:'               # Fork bomb
```

### 2. "Ask Permission" Patterns

Prompt for confirmation before sensitive-but-not-always-destructive commands.

```yaml
# patterns.yaml
bash_tool_patterns:
  - pattern: 'psql.*DROP'
    ask: true
  - pattern: 'npm publish'
    ask: true
  - pattern: 'docker.*--rm'
    ask: true
  - pattern: 'kubectl delete'
    ask: true
```

### 3. Path Protection

Granular access control for files and directories.

| Level | Meaning | Use For |
|-------|---------|---------|
| `zero_access` | No read, write, or list | `.ssh/`, `.aws/`, `.git/` |
| `read_only` | Read but never modify | `settings.json`, `patterns.yaml`, config files |
| `no_delete` | Can modify but never delete | Production builds, database schemas, logs |

```yaml
# patterns.yaml
path_protections:
  zero_access:
    - '.ssh/'
    - '.aws/'
    - '.git/'
    - '.env'
    - 'secrets/'

  read_only:
    - 'settings.json'
    - 'patterns.yaml'
    - 'docker-compose.prod.yml'
    - 'infrastructure/'

  no_delete:
    - 'dist/'
    - 'build/'
    - 'migrations/'
    - 'backups/'
```

## Hook Types

### Deterministic Hooks (Primary)

- Uses predefined regex patterns
- Instant blocking - no latency
- Absolute effectiveness for known threats
- Depends on patterns being explicitly defined

### Prompt Hooks (Secondary)

- AI evaluates every bash command for potential harm
- Catches novel/unknown destructive patterns
- **Trade-off**: Adds latency to every command
- Last-ditch effort, not primary defense

```json
// settings.json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Is this command potentially destructive? If yes, block it."
          }
        ]
      }
    ]
  }
}
```

## Hook Hierarchy

Hooks merge from general to specific, with specific taking precedence:

```
Enterprise (org-level, non-overridable)
    └── Global (User) - applies to ALL projects
        └── Project - codebase-specific rules
            └── Local - session-specific
```

**Best Practice**: Always have robust Global hooks. They protect even unconfigured projects.

## Installation

### Quick Start

```bash
# Create damage control config directory
mkdir -p .claude/hooks

# Create patterns.yaml with baseline protections
cat > .claude/patterns.yaml << 'EOF'
bash_tool_patterns:
  # Filesystem destruction
  - 'rm\s+-rf\s+/'
  - 'rm\s+-rf\s+\*'
  - 'rm\s+-rf\s+~'

  # Git history destruction
  - 'git\s+push\s+--force'
  - 'git\s+reset\s+--hard'
  - 'git\s+clean\s+-fd'

  # Database destruction
  - 'DROP\s+DATABASE'
  - 'DROP\s+TABLE'
  - 'TRUNCATE\s+TABLE'

  # Ask permission patterns
  - pattern: 'npm\s+publish'
    ask: true
  - pattern: 'docker\s+push'
    ask: true

path_protections:
  zero_access:
    - '.ssh/'
    - '.aws/'
    - '.env'
  read_only:
    - 'settings.json'
    - 'patterns.yaml'
  no_delete:
    - 'migrations/'
EOF
```

### Verify Protections

```bash
# In Claude Code
Use the damage control skill and list all damage controls
```

## Operational Procedures

### When "Ask Permission" Triggers

Agent pauses and asks:
```
The command `npm publish` matches a protected pattern.
Do you want to proceed? (yes/skip)
```

- `yes` - Execute the command
- `skip` - Block and continue

### When Command is Blocked

Agent outputs:
```
BLOCKED: Command matches destructive pattern 'rm -rf /'
This command cannot be executed.
```

No user override possible for deterministic blocks.

## Customization by Project Type

### Web Application

```yaml
path_protections:
  zero_access:
    - '.env.production'
    - 'secrets/'
  no_delete:
    - 'public/'
    - 'dist/'
    - 'node_modules/'  # Expensive to recreate
```

### Database Project

```yaml
bash_tool_patterns:
  - pattern: 'psql.*-c.*DELETE'
    ask: true
  - pattern: 'mysql.*DROP'
    ask: true

path_protections:
  no_delete:
    - 'migrations/'
    - 'seeds/'
    - 'schemas/'
```

### Infrastructure/DevOps

```yaml
bash_tool_patterns:
  - 'terraform\s+destroy'
  - 'kubectl\s+delete\s+namespace'
  - pattern: 'kubectl\s+apply'
    ask: true

path_protections:
  read_only:
    - 'terraform/'
    - 'kubernetes/'
    - 'ansible/'
```

## Integration with Autonomous Execution

When running long-running agents (Ralph loops, parallel batch execution):

### Pre-Execution Checklist

- [ ] Damage control hooks installed
- [ ] Global patterns cover destructive commands
- [ ] Project-specific paths protected
- [ ] Production credentials in `zero_access` paths
- [ ] `--dangerously-skip-permissions` NOT used without damage control

### Monitoring During Execution

Watch for:
- Blocked command notifications
- "Ask permission" prompts that pile up
- Repeated attempts to access protected paths

### Post-Execution Audit

```bash
# Review what damage control blocked
grep "BLOCKED:" .claude/logs/*.log

# Review permission requests
grep "ask:" .claude/logs/*.log
```

## Common Mistakes

### 1. Relying Only on Prompt Hooks

Prompt hooks are probabilistic. They can miss novel attacks or have false negatives.
**Always** have deterministic patterns for known threats.

### 2. No Global Hooks

Without global hooks, new projects have no protection until configured.
**Always** install baseline global hooks.

### 3. Protecting Wrong Paths

Don't protect paths the agent legitimately needs to modify.
Be precise: protect `.env` but not `.env.example`.

### 4. Forgetting Database CLIs

`psql`, `mysql`, `mongo` commands can be destructive.
Add patterns for your project's database CLI.

### 5. Not Updating Patterns

As you discover new dangerous patterns, add them.
Damage control is living documentation.

## Troubleshooting

### Hook Not Triggering

1. Check pattern syntax (regex)
2. Verify settings.json is valid JSON
3. Restart Claude Code after changes
4. Check hook level (Global vs Project vs Local)

### Too Many False Positives

1. Make patterns more specific
2. Use `ask: true` instead of blocking
3. Exclude safe variants explicitly

### Agent Circumventing Hooks

If agent tries alternative commands to achieve blocked goal:
1. Add variants to patterns
2. Use path protection as backup
3. Consider `zero_access` for critical paths

## Related Skills

| Skill | Relationship |
|-------|--------------|
| `autonomy` | Ralph loops need damage control hooks |
| `agent-native-architecture` | Agent-native doesn't mean unsafe |
| `repository-hygiene` | Git safety patterns overlap |

---

*A single incorrect command can destroy months of work. Protect everything.*
