from .access import organizations_for_user, ACTIVE_ORGANIZATION_SESSION_KEY

def organization_context(request):
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {"available_organizations": [], "active_organization": None}
    organizations = list(organizations_for_user(request.user))
    active_id = request.session.get(ACTIVE_ORGANIZATION_SESSION_KEY)
    active = next((org for org in organizations if str(org.pk) == str(active_id)), None)
    if active is None and organizations:
        active = organizations[0]
        request.session[ACTIVE_ORGANIZATION_SESSION_KEY] = str(active.pk)
    return {"available_organizations": organizations, "active_organization": active}
