import threading

_thread_locals = threading.local()


def get_current_user():
    return getattr(_thread_locals, "user", None)


def get_current_request():
    return getattr(_thread_locals, "request", None)


class AuditActorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.user = getattr(request, "user", None)
        _thread_locals.request = request
        try:
            return self.get_response(request)
        finally:
            _thread_locals.user = None
            _thread_locals.request = None


class SuperuserOnlyAdminMiddleware:
    """Keep Django's global administration surface out of tenant-admin hands."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/admin/"):
            user = getattr(request, "user", None)
            if user and user.is_authenticated and not user.is_superuser:
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden("Django administration is restricted to platform superusers.")
        return self.get_response(request)
