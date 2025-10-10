---
name: Feature Request
about: Suggest an idea for this project
title: '[FEATURE] Add --pipe flag for Unix pipeline integration'
labels: enhancement
assignees: ''
---

## Feature Description
Add a `--pipe` flag that enables true stdin/stdout mode for seamless integration with Unix pipelines and automation scripts.

## Problem/Motivation
**Is your feature request related to a problem?**
The current interactive mode is great for human use but doesn't work well with shell scripts, CI/CD pipelines, or Unix tool chains. I need a way to use chat_loop as a filter in standard Unix pipelines.

Example: "I'm frustrated when I need to process multiple queries in a script because the interactive prompts and formatting break pipeline composition."

## Proposed Solution
Add a pipe mode that reads queries from stdin (one per line) and writes responses to stdout with minimal formatting.

**Example:**
```bash
# Basic pipeline
echo "What is 2+2?" | chat_loop myagent --pipe
# Output: 4

# Process multiple queries
cat queries.txt | chat_loop myagent --pipe > responses.txt

# Chain with other tools
curl https://api.example.com/data |
  jq -r '.questions[]' |
  chat_loop myagent --pipe |
  tee results.txt

# Parallel processing
parallel -j4 "chat_loop myagent --pipe" < queries.txt > all_responses.txt

# Integration with data processing
awk '{print "Summarize: " $0}' logfile.txt |
  chat_loop myagent --pipe > summaries.txt
```

## Alternatives Considered
1. **Expect scripts** - Too fragile, breaks with format changes
2. **API wrapper** - Requires additional service, overkill for simple scripts
3. **Separate tool** - Would fragment the ecosystem
4. **--quiet flag** - Not enough, need proper stdin handling

## Benefits
Who would benefit from this feature and how?
- **DevOps engineers**: Integrate agents into CI/CD pipelines
- **Data scientists**: Batch processing of datasets
- **Automation scripts**: Reliable, scriptable agent interaction
- **Unix enthusiasts**: Follows Unix philosophy (do one thing well, composable)

## Implementation Ideas
**Behavior in pipe mode:**
- Disable all interactive prompts and readline
- Read one query per line from stdin
- Write one response per line to stdout
- Suppress banners, status bars, colors (unless --pipe-color)
- Exit after processing all input (no interactive loop)
- Write errors to stderr only
- Exit code 0 on success, non-zero on failure

**Optional enhancements:**
```bash
# Keep delimiters for multi-line responses
chat_loop myagent --pipe --delimiter "---"

# JSON mode for structured output
chat_loop myagent --pipe --json
# Output: {"query": "...", "response": "...", "tokens": 123, "cost": 0.01}

# Batch processing with status
chat_loop myagent --pipe --progress
# Writes progress to stderr: [1/100] Processing query...
```

**Suggested implementation approach:**
```python
def pipe_mode(agent, config):
    """Process stdin queries in batch mode."""
    try:
        for line in sys.stdin:
            query = line.strip()
            if not query:
                continue

            try:
                response = agent(query)
                # Extract just the text response
                text = extract_response_text(response)
                print(text, flush=True)
            except Exception as e:
                print(f"ERROR: {e}", file=sys.stderr)
                sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)  # Standard Unix SIGINT exit code
```

## Additional Context
This follows the Unix philosophy of composable tools:
- Each program does one thing well
- Programs work together via stdin/stdout
- Text streams as universal interface

Similar to:
- `jq` for JSON processing
- `sed`/`awk` for text transformation
- `curl` with `-s` flag
- `ffmpeg` with `-i -` for stdin

Would make `chat_loop` a first-class citizen in shell tooling.

**Example use cases:**
```bash
# Log analysis
tail -f app.log | grep ERROR | chat_loop analyst --pipe |
  notify "New error analysis"

# Code review automation
git diff | chat_loop reviewer --pipe > review_comments.txt

# Content generation
cat topics.txt | chat_loop writer --pipe > articles/

# Data enrichment
psql -t -c "SELECT description FROM products" |
  chat_loop classifier --pipe |
  psql -c "UPDATE products SET category = stdin"
```

## Priority
How important is this feature to you?
- [ ] Critical - Blocking my workflow
- [x] High - Would significantly improve my experience
- [ ] Medium - Nice to have
- [ ] Low - Minor improvement
