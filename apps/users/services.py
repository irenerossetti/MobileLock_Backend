from django.utils import timezone

from apps.saas.models import SubscriptionPlan, UserSubscription
from apps.users.models import Profile, Usuario


class UserService:

    @staticmethod
    def get_user_profile(user_id):
        return Usuario.objects.get(id=user_id)

    @staticmethod
    def update_user_profile(user, data):

        user.nombres = data.get("nombres", user.nombres)
        user.apellido_paterno = data.get("apellido_paterno", user.apellido_paterno)
        user.apellido_materno = data.get("apellido_materno", user.apellido_materno)

        user.save()

        return user
    @staticmethod
    def search_users(query):

        return Usuario.objects.filter(
            nombres__icontains=query
        ) | Usuario.objects.filter(
            correo_electronico__icontains=query
        )


class UserPlanService:
    PRO_PLAN_NAMES = {"pro", "premium", "empresarial", "enterprise"}

    @staticmethod
    def resolve_plan(plan_ref):
        if plan_ref is None or plan_ref == "":
            return None

        plan = SubscriptionPlan.objects.filter(id=plan_ref, is_active=True).first()
        if plan:
            return plan

        return SubscriptionPlan.objects.filter(
            nombre__iexact=str(plan_ref).strip(),
            is_active=True,
        ).first()

    @staticmethod
    def assign_plan(user, plan_ref):
        plan = UserPlanService.resolve_plan(plan_ref)
        if not plan:
            return False

        profile, _ = Profile.objects.get_or_create(usuario=user)
        profile.plan_actual = plan
        profile.save(update_fields=["plan_actual"])

        es_plan_pro = (plan.nombre or "").strip().lower() in UserPlanService.PRO_PLAN_NAMES
        user.plan_suscripcion = (
            Usuario.PlanSuscripcion.PREMIUM if es_plan_pro else Usuario.PlanSuscripcion.FREE
        )
        user.plan_estado = Usuario.PlanEstado.ACTIVO
        user.save(update_fields=["plan_suscripcion", "plan_estado"])

        UserSubscription.objects.filter(usuario=user, is_active=True).update(
            is_active=False,
            fecha_fin=timezone.now(),
        )
        UserSubscription.objects.create(
            usuario=user,
            plan=plan,
            is_active=True,
        )

        return True

    @staticmethod
    def sync_plan_flags(user):
        profile = getattr(user, "profile", None)
        active_subscription = (
            UserSubscription.objects.select_related("plan")
            .filter(usuario=user, is_active=True)
            .order_by("-fecha_inicio")
            .first()
        )

        plan = None
        if profile and profile.plan_actual:
            plan = profile.plan_actual
        elif active_subscription and active_subscription.plan:
            plan = active_subscription.plan

        if not plan:
            return user

        es_plan_pro = (plan.nombre or "").strip().lower() in UserPlanService.PRO_PLAN_NAMES
        expected_plan = (
            Usuario.PlanSuscripcion.PREMIUM if es_plan_pro else Usuario.PlanSuscripcion.FREE
        )

        update_fields = []
        if user.plan_suscripcion != expected_plan:
            user.plan_suscripcion = expected_plan
            update_fields.append("plan_suscripcion")

        if user.plan_estado != Usuario.PlanEstado.ACTIVO:
            user.plan_estado = Usuario.PlanEstado.ACTIVO
            update_fields.append("plan_estado")

        if update_fields:
            user.save(update_fields=update_fields)

        return user