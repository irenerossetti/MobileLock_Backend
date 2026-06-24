import os
import sys
import time
import django
import random
import requests
from django.core.files.uploadedfile import SimpleUploadedFile

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MobileLock_AI.settings")
django.setup()

from apps.users.models import Usuario
from apps.devices.models import Dispositivo
from rest_framework.test import APIClient

def test_e2e_flow():
    print("Iniciando Prueba E2E de Registro y Verificación...")
    client = APIClient()

    # 1. Preparar usuario
    print("1. Configurando usuario de prueba...")
    email = f"e2e_{random.randint(1000,9999)}@example.com"
    user, created = Usuario.objects.get_or_create(
        correo_electronico=email,
        defaults={"username": f"user_{random.randint(1000,9999)}"}
    )
    if created:
        user.set_password("e2e_password")
        user.plan_suscripcion = "PREMIUM"
        user.save()

    # Obtener token
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)
    token = str(refresh.access_token)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    # 2. Registrar Dispositivo (con foto simulada)
    print("2. Registrando dispositivo...")
    start_time = time.time()
    
    # Crear una imagen simulada (en entorno real debería ser una foto válida para la IA)
    from PIL import Image
    import io
    img = Image.new("RGB", (300, 300), color="red")
    img_io = io.BytesIO()
    img.save(img_io, format='JPEG')
    img_file = SimpleUploadedFile("test_e2e.jpg", img_io.getvalue(), content_type="image/jpeg")

    imei = f"888{random.randint(100000000000, 999999999999)}"
    response = client.post(
        "/api/devices/create/",
        {
            "marca_modelo": "Test E2E Phone",
            "hash_imei": imei,
            "hash_adn_hardware": f"HW_E2E_{imei}",
            "url_imagen_referencia": img_file
        },
        format="multipart"
    )
    
    if response.status_code == 201:
        reg_time = time.time() - start_time
        device_id = response.json()["id_dispositivo"]
        print(f" [OK] Dispositivo registrado exitosamente en {reg_time:.2f} segundos.")
    else:
        print(f" [ERROR] Falló el registro: {response.json()}")
        return

    # 3. Simulación de Verificación Física e IA
    print("3. Ejecutando verificación del dispositivo...")
    start_time_verify = time.time()

    img2 = Image.new("RGB", (300, 300), color="red")
    img_io2 = io.BytesIO()
    img2.save(img_io2, format='JPEG')
    img_file_verify = SimpleUploadedFile("test_verify.jpg", img_io2.getvalue(), content_type="image/jpeg")

    verify_response = client.post(
        "/api/devices/verify/",
        {
            "imei": imei,
            "imagen_verificacion": img_file_verify
        },
        format="multipart"
    )

    if verify_response.status_code == 200:
        ver_time = time.time() - start_time_verify
        print(f" [OK] Verificación completada en {ver_time:.2f} segundos.")
        print(f"      Auténtico: {verify_response.json()['autentico']}")
        print(f"      Similitud: {verify_response.json()['similitud']:.2f}")
    else:
        print(f" [ERROR] Falló la verificación: {verify_response.json()}")

    # 4. Simulación de Cambio de Estado y Trazabilidad (Mock de Polygon)
    print("4. Cambiando estado del dispositivo y trazabilidad...")
    start_time_status = time.time()
    
    status_response = client.patch(
        f"/api/devices/report-state/{device_id}/",
        {
            "estado": "ROBADO",
            "motivo": "Simulación de Robo E2E"
        }
    )

    if status_response.status_code == 200:
        stat_time = time.time() - start_time_status
        print(f" [OK] Estado cambiado en BD y trazabilidad registrada en {stat_time:.2f} segundos.")
    else:
        print(f" [ERROR] Falló el cambio de estado: {status_response.json()}")

    # Limpiar BD
    user.delete()
    print("Prueba E2E finalizada.")

if __name__ == "__main__":
    test_e2e_flow()
