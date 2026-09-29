from collections.abc import Iterable

ROLE_PERMISSIONS = {
    "admin": {"*"},
    "approver": {
        "dashboard.view",
        "catalog.view",
        "catalog.manage",
        "stock.view",
        "stock.entry",
        "stock.exit",
        "stock.adjust",
        "stock.transfer",
        "requests.create",
        "requests.view_own",
        "requests.view_department",
        "requests.approve",
        "requests.process",
        "requests.cancel_any",
        "audit.view",
    },
    "operations": {
        "dashboard.view",
        "catalog.view",
        "catalog.manage",
        "stock.view",
        "stock.entry",
        "stock.transfer",
        "stock.receive",
        "stock.exit_confirm",
        "requests.view_own",
        "requests.view_department",
        "requests.view_all",
        "requests.process",
        "audit.view",
    },
    "operator": {
        "dashboard.view",
        "catalog.view",
        "stock.view",
        "stock.entry",
        "stock.transfer",
        "stock.receive",
        "stock.exit_confirm",
        "requests.view_own",
        "requests.view_department",
        "requests.view_all",
        "requests.process",
        "audit.view",
    },
    "requester": {"dashboard.view", "catalog.view", "requests.create", "requests.view_own"},
    "industry": {
        "dashboard.view",
        "catalog.view",
        "stock.view",
        "requests.view_own",
    },
}


def profile_role(user) -> str:
    if not user or not user.is_authenticated:
        return ""
    if user.is_superuser:
        return "admin"
    try:
        return user.profile.role
    except Exception:
        return ""


def has_permission(user, permission: str) -> bool:
    permissions = ROLE_PERMISSIONS.get(profile_role(user), set())
    return "*" in permissions or permission in permissions


def has_any_permission(user, permissions: Iterable[str]) -> bool:
    return any(has_permission(user, permission) for permission in permissions)

