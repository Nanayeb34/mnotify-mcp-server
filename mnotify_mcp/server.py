import os
from typing import Any, Dict, List, Optional, Union
from mcp.server.fastmcp import FastMCP as _MCPServer
import functions as mnotify
from context_cache import EntityCache


def _require_key() -> str:
    key = os.getenv("MNOTIFY_API_KEY")
    if not key:
        
        raise RuntimeError("Missing MNOTIFY_API_KEY environment variable. Configure it in your MCP client.")
    return key


server = _MCPServer("mnotify")
cache = EntityCache()


def _coerce_str_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    # allow comma-separated string
    raw = str(value).strip()
    if not raw:
        return []
    if raw.startswith("[") and raw.endswith("]"):
        raw = raw[1:-1]
    return [p.strip().strip("\"'") for p in raw.split(",") if p.strip()]


def _maybe_verify_sender(sender_id: str, verify_flag: bool) -> None:
    if not verify_flag:
        return
    try:
        status = mnotify.check_sender_id(sender_id=sender_id)
        state = str((status or {}).get("status") or (status or {}).get("state") or "").lower()
        if state and state not in {"approved", "active", "ok", "success"}:
            pass
    except Exception:
        pass


@server.tool("send_quick_bulk_sms")
def send_quick_bulk_sms(
    recipient: Union[str, List[str], None] = None,
    recipients: Union[str, List[str], None] = None,
    sender_id: str = "",
    message: str = "",
    schedule: bool = False,
    schedule_time: Optional[str] = None,
    verify_sender: bool = False,
) -> Dict[str, Any]:
    """Send SMS to explicit phone numbers.

    Parameters
    - recipient: string (comma-separated) or array of phone numbers
    - recipients: alias of recipient
    - sender_id: string, max 11 chars
    - message: string, max 460 chars
    - schedule: boolean (default false)
    - schedule_time: string 'YYYY-MM-DD HH:MM' if schedule is true
    - verify_sender: boolean, best-effort status check before sending

    Returns
    - API response payload; indexes campaign id in session cache
    """
    _require_key()
    rec = recipient if recipient else recipients
    recipients_list = _coerce_str_list(rec)
    if bool(schedule) and not str(schedule_time or "").strip():
        return {"error": "schedule_time is required when schedule is true (YYYY-MM-DD HH:MM)"}
    if len(message) > 460:
        return {"error": f"message is too long ({len(message)} chars). Max 460."}
    _maybe_verify_sender(sender_id, bool(verify_sender))
    result = mnotify.send_quick_bulk_sms(
        recipient=recipients_list,
        sender_id=sender_id,
        message=message,
        schedule=bool(schedule),
        schedule_time=schedule_time,
    )
    try:
        cache.index_tool_result("send_quick_bulk_sms", result)
    except Exception:
        pass
    return result


@server.tool("send_bulk_group_sms")
def send_bulk_group_sms(
    group_id: Union[str, List[str], None] = None,
    groups: Union[str, List[str], None] = None,
    group_names: Union[str, List[str], None] = None,
    sender_id: str = "",
    message: str = "",
    schedule: bool = False,
    schedule_time: Optional[str] = None,
    verify_sender: bool = False,
) -> Dict[str, Any]:
    """Send an SMS to all contacts in one or more groups.

    Provide `group_id` list and a `message` (≤ 460 chars). For scheduling,
    set `schedule=true` and supply `schedule_time` (YYYY-MM-DD HH:MM).
    """
    _require_key()
    # Prefer explicit IDs, accept aliases; else try to resolve provided group names from cache
    group_ids_raw = group_id or groups
    group_ids = _coerce_str_list(group_ids_raw)
    if not group_ids and group_names:
        names = _coerce_str_list(group_names)
        for name in names:
            norm = " ".join(name.strip().lower().split())
            for known_name, ids in cache.group_ids_by_name.items():
                if norm in known_name or known_name in norm:
                    for gid in ids:
                        group_ids.append(gid)
        # de-duplicate
        group_ids = list(dict.fromkeys(group_ids))
        # If still empty, try to fetch groups now and retry resolution
        if not group_ids:
            try:
                result_list = mnotify.get_group_list()
                try:
                    cache.index_tool_result("get_group_list", result_list)
                except Exception:
                    pass
                # retry
                for name in names:
                    norm = " ".join(name.strip().lower().split())
                    for known_name, ids in cache.group_ids_by_name.items():
                        if norm in known_name or known_name in norm:
                            for gid in ids:
                                group_ids.append(gid)
                group_ids = list(dict.fromkeys(group_ids))
            except Exception:
                pass
    # Conditional requirement: schedule_time when schedule=True
    if bool(schedule) and not str(schedule_time or "").strip():
        return {"error": "schedule_time is required when schedule is true (YYYY-MM-DD HH:MM)"}
    if len(message) > 460:
        return {"error": f"message is too long ({len(message)} chars). Max 460."}
    _maybe_verify_sender(sender_id, bool(verify_sender))
    result = mnotify.send_bulk_group_sms(
        group_id=group_ids,
        sender_id=sender_id,
        message=message,
        schedule=bool(schedule),
        schedule_time=schedule_time,
    )
    # Index campaign id if present
    try:
        cache.index_tool_result("send_bulk_group_sms", result)
    except Exception:
        pass
    return result


