import inspect
from typing import Any, Callable, Dict, List, Optional, get_origin, get_args

def _to_str(value: Any) -> str:
    return "" if value is None else str(value)


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        v = value.strip().lower()
        if v in {"true", "yes", "y", "1"}:
            return True
        if v in {"false", "no", "n", "0"}:
            return False
    return bool(value)


def _to_int(value: Any) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return int(str(value).strip())


def _to_float(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    return float(str(value).strip())


def _to_str_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip().strip("\"'") for x in value if str(x).strip()]
    raw = str(value).strip()
    if raw.startswith("[") and raw.endswith("]"):
        raw = raw[1:-1]
    parts = [p.strip() for p in raw.split(",")]
    return [p.strip().strip("\"'") for p in parts if p.strip()]


# Adapter config types
class FunctionOverride:
    def __init__(
        self,
        expected_types: Optional[Dict[str, str]] = None,
        required: Optional[List[str]] = None,
        optional: Optional[List[str]] = None,
        required_if: Optional[List[Dict[str, Any]]] = None,
        defaults: Optional[Dict[str, Any]] = None,
        aliases: Optional[Dict[str, str]] = None,
        max_lengths: Optional[Dict[str, int]] = None,
    ) -> None:
        self.expected_types = expected_types or {}
        self.required = set(required or [])
        self.optional = set(optional or [])
        self.required_if = required_if or []
        self.defaults = defaults or {}
        self.aliases = aliases or {}
        self.max_lengths = max_lengths or {}


def _infer_expected_type(param: inspect.Parameter) -> str:
    """
    Infer a simple expected type string from annotations when possible.
    Supported: str, bool, int, float, list[str] (as 'list[str]' or 'list')
    Default fallback: 'str'
    """
    annotation = param.annotation
    if annotation is inspect._empty:
        return "str"
    origin = get_origin(annotation)
    args = get_args(annotation)

    if annotation in (str,):
        return "str"
    if annotation in (bool,):
        return "bool"
    if annotation in (int,):
        return "int"
    if annotation in (float,):
        return "float"
    if annotation in (list, List) or origin in (list, List):
        return "list[str]"
    return "str"


def _coerce_value(expected: str, value: Any) -> Any:
    if expected == "str":
        return _to_str(value)
    if expected == "bool":
        return _to_bool(value)
    if expected == "int":
        return _to_int(value)
    if expected == "float":
        return _to_float(value)
    if expected in ("list", "list[str]"):
        return _to_str_list(value)
    return value


def make_flex_wrapper(func: Callable, override: Optional[FunctionOverride] = None) -> Callable:
    sig = inspect.signature(func)
    override = override or FunctionOverride()

    def wrapper(**kwargs):
        if (
            isinstance(kwargs, dict)
            and len(kwargs) == 1
            and "kwargs" in kwargs
            and isinstance(kwargs.get("kwargs"), dict)
        ):
            kwargs = kwargs["kwargs"]

        # Pre-alias normalization for common variants
        try:
            normalized: Dict[str, Any] = {}
            for key, value in list(kwargs.items()):
                canonical = key
                if key in {"phoneNumber", "phone_number"}:
                    canonical = "phone"
                elif key in {"groupId", "group"}:
                    canonical = "group_id"
                elif key in {"contactId"}:
                    canonical = "contact_id"
                elif key in {"templateId"}:
                    canonical = "template_id"
                elif key in {"campaignId"}:
                    canonical = "campaign_id"
                if canonical not in kwargs:
                    normalized[canonical] = value
            kwargs.update(normalized)

            # Expand 'name'/'full_name' into first_name/last_name if missing
            full_name_value = None
            if "full_name" in kwargs:
                full_name_value = kwargs.get("full_name")
            elif "name" in kwargs:
                full_name_value = kwargs.get("name")
            if full_name_value and ("first_name" not in kwargs and "last_name" not in kwargs):
                text = str(full_name_value).strip()
                parts = [p for p in text.split() if p]
                if len(parts) == 1:
                    kwargs["first_name"] = parts[0]
                elif len(parts) >= 2:
                    kwargs["first_name"] = " ".join(parts[:-1])
                    kwargs["last_name"] = parts[-1]

            # Map 'contacts' list → first phone when single-add APIs are used
            if "contacts" in kwargs and "phone" not in kwargs:
                contacts_value = kwargs.get("contacts")
                if isinstance(contacts_value, list) and contacts_value:
                    for item in contacts_value:
                        s = str(item).strip()
                        if s:
                            kwargs["phone"] = s
                            break
        except Exception:
            pass
        # Apply aliases first
        if override.aliases:
            for alias, canonical in override.aliases.items():
                if alias in kwargs and canonical not in kwargs:
                    kwargs[canonical] = kwargs.pop(alias)

        bound_args = {}
        # Apply defaults from override first
        for k, v in override.defaults.items():
            bound_args[k] = v

        # Coerce and bind known params
        for name, param in sig.parameters.items():
            if name in kwargs:
                expected = override.expected_types.get(name) or _infer_expected_type(param)
                bound_args[name] = _coerce_value(expected, kwargs[name])
            else:
                if param.default is not inspect._empty:
                    # Has a default in original function; keep unspecified
                    pass
                else:
                    pass

        for k, v in kwargs.items():
            if k not in bound_args:
                bound_args[k] = v

        # Validate required parameters
        missing: List[str] = []
        for req in override.required:
            if bound_args.get(req) in (None, "", [], {}):
                missing.append(req)

        # Conditional requirements (e.g., schedule_time when schedule is True)
        for rule in override.required_if:
            param_name = rule.get("param")
            when = rule.get("when", {})
            meets = True
            for wkey, wval in when.items():
                if bound_args.get(wkey) != wval:
                    meets = False
                    break
            if meets and bound_args.get(param_name) in (None, "", [], {}):
                missing.append(param_name)

        if missing:
            return {"error": f"Missing required parameter(s): {', '.join(sorted(set(missing)))}"}

        for field_name, max_len in (override.max_lengths or {}).items():
            value = bound_args.get(field_name)
            if isinstance(value, str) and len(value) > int(max_len):
                return {
                    "error": (
                        f"{field_name} is too long ({len(value)} characters). "
                        f"Maximum allowed is {max_len}. Please shorten it and try again."
                    )
                }

        return func(**bound_args)

    try:
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = (func.__doc__ or "").rstrip()
        wrapper.__signature__ = sig 
        try:
            wrapper.__annotations__ = getattr(func, "__annotations__", {})
        except Exception:
            pass
    except Exception:
        pass

    return wrapper


