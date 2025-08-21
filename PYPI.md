# MNotify MCP Server

Expose the MNotify SMS API as an MCP server so IDEs and AI tools (e.g., Cursor) can securely call real MNotify actions (send SMS, manage contacts/groups/templates, delivery reports) via stdio.

This page describes the package specifically for PyPI. For the broader repository (including a local CLI agent), see the project README on [GitHub](https://github.com/Nanayeb34/mnotify-mcp-server).

## Installation
```bash
pip install mnotify_mcp_server
```

## Quick Start
Set your MNotify API key and start the MCP server process:
```bash
export MNOTIFY_API_KEY=sk_mnotify_...

# Start the server
mnotify_mcp server
# or
mnotify-mcp
# or
python -m mnotify_mcp.server
```

## Environment
- `MNOTIFY_API_KEY` is required.
- Python 3.10+.

## Tools Exposed
- SMS: send_quick_bulk_sms, send_bulk_group_sms, update_scheduled_sms
- Reports: sms_delivery_report, specific_sms_delivery_report, periodic_sms_delivery_report
- Contacts: add_contact, update_contact, delete_contact, get_contact_details, get_contact_list, get_group_contacts
- Groups: add_group, update_group, delete_group, get_group_details, get_group_list
- Templates: get_template_list, get_message_template, add_message_template, update_message_template, delete_message_template
- Utilities: register_sender_id, check_sender_id, check_sms_balance

## Validation & Guardrails
- Message length ≤ 460; sender ID length ≤ 11
- Scheduling requires `schedule_time` in `YYYY-MM-DD HH:MM`

## Security
- Never pass secrets as tool arguments; the server reads `MNOTIFY_API_KEY` from the environment.
- The server does not log secrets.
