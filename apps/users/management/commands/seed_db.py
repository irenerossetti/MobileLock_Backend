from django.core.management.base import BaseCommand
from faker import Faker
import random
import uuid

from apps.users.models import Usuario


fake = Faker()


class Command(BaseCommand):

    help = "Genera datos de prueba para MobileLock AI"

    def handle(self, *args, **kwargs):

        self.stdout.write("Creando usuarios de prueba...")
        Usuario.objects.exclude(is_superuser=True).delete()
        for i in range(10):

            correo = fake.unique.email()

            usuario = Usuario.objects.create_user(
                username=correo,
                correo_electronico=correo,
                password="12345678",
                nombres=fake.first_name(),
                apellido_paterno=fake.last_name(),
                apellido_materno=fake.last_name(),
                direccion_blockchain=str(uuid.uuid4()),
                puntaje_reputacion=random.uniform(0, 100),
                dispositivos_registrados_actual=random.randint(0, 5)
            )

            self.stdout.write(f"Usuario creado: {usuario.correo_electronico}")

        self.stdout.write(self.style.SUCCESS("SEED COMPLETADO"))