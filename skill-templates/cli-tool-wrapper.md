# CLI Tool Wrapper Template

For wrapping command-line tools like git, docker, gh, kubectl, etc. Provides higher-level automation around existing CLI tools.

## Template Files

### SKILL.md
```markdown
---
name: your-tool
description: "Interact with YourTool using the CLI. Brief description of automation capabilities."
metadata:
  {
    "openclaw":
      {
        "emoji": "🛠️",
        "requires": { "bins": ["your-tool"] },
        "install":
          [
            {
              "id": "brew",
              "kind": "brew",
              "formula": "your-tool",
              "bins": ["your-tool"],
              "label": "Install YourTool (brew)",
            },
            {
              "id": "apt",
              "kind": "apt",
              "package": "your-tool",
              "bins": ["your-tool"],
              "label": "Install YourTool (apt)",
            },
          ],
      },
  }
---

# YourTool Skill

Use the `your-tool` CLI to automate common workflows. Always specify required context (workspace, project, etc.) when not in the expected directory.

## Common Operations

### List items
```bash
your-tool list --format json | jq '.[] | select(.status == "active")'
```

### Create/Update
```bash
your-tool create --name "example" --config /path/to/config
```

### Status checking
```bash
your-tool status --id "example-123"
```

## Advanced Workflows

### Batch operations
```bash
# Process multiple items
your-tool list --status pending --json | jq -r '.[].id' | while read id; do
  your-tool process "$id"
done
```

### Conditional logic
```bash
# Only proceed if certain conditions are met
if your-tool check --name "example" >/dev/null 2>&1; then
  your-tool deploy --name "example"
else
  echo "Prerequisites not met"
fi
```

## JSON Output and Filtering

Most modern CLI tools support `--json` output. Use `jq` for filtering:

```bash
your-tool list --json | jq '.[] | "\(.id): \(.name) (\(.status))"'
```

## Error Handling

Common exit codes and meanings:
- 0: Success
- 1: General error
- 2: Misuse (invalid arguments)
- 130: Interrupted by user (Ctrl+C)

## Context and Authentication

Document how to handle:
- Working directories
- Configuration files
- Authentication tokens/keys
- Environment variables
```

### scripts/main.sh
```bash
#!/bin/bash
set -euo pipefail

# Main entry point for YourTool automation
# Usage: ./main.sh <operation> [args...]

operation=${1:-help}
shift || true

case $operation in
  "status")
    # Check overall system status
    your-tool status --summary
    ;;
  "deploy")
    # Deploy with safety checks
    project=${1?"Project name required"}
    if your-tool validate --project "$project"; then
      your-tool deploy --project "$project" --confirm
    else
      echo "Validation failed for project: $project"
      exit 1
    fi
    ;;
  "cleanup")
    # Safe cleanup operation
    echo "Finding unused resources..."
    your-tool list --unused | while read resource; do
      echo "Would delete: $resource"
      # Add --dry-run flag in real implementation
    done
    ;;
  "help")
    echo "Usage: $0 {status|deploy|cleanup}"
    echo "  status      - Check system status"
    echo "  deploy      - Deploy a project (requires project name)"
    echo "  cleanup     - Clean up unused resources"
    ;;
  *)
    echo "Unknown operation: $operation"
    exit 1
    ;;
esac
```

### scripts/helpers/validate.sh
```bash
#!/bin/bash
# Validation helper functions

validate_tool_installed() {
  if ! command -v your-tool >/dev/null 2>&1; then
    echo "Error: your-tool is not installed"
    echo "Install with: brew install your-tool"
    return 1
  fi
}

validate_config() {
  local config_path=${1?"Config path required"}
  
  if [[ ! -f "$config_path" ]]; then
    echo "Error: Config file not found: $config_path"
    return 1
  fi
  
  # Validate config syntax if tool supports it
  if ! your-tool config validate "$config_path"; then
    echo "Error: Invalid config file: $config_path"
    return 1
  fi
}

validate_credentials() {
  if ! your-tool auth check >/dev/null 2>&1; then
    echo "Error: Not authenticated"
    echo "Run: your-tool auth login"
    return 1
  fi
}
```

## Example Implementation

Based on the GitHub CLI pattern:

```markdown
---
name: docker-ops
description: "Docker operations and container management using the docker CLI."
metadata:
  {
    "openclaw":
      {
        "emoji": "🐳",
        "requires": { "bins": ["docker"] },
        "install":
          [
            {
              "id": "brew",
              "kind": "brew",
              "cask": "docker",
              "bins": ["docker"],
              "label": "Install Docker Desktop (brew)",
            }
          ],
      },
  }
---

# Docker Operations

Automate Docker container and image management workflows.

## Container Management

### List running containers with custom format
```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### Health check all services
```bash
docker ps --format "{{.Names}}" | xargs -I {} docker exec {} sh -c "curl -f http://localhost:8080/health || echo 'Health check failed for {}'"
```

### Logs from multiple containers
```bash
# Follow logs from all app containers
docker ps --filter "name=app-*" --format "{{.Names}}" | xargs -I {} docker logs -f {} &
```

## Image Operations

### Clean up unused images
```bash
# Show what would be removed
docker image prune --filter "until=24h" --dry-run

# Actually remove
docker image prune --filter "until=24h" -f
```

### Build with proper tagging
```bash
# Build and tag with git commit
tag=$(git rev-parse --short HEAD)
docker build -t "myapp:$tag" -t "myapp:latest" .
```

## Compose Operations

### Scale services based on load
```bash
# Check current replicas
docker-compose ps

# Scale up web service
docker-compose up -d --scale web=3
```

### Rolling updates
```bash
# Update service without downtime
docker-compose pull service-name
docker-compose up -d --no-deps service-name
```

## JSON Output for Automation

```bash
# Get container info as JSON
docker inspect container-name | jq '.[0].State'

# List images with size info
docker images --format "{{json .}}" | jq '.Repository + ":" + .Tag + " (" + .Size + ")"'
```
```

## Customization Checklist

- [ ] Replace `your-tool` with actual CLI tool name
- [ ] Update installation methods (brew, apt, snap, etc.)
- [ ] Document authentication/configuration requirements
- [ ] Add tool-specific operations and workflows
- [ ] Include JSON output examples if supported
- [ ] Add safety checks for destructive operations
- [ ] Test all examples on actual tool
- [ ] Document common error scenarios

## Dependencies

- Target CLI tool (with version requirements)
- `jq` for JSON processing (if needed)
- `bash` with standard utilities (`grep`, `awk`, `sed`)

## Safety Guidelines

1. **Dry Run Mode**: Always support `--dry-run` for destructive operations
2. **Confirmation**: Ask for confirmation on irreversible actions
3. **Backup**: Suggest backup procedures before major changes
4. **Validation**: Validate inputs and prerequisites before execution
5. **Logging**: Log all operations for audit trails
6. **Rollback**: Document rollback procedures for failed operations