"""Shared process-exit semantics for Stage 7 data-quality runners."""

VALID_RESULT_STATUSES = {"PASS", "WARN", "FAIL"}


def exit_code_for_statuses(statuses):
    """Return nonzero only for FAIL; reject unknown status values."""
    normalized = [str(status).upper() for status in statuses]
    unknown = sorted(set(normalized) - VALID_RESULT_STATUSES)
    if unknown:
        raise ValueError(f"Unknown DQ result status(es): {', '.join(unknown)}")
    return 1 if "FAIL" in normalized else 0
