"""Organization-scoped access helpers used by application views."""
from functools import wraps
from uuid import UUID

from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from .models import Organization, UserRole

ACTIVE_ORGANIZATION_SESSION_KEY = "active_organization_id"


def organizations_for_user(user):
    if not user.is_authenticated:
        return Organization.objects.none()
    return Organization.objects.filter(
        user_roles__user=user,
        user_roles__deleted_at__isnull=True,
        user_roles__role__isnull=False,
        deleted_at__isnull=True,
    ).distinct().order_by("name")


def get_active_organization(request):
    """Resolve the active organization only from the user's explicit membership."""
    if not request.user.is_authenticated:
        raise PermissionDenied("Authentication is required.")

    memberships = UserRole.objects.filter(
        user=request.user,
        deleted_at__isnull=True,
        organization__deleted_at__isnull=True,
    ).select_related("organization")

    requested_id = request.session.get(ACTIVE_ORGANIZATION_SESSION_KEY)
    if requested_id:
        membership = memberships.filter(organization_id=requested_id).first()
        if membership:
            return membership.organization
        request.session.pop(ACTIVE_ORGANIZATION_SESSION_KEY, None)

    membership = memberships.order_by("organization__name", "organization_id").first()
    if not membership:
        raise PermissionDenied("The user has no active organization membership.")
    request.session[ACTIVE_ORGANIZATION_SESSION_KEY] = str(membership.organization_id)
    return membership.organization


def user_has_org_role(user, organization, role_codes):
    if not user.is_authenticated or not organization:
        return False
    return UserRole.objects.filter(
        user=user,
        organization=organization,
        role__code__in=role_codes,
        deleted_at__isnull=True,
    ).exists()


def require_org_roles(*role_codes):
    """View decorator enforcing an organization membership and an allowed role."""
    allowed = tuple(role_codes)

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            organization = get_active_organization(request)
            if not user_has_org_role(request.user, organization, allowed):
                raise PermissionDenied("You do not have permission to perform this operation.")
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator


def switch_organization(request):
    """POST endpoint target: change active organization only to a membership."""
    if request.method != "POST":
        raise PermissionDenied("POST is required.")
    organization_id = request.POST.get("organization_id", "").strip()
    try:
        organization_id = UUID(organization_id)
    except (TypeError, ValueError, AttributeError):
        raise PermissionDenied("The requested organization is not available to this user.")
    membership = UserRole.objects.filter(
        user=request.user,
        organization_id=organization_id,
        deleted_at__isnull=True,
        organization__deleted_at__isnull=True,
    ).select_related("organization").first()
    if not membership:
        raise PermissionDenied("The requested organization is not available to this user.")
    request.session[ACTIVE_ORGANIZATION_SESSION_KEY] = str(membership.organization_id)
    return redirect("home")
