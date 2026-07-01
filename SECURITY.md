# Security Scanning

## SAST (Static Analysis)
- Tool: Bandit
- Config: `.bandit.yml`
- Run: `cd backend && python -m bandit -c ../.bandit.yml -r app -ll`

## Dependency Scanning
- Tool: Safety
- Run: `pip list --format=freeze > requirements_full.txt && safety check -r requirements_full.txt`

## Secrets Scanning
- Recommendation: Install git-secrets or use pre-commit hooks
- Run: `git secrets --scan`

## CI/CD Integration
Security checks run automatically in GitHub Actions:
- `security-scan`: Bandit SAST scan
- `dependency-scan`: Safety vulnerability check
- `test-coverage`: Coverage threshold enforcement

## Reporting
Found a vulnerability? Contact: security@liankebao.top
