from django.core.management.base import BaseCommand
from apps.devices.models import Dispositivo
from apps.users.models import Usuario, Profile
from django.utils import timezone
import hashlib


class Command(BaseCommand):
    help = "Registrar dispositivos de prueba en la base de datos local."

    def handle(self, *args, **options):
        # 1. Obtener o crear un usuario de prueba
        user, created = Usuario.objects.get_or_create(
            correo_electronico="testuser@mobilelock.ai",
            defaults={
                "username": "testuser",
                "nombres": "Test",
                "apellido_paterno": "User",
                "apellido_materno": "Demo",
                "plan_suscripcion": Usuario.PlanSuscripcion.PREMIUM
            }
        )
        if created:
            user.set_password("testpassword123")
            user.save()
            self.stdout.write(self.style.SUCCESS("Usuario de prueba creado con éxito."))

        # Crear perfil para el usuario si no lo tiene
        Profile.objects.get_or_create(
            usuario=user,
            defaults={
                "limite_verificaciones_mensual": 20,
                "verificaciones_usadas_este_mes": 0
            }
        )

        # 2. Definir dispositivos a registrar
        dispositivos_seed = [
            {
                "marca_modelo": "iPhone 15 Pro Max",
                "hash_imei": "123456789012345", # IMEI plano
                "hash_adn_hardware": "IPHONE15PROMAXHARDWAREHASH",
                "estado": "LIBRE"
            },
            {
                "marca_modelo": "Samsung Galaxy S24 Ultra",
                "hash_imei": "987654321098765", # IMEI plano
                "hash_adn_hardware": "SAMSUNGGALAXYHARDWAREHASH",
                "estado": "ROBADO"
            },
            {
                "marca_modelo": "Xiaomi 14 Ultra",
                "hash_imei": "555555555555555", # IMEI plano
                "hash_adn_hardware": "XIAOMI14ULTRAHARDWAREHASH",
                "estado": "LIBRE"
            }
        ]

        # 3. Guardar en base de datos calculando hash sha256 del IMEI
        for item in dispositivos_seed:
            imei_plano = item["hash_imei"]
            imei_hash = hashlib.sha256(imei_plano.encode("utf-8")).hexdigest()

            # Evitar duplicados
            device, created = Dispositivo.objects.get_or_create(
                hash_imei=imei_hash,
                defaults={
                    "id_usuario_propietario": user,
                    "marca_modelo": item["marca_modelo"],
                    "hash_adn_hardware": item["hash_adn_hardware"],
                    "estado": item["estado"],
                    "fecha_registro_blockchain": timezone.now()
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"Sembrado dispositivo: {item['marca_modelo']} - IMEI: {imei_plano} ({item['estado']})"))
            else:
                # Actualizar estado para pruebas consistentes
                device.estado = item["estado"]
                device.save()
                self.stdout.write(self.style.WARNING(f"Dispositivo {item['marca_modelo']} ya existía, actualizado estado a {item['estado']}"))
