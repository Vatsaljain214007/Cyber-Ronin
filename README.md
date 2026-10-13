# Cyber Ronin

An AI agent for defensive cybersecurity and system administration tasks using natural language.

## Overview

Cyber Ronin lets you perform basic cybersecurity and system-administration tasks using plain English instead of memorizing command-line syntax across multiple tools.

## Architecture

```
User Input → Intent Parser → Safety Gate → Tool Executor → Summarizer → User Output
                ↓              ↓             ↓              ↓            ↓
            (LLM call)   (confirmation)  (subprocess)   (LLM call)   (text)
                ↓              ↓             ↓              ↓            ↓
            Audit Log ← Audit Log ← Audit Log ← Audit Log ← Audit Log
```

## Features

- **Network Scanning** - Scan hosts for open ports using Nmap
- **Auth Log Analysis** - Check for failed login attempts in system logs
- **System Health** - Monitor CPU, memory, disk, and top processes
- **Process Listing** - List running processes with optional filtering

## Safety Model

| Tool | Classification | Confirmation Required |
|------|---------------|----------------------|
| `network_scan` | Sensitive | Yes |
| `check_auth_log` | Safe (read-only) | No |
| `system_health` | Safe (read-only) | No |
| `list_processes` | Safe (read-only) | No |

**Safety guarantees:**
- All subprocess calls use parameterized list form (no `shell=True`)
- User input is validated/sanitized before use
- Sensitive actions blocked pending explicit `y/n` confirmation
- No offensive/exploitation functionality
- Full audit trail logged to `audit_log.jsonl`

## Requirements

- Python 3.8+
- Nmap (for network scanning): `sudo apt install nmap` / `brew install nmap` / [Windows installer](https://nmap.org/download.html)
- psutil: `pip install psutil`

Optional (for LLM features):
- openai: `pip install openai` (for OpenAI API)

## Installation

```bash
cd cyber_ronin
pip install -r requirements.txt  # or: pip install psutil
```

## Usage

### Single Command
```bash
python main.py "scan 192.168.1.1 for open ports"
python main.py "check for failed logins"
python main.py "show system health"
python main.py "list processes named python"
```

### Interactive Mode
```bash
python main.py --interactive
```

### With OpenAI (for better intent parsing/summarization)
```bash
python main.py --llm openai --api-key YOUR_KEY "scan example.com"
```

## Example Test Prompts

Run these against the finished agent to verify tool selection:

1. `"scan 192.168.1.1 for open ports"` → `network_scan`
2. `"check example.com for listening ports"` → `network_scan`
3. `"nmap scan target 10.0.0.5 top 100 ports"` → `network_scan`
4. `"check for recent failed logins in /var/log/auth.log"` → `check_auth_log`
5. `"show me failed ssh login attempts from the last 24 hours"` → `check_auth_log`
6. `"what's the system health looking like"` → `system_health`
7. `"show cpu and memory usage"` → `system_health`
8. `"list all running processes"` → `list_processes`
9. `"show processes named python"` → `list_processes`
10. `"check if nginx is running"` → `list_processes`

## Project Structure

```
cyber_ronin/
├── agent.py              # Main pipeline orchestration
├── main.py               # CLI entry point
├── tool_registry.json    # Tool schemas for LLM
├── tool_registry.py      # Registry loader
├── safety.py             # Permission gate logic
├── audit_log.py          # JSON-lines audit logging
├── llm_client.py         # LLM abstraction (mock/OpenAI)
├── intent_parser.py      # User input → tool selection
├── summarizer.py         # Tool output → human response
├── tool_executor.py      # Tool function dispatch
├── tools/
│   ├── __init__.py
│   ├── network_scan.py   # Nmap wrapper
│   ├── log_check.py      # Auth log parser
│   ├── system_health.py  # psutil system metrics
│   └── process_list.py   # Process enumeration
└── README.md
```

## Audit Log

All actions are logged to `audit_log.jsonl` with:
- Timestamp
- Pipeline step (intent_parser, safety_gate, tool_executor, summarizer)
- Action performed
- Input/output data
- Whether user confirmed (for sensitive actions)

## Extending

To add a new tool:
1. Create `tools/new_tool.py` with a typed function
2. Add entry to `tool_registry.json` with `sensitive: true/false`
3. Register in `tool_executor.py` TOOL_FUNCTIONS dict
4. Test with a natural language prompt

## License

MIT