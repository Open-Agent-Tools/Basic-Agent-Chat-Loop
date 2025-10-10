---
name: Feature Request
about: Suggest an idea for this project
title: '[FEATURE] Add --budget flag for cost control'
labels: enhancement
assignees: ''
---

## Feature Description
Add a `--budget <amount>` flag that automatically stops the chat session when the cumulative cost reaches the specified limit.

## Problem/Motivation
**Is your feature request related to a problem?**
When experimenting with expensive models or running long sessions, costs can add up quickly without realizing it. There's currently no built-in way to cap spending per session.

Example: "I'm frustrated when I need to test a new expensive agent because I worry about accidentally running up high API costs during exploration."

## Proposed Solution
Add a budget flag that monitors cumulative cost and gracefully stops the session when reached.

**Example:**
```bash
# Set $0.50 budget
chat_loop expensive-agent --budget 0.50

# During chat:
# [Shows cost tracking as normal]
# Time: 6.3s │ Tokens: 4.6K │ Cost: $0.017 (Budget: $0.483 remaining)

# When budget reached:
# ⚠️  Budget limit reached: $0.50 / $0.50
# Session ending gracefully...
# [Shows session summary]
```

## Alternatives Considered
1. **Manual monitoring** - Requires constantly watching cost display, error-prone
2. **External script** - Could wrap the CLI but wouldn't have access to internal tracking
3. **Config file setting** - Less flexible than per-session control

## Benefits
Who would benefit from this feature and how?
- **Developers**: Safe experimentation without cost anxiety
- **Students/learners**: Can try expensive models within fixed budgets
- **Teams**: Can enforce cost controls on shared accounts
- **Production users**: Safety net for automated/unattended sessions

## Implementation Ideas
- Check cost after each query against budget limit
- Give warning at 90% of budget ("Budget: 90% used")
- Option for soft limit (warning) vs hard limit (stop)
- Allow budget in dollars: `--budget 0.50` or tokens: `--budget-tokens 10000`
- Track budget across session summary

**Suggested implementation approach:**
```python
class ChatLoop:
    def __init__(self, ..., budget=None):
        self.budget = budget
        self.spent = 0.0

    async def process_query(self, query):
        # After getting response and tracking tokens
        self.spent = self.token_tracker.get_cost()

        if self.budget and self.spent >= self.budget:
            print(f"⚠️  Budget limit reached: ${self.spent:.3f} / ${self.budget:.3f}")
            raise BudgetLimitError()
```

**Configuration option:**
```yaml
# .chatrc
behavior:
  default_budget: 1.0  # Default budget for all sessions

agents:
  'expensive-agent':
    default_budget: 0.25  # Override for specific agent
```

## Additional Context
This aligns with responsible AI usage and cost management best practices. Similar features exist in:
- Cloud computing (AWS budget alerts, GCP billing alerts)
- Rate limiting in APIs
- Resource quotas in container orchestration

Would pair well with the existing token tracking to provide comprehensive cost control.

## Priority
How important is this feature to you?
- [ ] Critical - Blocking my workflow
- [x] High - Would significantly improve my experience
- [ ] Medium - Nice to have
- [ ] Low - Minor improvement
