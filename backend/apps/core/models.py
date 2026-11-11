from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone as dj_timezone

from .encoders import SafeJSONEncoder
from .mixins import BaseModel


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra):
        if not email:
            raise ValueError("Users must have an email address.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra)

    def create_superuser(self, email, password, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self._create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    import uuid as _uuid
    id = models.UUIDField(primary_key=True, default=_uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    locale = models.CharField(max_length=10, default="pt")
    timezone = models.CharField(max_length=64, default="UTC")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    totp_secret = models.CharField(max_length=64, blank=True)
    date_joined = models.DateTimeField(default=dj_timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        ordering = ("email",)

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email


class Organization(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    settings = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.name


ROLE_CODES = [
    ("admin", "Administrator"),
    ("risk_manager", "Risk Manager"),
    ("auditor", "Auditor"),
    ("control_owner", "Control Owner"),
    ("contributor", "Contributor"),
    ("reader", "Reader"),
]


class Role(models.Model):
    code = models.CharField(max_length=32, unique=True, choices=ROLE_CODES)
    name = models.CharField(max_length=64)
    is_system = models.BooleanField(default=True)

    class Meta:
        ordering = ("code",)

    def __str__(self):
        return self.name


class UserRole(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_roles")
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="user_roles")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="user_roles")
    granted_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta(BaseModel.Meta):
        constraints = [models.UniqueConstraint(fields=["user", "role", "organization"], name="uniq_user_role_org")]

    def __str__(self):
        return f"{self.user.email} -> {self.role.code} @ {self.organization.slug}"


class AuditLog(models.Model):
    ACTION_CREATE = "create"
    ACTION_UPDATE = "update"
    ACTION_DELETE = "delete"
    ACTION_TRANSITION = "transition"

    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    action = models.CharField(max_length=32)
    entity_type = models.CharField(max_length=64)
    entity_id = models.UUIDField()
    before = models.JSONField(null=True, blank=True, encoder=SafeJSONEncoder)
    after = models.JSONField(null=True, blank=True, encoder=SafeJSONEncoder)
    diff = models.JSONField(null=True, blank=True, encoder=SafeJSONEncoder)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["entity_type", "entity_id"]),
            models.Index(fields=["actor", "-created_at"]),
            models.Index(fields=["organization", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.action} {self.entity_type}#{self.entity_id}"


class Tag(BaseModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="tags")
    name = models.CharField(max_length=64)
    slug = models.SlugField(max_length=64)
    color = models.CharField(max_length=7, default="#6b7280")

    class Meta(BaseModel.Meta):
        constraints = [models.UniqueConstraint(fields=["organization", "slug"], name="uniq_tag_org_slug")]

    def __str__(self):
        return self.name


class TaggedItem(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name="tagged_items")
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["tag", "content_type", "object_id"], name="uniq_tagged_item")]
        indexes = [models.Index(fields=["content_type", "object_id"])]


class Comment(BaseModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.PROTECT, related_name="comments")
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey("content_type", "object_id")
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies")
    body = models.TextField()

    class Meta(BaseModel.Meta):
        indexes = [models.Index(fields=["content_type", "object_id"])]


class Attachment(BaseModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="attachments")
    uploaded_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+")
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey("content_type", "object_id")
    file = models.FileField(upload_to="attachments/%Y/%m/")
    filename = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=128, blank=True)
    size_bytes = models.BigIntegerField(default=0)
    sha256 = models.CharField(max_length=64, blank=True, db_index=True)

    class Meta(BaseModel.Meta):
        indexes = [models.Index(fields=["content_type", "object_id"])]


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    event_type = models.CharField(max_length=64)
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    link = models.CharField(max_length=512, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["user", "read_at", "-created_at"])]


class NotificationPreference(models.Model):
    CHANNEL_CHOICES = [("in_app", "In-app"), ("email", "Email")]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notification_prefs")
    event_type = models.CharField(max_length=64)
    channel = models.CharField(max_length=16, choices=CHANNEL_CHOICES)
    enabled = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "event_type", "channel"], name="uniq_notif_pref")]


class WorkflowDefinition(BaseModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="workflow_definitions")
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    is_default = models.BooleanField(default=True)

    class Meta(BaseModel.Meta):
        constraints = [models.UniqueConstraint(fields=["organization", "content_type", "name"], name="uniq_workflow_def")]

    def __str__(self):
        return f"{self.name} ({self.content_type.model})"


class WorkflowState(models.Model):
    definition = models.ForeignKey(WorkflowDefinition, on_delete=models.CASCADE, related_name="states")
    code = models.SlugField(max_length=64)
    label = models.CharField(max_length=128)
    is_terminal = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("order",)
        constraints = [models.UniqueConstraint(fields=["definition", "code"], name="uniq_workflow_state")]

    def __str__(self):
        return f"{self.definition.name}:{self.code}"


