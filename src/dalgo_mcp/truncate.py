"""Token-aware output truncation for large tool responses.

Prevents context window flooding from large API responses while giving
the model metadata to request more data when needed.
"""

MAX_LOG_LINES = 100
MAX_LIST_ITEMS = 50


def truncate_log_text(text: str, max_lines: int = MAX_LOG_LINES) -> dict:
    """Truncate log text to max_lines, keeping head and tail.

    Returns a dict with 'content' and '_meta' keys.
    """
    if not text:
        return {"content": text, "_meta": {"truncated": False}}

    lines = text.splitlines()
    if len(lines) <= max_lines:
        return {"content": text, "_meta": {"truncated": False, "total_lines": len(lines)}}

    half = max_lines // 2
    head = lines[:half]
    tail = lines[-half:]
    omitted = len(lines) - max_lines

    truncated_text = "\n".join(head) + f"\n\n... [{omitted} lines omitted] ...\n\n" + "\n".join(tail)
    return {
        "content": truncated_text,
        "_meta": {
            "truncated": True,
            "total_lines": len(lines),
            "shown": max_lines,
            "omitted": omitted,
            "note": (f"Showing first {half} and last {half} lines. Full logs available in Dalgo UI."),
        },
    }


def truncate_list(items: list, max_items: int = MAX_LIST_ITEMS) -> dict:
    """Truncate a list to max_items with metadata.

    Returns a dict with 'items' and '_meta' keys.
    """
    if len(items) <= max_items:
        return {"items": items, "_meta": {"truncated": False, "total": len(items)}}

    return {
        "items": items[:max_items],
        "_meta": {
            "truncated": True,
            "total": len(items),
            "shown": max_items,
            "omitted": len(items) - max_items,
            "note": f"Showing first {max_items} of {len(items)} items.",
        },
    }