def default_overrides() -> Dict[str, FunctionOverride]:
    """Overrides based on known docstrings and patterns."""
    overrides: Dict[str, FunctionOverride] = {}

    # SMS quick
    overrides["send_quick_bulk_sms"] = FunctionOverride(
        expected_types={
            "recipient": "list[str]",
            "sender_id": "str",
            "message": "str",
            "schedule": "bool",
            "schedule_time": "str",
        },
        required=["recipient", "sender_id", "message"],
        optional=["schedule", "schedule_time"],
        required_if=[{"param": "schedule_time", "when": {"schedule": True}}],
        aliases={"recipients": "recipient"},
        defaults={"schedule": False},
        max_lengths={"message": 460},
    )

    # SMS by group
    overrides["send_bulk_group_sms"] = FunctionOverride(
        expected_types={
            "group_id": "list[str]",
            "sender_id": "str",
            "message": "str",
            "schedule": "bool",
            "schedule_time": "str",
        },
        required=["group_id", "sender_id", "message"],
        optional=["schedule", "schedule_time"],
        required_if=[{"param": "schedule_time", "when": {"schedule": True}}],
        defaults={"schedule": False},
        max_lengths={"message": 460},
    )

    # Update scheduled SMS: enforce message length if provided
    overrides["update_scheduled_sms"] = FunctionOverride(
        expected_types={
            "_id": "str",
            "sender_id": "str",
            "schedule_time": "str",
            "message": "str",
        },
        required=["_id", "sender_id", "schedule_time"],
        optional=["message"],
        max_lengths={"message": 460},
    )


    # Common patterns
    for name in [
        "add_contact", "update_contact", "delete_contact", "get_contact_details",
        "add_group", "update_group", "delete_group", "get_group_details",
        "get_message_template", "update_message_template", "delete_message_template",
        "sms_delivery_report", "specific_sms_delivery_report", "update_scheduled_sms",
    ]:
        overrides[name] = overrides.get(name) or FunctionOverride()

    # Contacts: explicit types, requirements, and aliases
    overrides["add_contact"] = FunctionOverride(
        expected_types={
            "group_id": "str",
            "phone": "str",
            "first_name": "str",
            "last_name": "str",
            "dob": "str",
            "email": "str",
        },
        required=["group_id", "phone"],
        aliases={
            "group": "group_id",
            "phone_number": "phone",
            "phoneNumber": "phone",
        },
    )

    overrides["update_contact"] = FunctionOverride(
        expected_types={
            "contact_id": "str",
            "phone": "str",
            "first_name": "str",
            "last_name": "str",
            "dob": "str",
            "email": "str",
            "group_id": "str",
        },
        required=["contact_id", "phone"],
        aliases={
            "group": "group_id",
            "phone_number": "phone",
            "phoneNumber": "phone",
            "contactId": "contact_id",
        },
    )

    return overrides


def default_aliases() -> Dict[str, Dict[str, str]]:
    """Per-function param aliases."""
    return {
        "send_quick_bulk_sms": {"recipients": "recipient"},
        "send_bulk_group_sms": {"groups": "group_id", "group_ids": "group_id"},
    }


def register_flex_functions(
    agent: Any,
    functions_module: Any,
    overrides: Optional[Dict[str, FunctionOverride]] = None,
    aliases: Optional[Dict[str, Dict[str, str]]] = None,
) -> List[str]:
    """
    Create and register flex wrappers for all public functions in the module.

    Returns list of registered wrapper names.
    """
    overrides = overrides or default_overrides()
    aliases = aliases or default_aliases()

    registered: List[str] = []
    for name, func in inspect.getmembers(functions_module, inspect.isfunction):
        if name.startswith("_"):
            continue
        # Only include functions defined in the target module 
        if getattr(func, "__module__", None) != getattr(functions_module, "__name__", None):
            continue
        # Skip utility functions not intended as tools
        if name in {"main", "safe_api_call", "validate_sms_request", "validate_contact_data"}:
            continue

        ov = overrides.get(name, FunctionOverride())
        ov.aliases = {**aliases.get(name, {}), **ov.aliases}
        wrapper = make_flex_wrapper(func, ov)
        agent.add_tool(wrapper)
        registered.append(wrapper.__name__)
    return registered
