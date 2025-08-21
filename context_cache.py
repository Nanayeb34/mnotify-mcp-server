import time
from typing import Any, Dict, List, Optional, Tuple, Set


def _normalize(text: Optional[str]) -> str:
    if not isinstance(text, str):
        return ""
    return " ".join(text.strip().lower().split())


def _normalize_phone(phone: Optional[str]) -> str:
    if not isinstance(phone, str):
        return ""
    import re
    return re.sub(r"[^\d+]", "", phone)


class EntityCache:
    """
    Central in-memory cache for entities and a schema-driven indexer to extract
    identifiers and human-friendly keys from tool results.

    This does not expose any state to the LLM by default. Use
    get_memory_lines_and_reset() to generate tiny breadcrumbs when helpful.
    """

    def __init__(self) -> None:
        now = time.time()
        # Groups
        self.groups_by_id: Dict[str, Dict[str, Any]] = {}
        self.group_ids_by_name: Dict[str, Set[str]] = {}
        self.groups_last_created_id: Optional[str] = None

        # Contacts
        self.contacts_by_id: Dict[str, Dict[str, Any]] = {}
        self.contact_ids_by_phone: Dict[str, Set[str]] = {}
        self.contact_ids_by_fullname: Dict[str, Set[str]] = {}
        self.contacts_last_created_id: Optional[str] = None

        # Templates
        self.templates_by_id: Dict[str, Dict[str, Any]] = {}
        self.template_ids_by_title: Dict[str, Set[str]] = {}
        self.templates_last_created_id: Optional[str] = None

        # Campaigns
        self.campaigns_by_id: Dict[str, Dict[str, Any]] = {}
        self.campaigns_last_created_id: Optional[str] = None

        # Sender IDs
        self.sender_ids_by_name: Dict[str, Dict[str, Any]] = {}

        # Deltas to turn into minimal breadcrumbs
        self._delta_group_pairs: Set[Tuple[str, str]] = set()
        self._delta_created_groups: Set[Tuple[str, str]] = set()
        self._delta_created_contacts: Set[Tuple[str, str, str]] = set()  # (first,last,id)
        self._delta_campaigns_created: Set[str] = set()

        self._updated_at = now

    # ------------------------ Indexing helpers ------------------------

    def _record_group(self, group_id: Optional[str], name: Optional[str], created: bool = False) -> None:
        if not group_id:
            return
        if name is None:
            name = ""
        norm_name = _normalize(name)
        existing = self.groups_by_id.get(group_id) or {}
        # Update stored group
        merged = {
            **existing,
            "_id": existing.get("_id") or group_id,
            "id": existing.get("id"),
            "group_id": existing.get("group_id"),
            "name": existing.get("name") or name,
            "group_name": existing.get("group_name") or name,
            "__updated_at": time.time(),
        }
        self.groups_by_id[group_id] = merged
        if norm_name:
            self.group_ids_by_name.setdefault(norm_name, set()).add(group_id)
            self._delta_group_pairs.add((name or "", group_id))
        if created:
            self.groups_last_created_id = group_id
            self._delta_created_groups.add((name or "", group_id))

    def _record_contact(self, contact_id: Optional[str], first: Optional[str], last: Optional[str], phone: Optional[str], created: bool = False) -> None:
        if not contact_id:
            return
        first = first or ""
        last = last or ""
        norm_full = _normalize((first + " " + last).strip())
        norm_phone = _normalize_phone(phone or "")
        existing = self.contacts_by_id.get(contact_id) or {}
        merged = {
            **existing,
            "id": existing.get("id") or contact_id,
            "_id": existing.get("_id") or contact_id,
            "firstname": existing.get("firstname") or first,
            "lastname": existing.get("lastname") or last,
            "phone": existing.get("phone") or phone,
            "__updated_at": time.time(),
        }
        self.contacts_by_id[contact_id] = merged
        if norm_full:
            self.contact_ids_by_fullname.setdefault(norm_full, set()).add(contact_id)
        if norm_phone:
            self.contact_ids_by_phone.setdefault(norm_phone, set()).add(contact_id)
        if created:
            self.contacts_last_created_id = contact_id
            self._delta_created_contacts.add((first, last, contact_id))

    def _record_template(self, template_id: Optional[str], title: Optional[str], created: bool = False) -> None:
        if not template_id:
            return
        title = title or ""
        norm_title = _normalize(title)
        existing = self.templates_by_id.get(template_id) or {}
        merged = {
            **existing,
            "_id": existing.get("_id") or template_id,
            "id": existing.get("id") or template_id,
            "title": existing.get("title") or title,
            "name": existing.get("name") or title,
            "__updated_at": time.time(),
        }
        self.templates_by_id[template_id] = merged
        if norm_title:
            self.template_ids_by_title.setdefault(norm_title, set()).add(template_id)
        if created:
            self.templates_last_created_id = template_id

    def _record_campaign(self, campaign_id: Optional[str], payload: Optional[Dict[str, Any]] = None, created: bool = False) -> None:
        if not campaign_id:
            return
        existing = self.campaigns_by_id.get(campaign_id) or {}
        merged = {**existing, **(payload or {}), "__updated_at": time.time()}
        self.campaigns_by_id[campaign_id] = merged
        if created:
            self.campaigns_last_created_id = campaign_id
            self._delta_campaigns_created.add(campaign_id)

    # ------------------------ Public API ------------------------

    def index_tool_result(self, tool_name: str, result: Any) -> None:
        """
        Index the output of a tool call based on expected shapes from docstrings.
        Handles dicts, lists, and (payload, id) tuples returned by some functions.
        """
        if result is None:
            return
        try:
            # Unwrap (payload, id) tuples
            payload = result
            extra_id = None
            if isinstance(result, (list, tuple)) and len(result) == 2 and isinstance(result[1], (str, int)):
                payload, extra_id = result

            # Groups
            if tool_name in {"get_group_list", "get_group_details"}:
                items = []
                if isinstance(payload, dict):
                    for key in ("groups", "data", "result", "items"):
                        val = payload.get(key)
                        if isinstance(val, list):
                            items = val
                            break
                    if items:
                        for g in items:
                            if isinstance(g, dict):
                                gid = g.get("_id") or g.get("id") or g.get("group_id")
                                name = g.get("name") or g.get("group_name") or g.get("title")
                                self._record_group(str(gid) if gid is not None else None, str(name) if name is not None else None)
                elif isinstance(payload, list):
                    for g in payload:
                        if isinstance(g, dict):
                            gid = g.get("_id") or g.get("id") or g.get("group_id")
                            name = g.get("name") or g.get("group_name") or g.get("title")
                            self._record_group(str(gid) if gid is not None else None, str(name) if name is not None else None)

            if tool_name in {"add_group", "update_group"}:
                gid = None
                name = None
                if extra_id:
                    gid = str(extra_id)
                if isinstance(payload, dict):
                    gid = gid or payload.get("_id") or payload.get("id") or payload.get("group_id")
                    name = payload.get("name") or payload.get("group_name") or payload.get("title")
                self._record_group(str(gid) if gid is not None else None, str(name) if name is not None else None, created=(tool_name == "add_group"))

            # Contacts
            if tool_name in {"get_contact_list", "get_group_contacts", "get_contact_details"}:
                items = []
                if isinstance(payload, dict):
                    for key in ("contacts", "data", "result", "items"):
                        val = payload.get(key)
                        if isinstance(val, list):
                            items = val
                            break
                elif isinstance(payload, list):
                    items = payload
                for c in items:
                    if isinstance(c, dict):
                        cid = c.get("id") or c.get("_id")
                        first = c.get("firstname") or c.get("first_name")
                        last = c.get("lastname") or c.get("last_name")
                        phone = c.get("phone")
                        self._record_contact(str(cid) if cid is not None else None, str(first) if first is not None else None, str(last) if last is not None else None, str(phone) if phone is not None else None)

            if tool_name in {"add_contact", "update_contact"}:
                cid = None
                first = None
                last = None
                phone = None
                if extra_id:
                    cid = str(extra_id)
                if isinstance(payload, dict):
                    cid = cid or payload.get("id") or payload.get("_id")
                    first = payload.get("firstname") or payload.get("first_name")
                    last = payload.get("lastname") or payload.get("last_name")
                    phone = payload.get("phone")
                self._record_contact(str(cid) if cid is not None else None, str(first) if first is not None else None, str(last) if last is not None else None, str(phone) if phone is not None else None, created=(tool_name == "add_contact"))

            # Templates
            if tool_name in {"get_template_list", "get_message_template"}:
                items = []
                if isinstance(payload, dict):
                    for key in ("templates", "data", "result", "items"):
                        val = payload.get(key)
                        if isinstance(val, list):
                            items = val
                            break
                    if items:
                        for t in items:
                            if isinstance(t, dict):
                                tid = t.get("_id") or t.get("id")
                                title = t.get("title") or t.get("name")
                                self._record_template(str(tid) if tid is not None else None, str(title) if title is not None else None)
                elif isinstance(payload, list):
                    for t in payload:
                        if isinstance(t, dict):
                            tid = t.get("_id") or t.get("id")
                            title = t.get("title") or t.get("name")
                            self._record_template(str(tid) if tid is not None else None, str(title) if title is not None else None)

            if tool_name in {"add_message_template", "update_message_template"}:
                tid = None
                title = None
                if extra_id:
                    tid = str(extra_id)
                if isinstance(payload, dict):
                    tid = tid or payload.get("_id") or payload.get("id")
                    title = payload.get("title") or payload.get("name")
                self._record_template(str(tid) if tid is not None else None, str(title) if title is not None else None, created=(tool_name == "add_message_template"))

            # Campaigns (SMS)
            if tool_name in {"send_quick_bulk_sms", "send_bulk_group_sms", "send_bulk_group_sms_by_group_names"}:
                campaign_id = None
                if extra_id:
                    campaign_id = str(extra_id)
                if isinstance(payload, dict):
                    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else None
                    if summary:
                        campaign_id = campaign_id or summary.get("_id") or summary.get("id")
                self._record_campaign(str(campaign_id) if campaign_id is not None else None, payload if isinstance(payload, dict) else None, created=True)

            if tool_name in {"update_scheduled_sms", "check_scheduled_sms", "sms_delivery_report", "specific_sms_delivery_report", "periodic_sms_delivery_report"}:
                if isinstance(payload, dict):
                    # Try to record campaign ids if present
                    possible_ids = []
                    if payload.get("summary") and isinstance(payload.get("summary"), dict):
                        summary = payload["summary"]
                        possible_ids.append(summary.get("_id") or summary.get("id"))
                    for key in ("campaign_id", "id", "_id"):
                        if key in payload:
                            possible_ids.append(payload.get(key))
                    for cid in possible_ids:
                        if cid:
                            self._record_campaign(str(cid), payload)

            # Sender IDs
            if tool_name in {"register_sender_id", "check_sender_id"}:
                if isinstance(payload, dict):
                    sender_name = payload.get("sender_name") or payload.get("sender") or payload.get("name")
                    if sender_name:
                        self.sender_ids_by_name[_normalize(sender_name)] = payload

        except Exception:
            # Avoid crashing on unexpected shapes
            return

    def get_memory_lines_and_reset(self, max_pairs: int = 10) -> List[str]:
        lines: List[str] = []
        if self._delta_group_pairs:
            pairs = list(self._delta_group_pairs)
            preview = ", ".join([f"{n} -> {gid}" for n, gid in pairs[:max_pairs]])
            extra = " (…more)" if len(pairs) > max_pairs else ""
            if preview:
                lines.append(f"Known groups: {preview}{extra}")
        for name, gid in sorted(self._delta_created_groups):
            if name:
                lines.append(f"Created group: {name} -> {gid}")
            else:
                lines.append(f"Created group id: {gid}")
        for first, last, cid in sorted(self._delta_created_contacts):
            display = f"{(first or '').strip()} {(last or '').strip()}".strip() or "contact"
            lines.append(f"Created {display} -> {cid}")
        for cid in sorted(self._delta_campaigns_created):
            lines.append(f"Campaign created: {cid}")

        # Reset deltas
        self._delta_group_pairs.clear()
        self._delta_created_groups.clear()
        self._delta_created_contacts.clear()
        self._delta_campaigns_created.clear()
        return lines
