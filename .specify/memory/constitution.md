<!--
Sync Impact Report:
- Version change: Template → 1.0.0
- Modified principles: All principles newly defined from CLAUDE.md
- Added sections:
  * Core Principles (6 principles defined)
  * Development Workflow Standards
  * Code Quality Requirements
  * Governance
- Templates requiring updates:
  ✅ constitution.md - updated
  ⚠ plan-template.md - requires review for TDD/quality gate alignment
  ⚠ spec-template.md - requires review for mandatory sections
  ⚠ tasks-template.md - requires review for principle-driven categorization
- Follow-up TODOs: None - all placeholders filled
-->

# Agent Leaderboard Constitution

## Core Principles

### I. Test-Driven Development (NON-NEGOTIABLE)

**Rules:**
- Unit tests MUST be created before implementation
- Tests MUST be approved by the user before implementation begins
- Implementation MUST follow Red-Green-Refactor cycle:
  1. Write test (Red phase - test fails)
  2. Implement feature (Green phase - test passes)
  3. Refactor if needed
- One feature MUST correspond to one test file
- Test file names MUST clearly reflect the feature being tested (e.g., `test_calculator.py` for `calculator.py`)

**Rationale:** TDD ensures correctness from the start, provides living documentation, and prevents regression. This discipline is non-negotiable to maintain code quality and confidence.

### II. Code-Specification Consistency

**Rules:**
- Specifications MUST be reviewed before implementation
- If specifications are ambiguous, implementation MUST halt and clarification MUST be requested
- Documentation changes REQUIRE user approval before implementation
- Implementation MAY only begin after specification updates are complete

**Rationale:** Maintaining alignment between code and documentation prevents drift, ensures shared understanding, and reduces rework.

### III. Code Quality Standards

**Rules:**
- Linter, formatter, and type checker MUST be run before every commit
- All errors MUST be resolved before committing
- Time constraints SHALL NOT be used as justification for quality compromises
- All functions, methods, and variables MUST have type annotations
- `Any` type usage is DISCOURAGED; specific types MUST be preferred
- Type errors MUST be resolved, not ignored

**Rationale:** Consistent quality standards ensure maintainability, reduce bugs, and improve collaboration. Automated tools catch issues before they reach production.

### IV. Data Accuracy

**Rules:**
- Magic numbers and fixed strings MUST NOT be embedded directly in code
- Environment-dependent values MUST NOT be hard-coded
- Credentials and API keys MUST NOT be stored in code
- Default value assignment on data fetch failure is FORBIDDEN
- Value generation based on guesses is FORBIDDEN
- All fixed values MUST be defined as named constants
- Configuration values MUST be centrally managed in dedicated configuration modules
- Environment-specific values MUST be managed via environment variables or configuration files
- Errors MUST be handled explicitly (raise exceptions)

**Rationale:** Explicit data management ensures traceability, prevents silent failures, and improves security. Guessed or implicit values create hidden bugs and security vulnerabilities.

### V. DRY (Don't Repeat Yourself)

**Rules:**
- Existing implementations MUST be searched and confirmed before creating new ones (using Glob, Grep tools)
- Similar functionality MUST be identified and reused
- Patterns repeated 3+ times MUST be extracted into functions or modules
- Identical logic MUST be consolidated
- When duplication is detected:
  1. Work MUST be paused
  2. Existing implementation extensibility MUST be evaluated
  3. Refactoring plan MUST be created

**Rationale:** Code duplication increases maintenance burden, introduces inconsistency, and multiplies bug-fixing effort. Consolidation improves maintainability and reduces errors.

### VI. Refactoring Policy

**Rules:**
- Existing code MUST be modified directly; versioned classes (V2, V3) MUST NOT be created
- Design correctness SHALL take priority over backward compatibility
- Before refactoring:
  1. Impact scope MUST be identified (dependency analysis)
  2. Test coverage MUST be verified
  3. Documentation update plan MUST be created

**Rationale:** Direct modification keeps the codebase clean and prevents proliferation of legacy variants. Proper analysis minimizes risk while enabling continuous improvement.

## Development Workflow Standards

### Package Management
- **Package Manager:** uv
- Dependency installation: `uv sync`
- Development dependencies: `uv add <package> --dev`
- Documentation dependencies: `uv add <package> --group docs`

### Testing Protocol
- **Test Framework:** pytest
- Run all tests: `pytest`
- Run specific test file: `pytest tests/path/to/test_file.py`
- Verbose output: `pytest -v`

### Code Quality Tools
- **Linter:** ruff
- **Type Checker:** mypy
- **Formatter:** ruff (format mode)
- Pre-commit check: `ruff check . && ruff format . && mypy .`

### Code Style Standards
- **Naming Conventions:**
  - Classes: PascalCase
  - Functions/Variables: snake_case
  - Constants: UPPER_SNAKE_CASE
- **Docstrings:** Google-style format
- **Type Hints:** Required for all public APIs
- **Import Order:** stdlib → third-party → local (auto-sorted by tools)
- **Line Length:** Enforced by ruff configuration in pyproject.toml

### Documentation Requirements
- Public functions, classes, and modules MUST have comprehensive docstrings
- Google-style docstring format MUST be used
- Docstrings MUST align with type annotations
- Complex functions MUST include usage examples
- Documentation location: `docs/*.md`
- Documentation system: Sphinx with RTD theme
- Build command: `make html` (in docs/ directory)

### Testing Strategy
- **Unit Tests:** Fast, no external dependencies (use mocks)
- **Integration Tests:** Moderate speed, mock external services
- **E2E Tests:** Use real external services, mark appropriately
- **Test Markers:** Use pytest markers to indicate test types and dependencies

## Code Quality Requirements

All code MUST pass the following gates before commit:

1. **Type Checking:** `mypy .` with zero errors
2. **Linting:** `ruff check .` with zero violations
3. **Formatting:** `ruff format .` applied
4. **Testing:** All tests passing

Configuration for all tools MUST be maintained in `pyproject.toml`.

## Governance

### Amendment Process
1. Proposed changes MUST be documented with rationale
2. Changes MUST be approved before adoption
3. Version bump MUST follow semantic versioning:
   - **MAJOR:** Backward-incompatible governance/principle removals or redefinitions
   - **MINOR:** New principle/section added or materially expanded guidance
   - **PATCH:** Clarifications, wording, typo fixes, non-semantic refinements

### Compliance Review
- All pull requests MUST verify constitutional compliance
- Complexity MUST be justified against principles
- Constitutional violations MUST be rejected or escalated

### Runtime Guidance
- Developers SHOULD refer to `CLAUDE.md` for detailed runtime development guidance
- This constitution supersedes all other development practices when conflicts arise

**Version**: 1.0.0 | **Ratified**: 2025-10-31 | **Last Amended**: 2025-10-31
