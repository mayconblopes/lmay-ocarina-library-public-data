"""Validate the notification feed and its version 1 contract.

This check intentionally uses only Python's standard library so it can run in
the public-data repository without adding a package manager or dependencies.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FEED = ROOT / "notifications.json"
DEFAULT_SCHEMA = Path(__file__).with_name("notifications.schema.json")
UTC_DATE_TIME = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)
ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
NOTIFICATION_TYPES = {"info", "warning", "maintenance"}


class ValidationError(ValueError):
    """Raised when the feed or schema violates the public contract."""


def load_json(path: Path) -> object:
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as error:
        raise ValidationError(f"{path}: invalid JSON: {error}") from error
    except OSError as error:
        raise ValidationError(f"{path}: could not be read: {error}") from error


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def validate_schema_contract(schema: object) -> None:
    require(isinstance(schema, dict), "schema: root must be an object")
    require(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", "schema: expected Draft 2020-12")
    require(schema.get("$id"), "schema: missing $id")

    properties = schema.get("properties")
    require(isinstance(properties, dict), "schema: missing root properties")
    require(properties.get("schemaVersion", {}).get("const") == 1, "schema: schemaVersion must remain 1")
    require(set(schema.get("required", [])) == {"schemaVersion", "notifications"}, "schema: root required fields changed")

    item_schema = properties.get("notifications", {}).get("items")
    require(isinstance(item_schema, dict), "schema: missing notification item schema")
    required = set(item_schema.get("required", []))
    require(required == {"id", "type", "title", "message"}, "schema: notification required fields changed")

    item_properties = item_schema.get("properties")
    require(isinstance(item_properties, dict), "schema: missing notification properties")
    require("startsAt" in item_properties and "expiresAt" in item_properties, "schema: startsAt/expiresAt fields are required")
    require("action" in item_properties, "schema: missing localized action field")
    conditionals = item_schema.get("allOf", [])
    require(
        any(
            isinstance(rule, dict)
            and rule.get("if", {}).get("properties", {}).get("type", {}).get("const") == "warning"
            and set(rule.get("then", {}).get("required", [])) == {"startsAt", "expiresAt"}
            for rule in conditionals
        ),
        "schema: warning notifications must require startsAt and expiresAt",
    )

    definitions = schema.get("$defs")
    require(isinstance(definitions, dict), "schema: missing definitions")
    localized_text = definitions.get("localizedText")
    require(isinstance(localized_text, dict), "schema: missing localizedText definition")
    require(set(localized_text.get("required", [])) == {"pt-BR"}, "schema: localizedText must require only pt-BR")
    require("en" in localized_text.get("properties", {}), "schema: localizedText must define optional en")

    action_schema = item_properties["action"]
    require(set(action_schema.get("required", [])) == {"label", "url"}, "schema: action must require label and url")
    require(isinstance(definitions.get("localizedUrl"), dict), "schema: missing localizedUrl definition")


def parse_utc_date_time(value: object, path: str) -> datetime:
    require(isinstance(value, str), f"{path}: must be a string")
    require(UTC_DATE_TIME.fullmatch(value) is not None, f"{path}: must be an ISO 8601 UTC date-time ending in Z")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise ValidationError(f"{path}: invalid date-time: {value}") from error


def validate_https_url(value: object, path: str) -> None:
    require(isinstance(value, str), f"{path}: must be a string")
    require(value.startswith("https://"), f"{path}: must use HTTPS")
    parsed = urlparse(value)
    require(parsed.scheme == "https" and bool(parsed.netloc), f"{path}: must be a valid HTTPS URL")


def validate_localized_text(value: object, path: str) -> None:
    require(isinstance(value, dict), f"{path}: must be an object")
    require(set(value) <= {"pt-BR", "en"}, f"{path}: only pt-BR and en are allowed")
    require("pt-BR" in value, f"{path}: pt-BR is required")
    for locale, text in value.items():
        require(isinstance(text, str) and len(text) > 0, f"{path}.{locale}: must be a non-empty string")


def validate_localized_url(value: object, path: str) -> None:
    require(isinstance(value, dict), f"{path}: must be an object")
    require(set(value) <= {"pt-BR", "en"}, f"{path}: only pt-BR and en are allowed")
    require("pt-BR" in value, f"{path}: pt-BR is required")
    for locale, url in value.items():
        validate_https_url(url, f"{path}.{locale}")


def validate_feed(feed: object) -> None:
    require(isinstance(feed, dict), "feed: root must be an object")
    require(set(feed) == {"schemaVersion", "notifications"}, "feed: unexpected top-level fields")
    require(feed.get("schemaVersion") == 1, "feed.schemaVersion: must be 1")
    notifications = feed.get("notifications")
    require(isinstance(notifications, list), "feed.notifications: must be an array")

    ids: set[str] = set()
    allowed_fields = {
        "id",
        "type",
        "startsAt",
        "expiresAt",
        "title",
        "message",
        "url",
        "action",
    }
    for index, notification in enumerate(notifications):
        path = f"feed.notifications[{index}]"
        require(isinstance(notification, dict), f"{path}: must be an object")
        require(set(notification) <= allowed_fields, f"{path}: contains an unsupported field")
        for field in ("id", "type", "title", "message"):
            require(field in notification, f"{path}.{field}: is required")

        identifier = notification["id"]
        require(isinstance(identifier, str) and ID_PATTERN.fullmatch(identifier) is not None, f"{path}.id: invalid stable identifier")
        require(identifier not in ids, f"{path}.id: duplicate identifier {identifier!r}")
        ids.add(identifier)

        require(notification["type"] in NOTIFICATION_TYPES, f"{path}.type: unsupported notification type")
        if notification["type"] == "warning":
            require("startsAt" in notification and "expiresAt" in notification, f"{path}: warnings require startsAt and expiresAt")
        validate_localized_text(notification["title"], f"{path}.title")
        validate_localized_text(notification["message"], f"{path}.message")

        starts_at = None
        expires_at = None
        if "startsAt" in notification:
            starts_at = parse_utc_date_time(notification["startsAt"], f"{path}.startsAt")
        if "expiresAt" in notification:
            expires_at = parse_utc_date_time(notification["expiresAt"], f"{path}.expiresAt")
        if starts_at is not None and expires_at is not None:
            require(expires_at > starts_at, f"{path}.expiresAt: must be later than startsAt")

        if "url" in notification:
            validate_https_url(notification["url"], f"{path}.url")
        if "action" in notification:
            action = notification["action"]
            require(isinstance(action, dict), f"{path}.action: must be an object")
            require(set(action) == {"label", "url"}, f"{path}.action: label and url are required")
            validate_localized_text(action["label"], f"{path}.action.label")
            validate_localized_url(action["url"], f"{path}.action.url")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feed", type=Path, default=DEFAULT_FEED, help="notification feed JSON file")
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA, help="notification JSON Schema file")
    args = parser.parse_args()

    try:
        schema = load_json(args.schema)
        feed = load_json(args.feed)
        validate_schema_contract(schema)
        validate_feed(feed)
    except ValidationError as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        return 1

    print(f"Valid notification feed: {args.feed}")
    print(f"Valid notification contract: {args.schema}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