class WorkflowTransition(models.Model):
    definition = models.ForeignKey(WorkflowDefinition, on_delete=models.CASCADE, related_name="transitions")
    from_state = models.ForeignKey(WorkflowState, on_delete=models.CASCADE, related_name="outgoing")
    to_state = models.ForeignKey(WorkflowState, on_delete=models.CASCADE, related_name="incoming")
    required_role = models.ForeignKey(Role, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    requires_comment = models.BooleanField(default=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["definition", "from_state", "to_state"], name="uniq_workflow_transition")]


class WorkflowInstance(models.Model):
    definition = models.ForeignKey(WorkflowDefinition, on_delete=models.CASCADE, related_name="instances")
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey("content_type", "object_id")
    current_state = models.ForeignKey(WorkflowState, on_delete=models.PROTECT, related_name="+")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["content_type", "object_id"], name="uniq_workflow_per_entity")]
        indexes = [models.Index(fields=["content_type", "object_id"])]

    def _validate_transition_context(self, user, to_state):
        from django.core.exceptions import PermissionDenied

        if not getattr(user, "is_authenticated", False) or not getattr(user, "is_active", False):
            raise PermissionDenied("Authentication is required to transition a workflow.")

        if to_state is None or to_state.definition_id != self.definition_id:
            raise PermissionDenied("The target state does not belong to this workflow.")
        if self.current_state.definition_id != self.definition_id:
            raise PermissionDenied("The current state does not belong to this workflow.")
        if self.definition.content_type_id != self.content_type_id:
            raise PermissionDenied("The workflow definition has an incompatible entity type.")
        if self.definition.deleted_at is not None:
            raise PermissionDenied("The workflow definition is inactive.")

        entity = self.content_object
        if entity is None:
            raise PermissionDenied("The workflow target object no longer exists.")
        if getattr(entity, "deleted_at", None) is not None:
            raise PermissionDenied("A deleted object cannot change workflow state.")

        from .workflows import _object_organization_id

        organization_id = self.definition.organization_id
        if _object_organization_id(entity) != organization_id:
            raise PermissionDenied("The workflow target belongs to another organization.")
        if not Organization.objects.filter(pk=organization_id, deleted_at__isnull=True).exists():
            raise PermissionDenied("The workflow organization is not active.")

        memberships = UserRole.objects.filter(
            user=user,
            organization_id=organization_id,
            deleted_at__isnull=True,
        )
        # Tenant membership is mandatory for every user, including superusers.
        if not memberships.exists():
            raise PermissionDenied("The user is not a member of this organization.")

        transition = self.definition.transitions.filter(
            from_state=self.current_state,
            to_state=to_state,
        ).select_related("required_role").first()
        if transition is None:
            raise PermissionDenied("This workflow transition is not allowed.")

        # A platform superuser bypasses the required role, never tenant or data
        # integrity checks.
        if not getattr(user, "is_superuser", False) and transition.required_role_id:
            has_required_role = memberships.filter(
                role_id=transition.required_role_id
            ).exists()
            has_admin_role = memberships.filter(role__code="admin").exists()
            if not has_required_role and not has_admin_role:
                raise PermissionDenied("The user does not have the role required for this transition.")

        return transition

    def can_transition(self, user, to_state):
        from django.core.exceptions import PermissionDenied

        try:
            self._validate_transition_context(user, to_state)
        except (PermissionDenied, AttributeError, ValueError):
            return False
        return True

    def transition(self, user, to_state, comment=""):
        from django.core.exceptions import PermissionDenied, ValidationError
        from django.db import transaction

        comment = (comment or "").strip()
        with transaction.atomic():
            try:
                locked = (
                    type(self).objects.select_for_update()
                    .select_related("definition", "current_state", "content_type")
                    .get(pk=self.pk)
                )
            except type(self).DoesNotExist:
                raise PermissionDenied("The workflow instance no longer exists.")

            transition = locked._validate_transition_context(user, to_state)
            if transition.requires_comment and not comment:
                raise ValidationError("A comment is required for this workflow transition.")

            old_state = locked.current_state
            locked.current_state = to_state
            locked.save(update_fields=["current_state", "updated_at"])

            AuditLog.objects.create(
                organization_id=locked.definition.organization_id,
                actor=user,
                action=AuditLog.ACTION_TRANSITION,
                entity_type=(
                    f"{locked.content_type.app_label}.{locked.content_type.model}"
                ),
                entity_id=locked.object_id,
                before={"state": old_state.code},
                after={"state": to_state.code},
                diff={"comment": comment} if comment else None,
            )

            # Keep the caller's object instance in sync with the locked row.
            self.current_state = locked.current_state
            self.updated_at = locked.updated_at


class SystemSetting(BaseModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="system_settings")
    key = models.CharField(max_length=128)
    value = models.JSONField(default=dict, blank=True)

    class Meta(BaseModel.Meta):
        constraints = [models.UniqueConstraint(fields=["organization", "key"], name="uniq_system_setting")]
