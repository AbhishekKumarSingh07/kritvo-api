"""The fixed permission catalogue (LLD 12.3).

Tenants combine these codes into their own named roles (``roles.permissions``); the
catalogue itself never changes per tenant. Nothing in TASK-003 writes a role — that is
a future module's job — but the source-of-truth list belongs here so that module can
import and validate against it rather than inventing its own copy.
"""

PERMISSION_CATALOGUE: frozenset[str] = frozenset(
    {
        "job.view_all",
        "job.view_assigned",
        "job.create",
        "job.assign",
        "job.update_assigned",
        "job.verify_supervisor",
        "job.cancel",
        "job.reopen",
        "attendance.punch_self",
        "attendance.review",
        "attendance.amend",
        "inventory.issue_return",
        "inventory.adjust",
        "obligation.waive",
        "contract.manage",
        "invoice.manage",
        "expense.submit",
        "expense.review",
        "report.finance",
        "report.operations",
        "audit.view",
        "settings.manage",
        "member.manage",
        "role.manage",
        "billing.manage",
        "portal.view_own",
    }
)


def assert_valid_permissions(codes: frozenset[str]) -> None:
    unknown = codes - PERMISSION_CATALOGUE
    if unknown:
        raise ValueError(f"unknown permission codes: {sorted(unknown)}")