@server.tool("update_scheduled_sms")
def update_scheduled_sms(
    id: str,
    sender_id: str,
    schedule_time: str,
    message: Optional[str] = None,
) -> Dict[str, Any]:
    """Update a scheduled SMS campaign.

    Supply `id`, `sender_id`, `schedule_time`, and optional `message` (≤ 460 chars).
    """
    _require_key()
    result = mnotify.update_scheduled_sms(
        _id=id,
        sender_id=sender_id,
        schedule_time=schedule_time,
        message=message,
    )
    try:
        cache.index_tool_result("update_scheduled_sms", result)
    except Exception:
        pass
    return result


@server.tool("sms_delivery_report")
def sms_delivery_report(id: str) -> Dict[str, Any]:
    """Get the delivery report for a specific SMS campaign by its ID."""
    _require_key()
    result = mnotify.sms_delivery_report(_id=id) 
    try:
        cache.index_tool_result("sms_delivery_report", result)
    except Exception:
        pass
    return result


@server.tool("specific_sms_delivery_report")
def specific_sms_delivery_report(campaign_id: str) -> Dict[str, Any]:
    """Get the delivery status for a specific message within a campaign by `campaign_id`."""
    _require_key()
    result = mnotify.specific_sms_delivery_report(campaign_id=campaign_id) 
    try:
        cache.index_tool_result("specific_sms_delivery_report", result)
    except Exception:
        pass
    return result


@server.tool("periodic_sms_delivery_report")
def periodic_sms_delivery_report(from_date: str, to_date: str) -> Dict[str, Any]:
    """Get delivery reports for campaigns within a date range (YYYY-MM-DD)."""
    _require_key()
    result = mnotify.periodic_sms_delivery_report(from_date=from_date, to_date=to_date) 
    try:
        cache.index_tool_result("periodic_sms_delivery_report", result)
    except Exception:
        pass
    return result


# Contacts
@server.tool("add_contact")
def add_contact(
    group_id: str,
    phone: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    dob: Optional[str] = None,
    email: Optional[str] = None,
) -> Dict[str, Any]:
    """Add a contact to a group. Requires `group_id` and `phone`."""
    _require_key()
    result = mnotify.add_contact(
        group_id=group_id,
        phone=phone,
        first_name=first_name,
        last_name=last_name,
        dob=dob,
        email=email,
    )
    try:
        cache.index_tool_result("add_contact", result)
    except Exception:
        pass
    return result


