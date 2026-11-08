"""JSON encoders safe for AuditLog fields."""

from django.core.serializers.json import DjangoJSONEncoder


class SafeJSONEncoder(DjangoJSONEncoder):
    """Extends DjangoJSONEncoder to fall back to str() on ANY type.

    Makes AuditLog immune to any model field that is not JSON-native
    (FileField, FieldFile, QuerySet, custom objects) both now and in
    the future — new fields never break audit logging.
    """

    def default(self, o):
        try:
            return super().default(o)
        except TypeError:
            try:
                return str(o)
            except Exception:
                return repr(o)