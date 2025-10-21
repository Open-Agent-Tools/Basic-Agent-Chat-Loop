# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Currently supported versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

We take the security of Basic Agent Chat Loop seriously. If you discover a security vulnerability, please follow these steps:

### Where to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via one of these methods:

1. **GitHub Security Advisories** (Preferred)
   - Navigate to the [Security Advisories](https://github.com/weshicks/Basic-Agent-Chat-Loop/security/advisories) page
   - Click "Report a vulnerability"
   - Fill out the form with details about the vulnerability

2. **Direct Email**
   - If you prefer email, contact the maintainers directly
   - Include "SECURITY" in the subject line
   - Provide detailed information about the vulnerability

### What to Include

When reporting a vulnerability, please include:

- **Description**: Clear description of the vulnerability
- **Impact**: What can an attacker accomplish?
- **Reproduction**: Step-by-step instructions to reproduce the issue
- **Version**: Which version(s) are affected
- **Proof of Concept**: Code, screenshots, or other evidence (if available)
- **Suggested Fix**: If you have ideas for how to fix it (optional)

### What to Expect

- **Acknowledgment**: We will acknowledge receipt within 48 hours
- **Assessment**: We will assess the vulnerability and determine severity
- **Updates**: We will keep you informed of progress toward a fix
- **Disclosure**: We will coordinate with you on public disclosure timing
- **Credit**: We will credit you in the security advisory (unless you prefer to remain anonymous)

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Release**: Depends on severity and complexity
  - Critical: Within 7 days
  - High: Within 14 days
  - Medium: Within 30 days
  - Low: Next regular release

## Security Best Practices

When using Basic Agent Chat Loop:

### Agent Code Security

- **Review Agent Code**: Always review agent code before loading, especially from untrusted sources
- **File System Access**: Agents have access to the file system - only load agents you trust
- **API Keys**: Store API keys securely (environment variables, not in code)
- **Input Validation**: Validate all user inputs in your agent code

### Configuration Security

- **Sensitive Data**: Never commit `.chatrc` files containing API keys or secrets
- **File Permissions**: Ensure config files have appropriate permissions (not world-readable)
- **Git Ignore**: Keep `.chatrc` in `.gitignore` to prevent accidental commits

### Logging and Privacy

The chat loop framework logs operational information to `~/.chat_loop_logs/`:

**What Gets Logged:**
- User queries (truncated to first 100 characters)
- Agent responses metadata (timing, token counts)
- Error messages and stack traces
- File paths for configurations, templates, and aliases
- Agent initialization and session information

**Privacy Considerations:**
- **PII Warning**: Logs may contain personally identifiable information from user queries
- **File Permissions**: Log files are created with restrictive permissions (0600 - owner read/write only)
- **Log Rotation**: Logs are automatically rotated (max 10MB per file, 5 backup files kept)
- **Local Storage**: All logs are stored locally on your machine, never transmitted

**Best Practices:**
- Review log files periodically and delete old logs if they contain sensitive information
- Do not share log files without reviewing their contents first
- Set `LOG_LEVEL=ERROR` environment variable to reduce logging verbosity
- Log directory location can be configured in `~/.chatrc` (see Configuration Security above)

### Dependencies

- **Keep Updated**: Regularly update to the latest version
- **Audit Dependencies**: We use Dependabot to monitor dependencies
- **Check Advisories**: Review GitHub Security Advisories for this project

## Security Updates

Security updates will be released as:

1. **Patch Releases**: For backward-compatible security fixes (0.1.x)
2. **GitHub Security Advisories**: Public disclosure after fix is available
3. **Release Notes**: Detailed information in CHANGELOG.md
4. **CVE**: We will request CVE numbers for significant vulnerabilities

## Contact

For questions about this security policy or other security-related matters:

- Open a discussion in [GitHub Discussions](https://github.com/weshicks/Basic-Agent-Chat-Loop/discussions) (for general questions)
- Use GitHub Security Advisories for vulnerability reports
- Check existing [Security Advisories](https://github.com/weshicks/Basic-Agent-Chat-Loop/security/advisories) for known issues

## Attribution

This security policy is based on best practices from the open source community and recommendations from the GitHub Security Lab.
