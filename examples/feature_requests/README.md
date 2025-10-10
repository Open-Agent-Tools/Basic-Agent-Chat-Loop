# Feature Request Examples

This directory contains well-formed example feature requests that could be submitted to the project's GitHub Issues page.

## Purpose

These examples demonstrate:
- How to use the project's feature request template
- Well-articulated problem statements and motivations
- Concrete implementation ideas
- Use cases and benefits

## Available Examples

### 1. Watch Mode (`watch_mode.md`)
**Priority: High**

Hot-reload agent during development, similar to nodemon. Dramatically improves development iteration speed.

```bash
chat_loop myagent --watch
```

### 2. Budget Limit (`budget_limit.md`)
**Priority: High**

Automatic cost control with budget limits. Prevents accidentally spending too much on expensive models.

```bash
chat_loop expensive-agent --budget 0.50
```

### 3. Pipe Mode (`pipe_mode.md`)
**Priority: High**

Unix pipeline integration for scripting and automation. Makes chat_loop composable with other Unix tools.

```bash
cat queries.txt | chat_loop myagent --pipe > responses.txt
```

## How to Submit

If you'd like to see any of these features implemented:

1. Go to the [GitHub Issues page](https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/issues)
2. Click "New Issue"
3. Select "Feature Request"
4. Copy the content from one of these example files
5. Modify as needed to reflect your specific use case
6. Submit!

## Creating Your Own

Use these as templates for your own feature requests. Good feature requests include:

- **Clear problem statement** - What pain point does this solve?
- **Concrete examples** - Show exactly how it would be used
- **Implementation ideas** - Suggest technical approaches
- **Alternatives considered** - Show you've thought it through
- **Priority assessment** - Help maintainers prioritize

## Contributing

Feel free to add more example feature requests to this directory! They help:
- Document community ideas
- Inspire future development
- Serve as reference for good feature request writing
