# MNotify MCP Server

Bring MNotify to your AI IDE in one command.

This package exposes the MNotify SMS API as an MCP server so tools like Cursor can securely call real MNotify actions (send SMS, manage contacts/groups/templates, delivery reports) via stdio. This repo also includes a simple interactive MNotify Agent for CLI use. It is based on [Mnotify API v2.0](https://readthedocs.mnotify.com/)

### Requirements
- Python 3.10+
- Environment variable: `MNOTIFY_API_KEY`

### Setup 
- Using uv (recommended):
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh  # install uv if needed
  uv venv                                          
  uv pip install -r requirements.txt               
  ```
- Using any virtualenv manager + pip:
  ```bash
  python -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt
  ```

### Quick start  — install and run the MCP server
```bash
pip install mnotify_mcp_server
export MNOTIFY_API_KEY=sk_mnotify_...

# Start the server (preferred)
mnotify_mcp server

# Alternatives
mnotify-mcp
python -m mnotify_mcp.server
```

### Connect to Cursor
- Option A: Project config `.cursor/mcp.json` (recommended)
```json
{
  "mcpServers": {
    "mnotify": {
      "command": "mnotify_mcp",
      "args": ["server"]
    }
  }
}
```
- Option B: Manual add in Cursor (Settings → MCP → Add Custom Server → Process)
  - Command: `mnotify_mcp`
  - Args: `server`
  - Ensure `MNOTIFY_API_KEY` is set in the environment where Cursor launches the process



## MNotify Agent (interactive CLI)
A local chat agent that can call all MNotify tools directly.
<img src='images/mnotify_cli_agent.png>

### Setup 
- Create a virtual environment and install dependencies with uv or pip (see above).
- Add a `.env` file with:
```env
OPENROUTER_API_KEY=sk-or-v1-...
MNOTIFY_API_KEY=...
AGNO_API_KEY=ag-...   # optional, if monitoring is set.
```

### Start the agent
```bash
uv run mnotify_agent.py
```

### CLI commands
- help: list commands
- history: show recent messages
- tools: list available tools
- test: run a quick tool-call test
- clear: clear conversation context


### Tools exposed
- SMS: `send_quick_bulk_sms`, `send_bulk_group_sms`, `update_scheduled_sms`
- Reports: `sms_delivery_report`, `specific_sms_delivery_report`, `periodic_sms_delivery_report`
- Contacts: `add_contact`, `update_contact`, `delete_contact`, `get_contact_details`, `get_contact_list`, `get_group_contacts`
- Groups: `add_group`, `update_group`, `delete_group`, `get_group_details`, `get_group_list`
- Templates: `get_template_list`, `get_message_template`, `add_message_template`, `update_message_template`, `delete_message_template`
- Utilities: `register_sender_id`, `check_sender_id`, `check_sms_balance`
- Helpers: `get_context_snapshot`, `resolve_group_name`

### Validation & guardrails
- `message` length ≤ 460; `sender_id` length ≤ 11.
- `schedule=true` requires `schedule_time` (YYYY-MM-DD HH:MM).
- `recipient`/`recipients` and `group_id`/`groups` accept string, list, or comma-separated values.
- Optional: `verify_sender=true` performs a best‑effort sender status check before sending.

### Security
- Never pass secrets as tool arguments. The server reads `MNOTIFY_API_KEY` from the environment.
- The server does not log secrets.