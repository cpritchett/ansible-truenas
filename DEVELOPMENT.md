# Development Workflow

This fork uses a **dual validation strategy** to maintain both upstream compatibility and industry-standard testing practices.

## Quick Start

```bash
# Complete validation
./scripts/validate.sh

# Quick upstream validation
make lint && make check-docs

# Full development validation  
make -f Makefile.dev dev-validate
```

## Validation Approaches

### Upstream Compatible
- `make lint` - Python syntax validation
- `make check-docs` - Documentation validation  
- `make tarball` - Collection build test

### Industry Standard (Your Fork)
- `make -f Makefile.dev sanity-test` - ansible-test sanity
- `make -f Makefile.dev unit-test` - pytest unit tests
- `make -f Makefile.dev integration-test-syntax` - Integration test syntax
- `make -f Makefile.dev example-syntax` - Example playbook syntax

## Branch Strategy

- `feat/incus-support` - Clean branch for upstream PRs
- `development` - Your development branch with full testing

## Contributing to Upstream

### 1. Ensure Clean State
```bash
# Validate with both approaches
./scripts/validate.sh

# Check git status (mise files excluded automatically)
git status
```

### 2. Create PR
- Push from `feat/incus-support` branch
- Include both validations in PR description
- No testing infrastructure gets sent upstream

### 3. PR Description Template
```markdown
## Add TrueNAS Incus Container Support

**Modules Added:**
- `truenas_incus_instance`: Manage Incus containers/VMs  
- `truenas_incus_exec`: Execute commands in containers
- `rest_api`: New module_utils for HTTP API calls

**Validation:**
- ✅ `make lint` passes (upstream)
- ✅ `make check-docs` passes (upstream)  
- ✅ `ansible-test sanity` passes (development)
- ✅ Unit tests pass (development)
- ✅ Integration test syntax valid (development)
- ✅ Example syntax valid (development)

No changes to existing build/test infrastructure.
```

## File Exclusions

The following files are automatically excluded from upstream PRs:

- `.mise.toml`, `.mise/` - mise tooling
- `.venv/`, `.vscode/` - development environment  
- `requirements.lock` - lock file
- `tests/output/` - test artifacts
- `Makefile.dev` - development Makefile
- `scripts/validate.sh` - validation script
- `.github/workflows/sanity.yml` - GitHub Actions

## Automated Testing

GitHub Actions run on pushes to `development` and `feat/incus-support`:

- **Upstream Validation** - lint and doc checks
- **Ansible-Test Validation** - sanity tests  
- **Unit Tests** - pytest execution
- **Syntax Validation** - integration/example syntax
- **Collection Build** - tarball creation test

## Pre-commit Hook

Automatically runs basic validation before each commit:
- `make lint` 
- `make check-docs`

For full validation, manually run `./scripts/validate.sh`.

## Tips

- **Daily development**: Work in `development` branch
- **Upstream PRs**: Use `feat/incus-support` branch  
- **Quick validation**: `make lint && make check-docs`
- **Full validation**: `./scripts/validate.sh`
- **Clean slate**: `make -f Makefile.dev clean`