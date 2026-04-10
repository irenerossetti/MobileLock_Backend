from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Profile, Usuario


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    extra = 0

class UsuarioAdmin(UserAdmin):
    list_display = ('correo_electronico', 'nombres', 'apellido_paterno', 'plan_suscripcion', 'plan_estado')
    list_filter = ('plan_suscripcion', 'plan_estado', 'is_active', 'is_staff')
    search_fields = ('correo_electronico', 'nombres', 'apellido_paterno')
    inlines = (ProfileInline,)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Información Personal', {'fields': ('nombres', 'apellido_paterno', 'apellido_materno', 'correo_electronico')}),
        ('Suscripción', {'fields': ('plan_suscripcion', 'plan_expiracion', 'plan_estado')}),
        ('Blockchain', {'fields': ('direccion_blockchain',)}),
        ('Reputación', {'fields': ('puntaje_reputacion', 'dispositivos_registrados_actual')}),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información Personal', {'fields': ('nombres', 'apellido_paterno', 'apellido_materno', 'correo_electronico')}),
    )

admin.site.register(Usuario, UsuarioAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'usuario',
        'stripe_customer_id',
        'plan_actual',
        'limite_verificaciones_mensual',
        'verificaciones_usadas_este_mes',
        'fecha_ultimo_reseteo_verificaciones',
    )
    list_filter = ('plan_actual', 'fecha_ultimo_reseteo_verificaciones')
    search_fields = ('usuario__correo_electronico', 'usuario__username', 'stripe_customer_id')