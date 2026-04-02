from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

class UsuarioAdmin(UserAdmin):
    list_display = ('correo_electronico', 'nombres', 'apellido_paterno', 'plan_suscripcion', 'plan_estado')
    list_filter = ('plan_suscripcion', 'plan_estado', 'is_active', 'is_staff')
    search_fields = ('correo_electronico', 'nombres', 'apellido_paterno')
    
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