@server.tool("update_contact")
def update_contact(
    contact_id: str,
    phone: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    dob: Optional[str] = None,
    email: Optional[str] = None,
    group_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Update a contact by `contact_id`. Requires `phone`; other fields optional."""
    _require_key()
    result = mnotify.update_contact(
        contact_id=contact_id,
        phone=phone,
        first_name=first_name,
        last_name=last_name,
        dob=dob,
        email=email,
        group_id=group_id,
    )
    try:
        cache.index_tool_result("update_contact", result)
    except Exception:
        pass
    return result


@server.tool("delete_contact")
def delete_contact(contact_id: str) -> Dict[str, Any]:
    """Delete a contact by `contact_id`."""
    _require_key()
    return mnotify.delete_contact(contact_id=contact_id) 


@server.tool("get_contact_details")
def get_contact_details(contact_id: str) -> Dict[str, Any]:
    """Fetch contact details by `contact_id`."""
    _require_key()
    result = mnotify.get_contact_details(contact_id=contact_id) 
    try:
        cache.index_tool_result("get_contact_details", result)
    except Exception:
        pass
    return result


@server.tool("get_contact_list")
def get_contact_list() -> Dict[str, Any]:
    """List contacts (first page as returned by the API)."""
    _require_key()
    result = mnotify.get_contact_list() 
    try:
        cache.index_tool_result("get_contact_list", result)
    except Exception:
        pass
    return result


@server.tool("get_group_contacts")
def get_group_contacts(group_id: str) -> Dict[str, Any]:
    """List contacts in a given group by `group_id`."""
    _require_key()
    result = mnotify.get_group_contacts(group_id=group_id) 
    try:
        cache.index_tool_result("get_group_contacts", result)
    except Exception:
        pass
    return result


# Groups
@server.tool("add_group")
def add_group(group_name: str) -> Dict[str, Any]:
    """Create a new contact group with `group_name`."""
    _require_key()
    result = mnotify.add_group(group_name=group_name) 
    try:
        cache.index_tool_result("add_group", result)
    except Exception:
        pass
    return result


@server.tool("update_group")
def update_group(group_id: str, group_name: str) -> Dict[str, Any]:
    """Rename a contact group by `group_id` to `group_name`."""
    _require_key()
    result = mnotify.update_group(group_id=group_id, group_name=group_name) 
    try:
        cache.index_tool_result("update_group", result)
    except Exception:
        pass
    return result


@server.tool("delete_group")
def delete_group(group_id: str) -> Dict[str, Any]:
    """Delete a contact group by `group_id`."""
    _require_key()
    result = mnotify.delete_group(group_id=group_id) 
    try:
        cache.index_tool_result("delete_group", result)
    except Exception:
        pass
    return result


@server.tool("get_group_details")
def get_group_details(group_id: str) -> Dict[str, Any]:
    """Fetch details for a group by `group_id`."""
    _require_key()
    result = mnotify.get_group_details(group_id=group_id) 
    try:
        cache.index_tool_result("get_group_details", result)
    except Exception:
        pass
    return result


@server.tool("get_group_list")
def get_group_list_tool() -> Dict[str, Any]:
    """List all groups."""
    _require_key()
    result = mnotify.get_group_list() 
    try:
        cache.index_tool_result("get_group_list", result)
    except Exception:
        pass
    return result


# Templates
@server.tool("get_template_list")
def get_template_list_tool() -> Dict[str, Any]:
    """List message templates."""
    _require_key()
    result = mnotify.get_template_list() 
    try:
        cache.index_tool_result("get_template_list", result)
    except Exception:
        pass
    return result


@server.tool("get_message_template")
def get_message_template(template_id: str) -> Dict[str, Any]:
    """Fetch a message template by `template_id`."""
    _require_key()
    result = mnotify.get_message_template(template_id=template_id) 
    try:
        cache.index_tool_result("get_message_template", result)
    except Exception:
        pass
    return result


@server.tool("add_message_template")
def add_message_template(title: str, content: str) -> Dict[str, Any]:
    """Create a message template with `title` and `content`."""
    _require_key()
    result = mnotify.add_message_template(title=title, content=content) 
    try:
        cache.index_tool_result("add_message_template", result)
    except Exception:
        pass
    return result


@server.tool("update_message_template")
def update_message_template(template_id: str, title: Optional[str] = None, content: Optional[str] = None) -> Dict[str, Any]:
    """Update a template by `template_id`. `title` and/or `content` optional."""
    _require_key()
    result = mnotify.update_message_template(template_id=template_id, title=title, content=content) 
    try:
        cache.index_tool_result("update_message_template", result)
    except Exception:
        pass
    return result


@server.tool("delete_message_template")
def delete_message_template(template_id: str) -> Dict[str, Any]:
    """Delete a message template by `template_id`."""
    _require_key()
    result = mnotify.delete_message_template(template_id=template_id) 
    try:
        cache.index_tool_result("delete_message_template", result)
    except Exception:
        pass
    return result


# Utilities
@server.tool("register_sender_id")
def register_sender_id(sender_id: str, purpose: str) -> Dict[str, Any]:
    """Register a sender ID (≤ 11 chars) with a `purpose`."""
    _require_key()
    result = mnotify.register_sender_id(sender_id=sender_id, purpose=purpose) 
    try:
        cache.index_tool_result("register_sender_id", result)
    except Exception:
        pass
    return result


@server.tool("check_sender_id")
def check_sender_id(sender_id: str) -> Dict[str, Any]:
    """Check the status of a registered sender ID."""
    _require_key()
    result = mnotify.check_sender_id(sender_id=sender_id) 
    try:
        cache.index_tool_result("check_sender_id", result)
    except Exception:
        pass
    return result


@server.tool("check_sms_balance")
def check_sms_balance_tool() -> Dict[str, Any]:
    """Get your current SMS balance and wallet summary."""
    _require_key()
    return mnotify.check_sms_balance() 


# Helper/context tools: expose a small snapshot of known IDs
@server.tool("get_context_snapshot")
def get_context_snapshot() -> Dict[str, Any]:
    """Return a compact snapshot of known entities (names → IDs) gathered so far."""
    lines = []
    try:
        lines = cache.get_memory_lines_and_reset()
    except Exception:
        lines = []
    return {"snapshot": lines}


@server.tool("resolve_group_name")
def resolve_group_name(group_name: str, fetch: bool = False) -> Dict[str, Any]:
    """Resolve a group name (case-insensitive, substring) to known IDs from this session.

    This uses the MCP server's in-memory cache populated by prior tool calls.
    """
    name = (group_name or "").strip().lower()
    if not name:
        return {"error": "group_name is required"}
    matches = []
    try:
        for norm_name, ids in cache.group_ids_by_name.items():
            if name in norm_name:
                for gid in ids:
                    matches.append({"group_id": gid, "name": norm_name})
    except Exception:
        pass
    if not matches and bool(fetch):
        try:
            result_list = mnotify.get_group_list()
            try:
                cache.index_tool_result("get_group_list", result_list)
            except Exception:
                pass
            for norm_name, ids in cache.group_ids_by_name.items():
                if name in norm_name:
                    for gid in ids:
                        matches.append({"group_id": gid, "name": norm_name})
        except Exception:
            pass
    if not matches:
        return {"error": f"No known groups matching '{group_name}'. Fetch groups first or set fetch=true."}
    return {"matches": matches}


def main() -> None:
    server.run()


if __name__ == "__main__":
    main()
