import os
import json
import tempfile
from unittest.mock import patch, MagicMock
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from apps.devices.models import Dispositivo
from apps.devices.services import DeviceService
from apps.devices.ai_service import AIService
from PIL import Image
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class DeviceAITestCase(APITestCase):
    def setUp(self):
        # Crear usuario de prueba
        self.user = User.objects.create_user(
            username="test_ai_user",
            correo_electronico="test_ai@example.com",
            password="password123",
            plan_suscripcion="PREMIUM"
        )
        
        # Crear un archivo de imagen temporal real
        self.temp_dir = tempfile.TemporaryDirectory()
        self.img_path = os.path.join(self.temp_dir.name, "test_device.jpg")
        # Crear imagen RGB de 300x300 en azul
        img = Image.new("RGB", (300, 300), color="blue")
        img.save(self.img_path, "JPEG")

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("requests.post")
    def test_ai_service_preprocessing_and_extraction(self, mock_post):
        # Simular respuesta del microservicio de IA
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "vector": [0.5] * 1280,
            "visual_hash": "a" * 64
        }
        mock_post.return_value = mock_response

        # Validar extracción de vector
        vector = AIService.extraer_vector_caracteristicas(self.img_path)
        self.assertEqual(len(vector), 1280)
        self.assertEqual(vector[0], 0.5)

        # Validar generación de hash visual
        hash_val = AIService.generar_hash_visual(vector)
        self.assertEqual(len(hash_val), 64)

    @patch("requests.post")
    def test_create_device_with_image_triggers_ai(self, mock_post):
        # Simular respuesta del microservicio de IA
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "vector": [0.42] * 1280,
            "visual_hash": "b" * 64
        }
        mock_post.return_value = mock_response

        # Preparar archivo de carga simulado
        with open(self.img_path, "rb") as f:
            uploaded_image = SimpleUploadedFile(
                name="device.jpg",
                content=f.read(),
                content_type="image/jpeg"
            )

        data = {
            "hash_adn_hardware": "TEST_HW_AI_123",
            "hash_imei": "TEST_IMEI_AI_123",
            "marca_modelo": "Test Phone AI",
            "url_imagen_referencia": uploaded_image
        }

        # Crear dispositivo usando el servicio
        device = DeviceService.create_device(self.user, data)

        # Validar que se generaron y guardaron los campos de IA
        self.assertIsNotNone(device.hash_visual)
        self.assertEqual(len(device.hash_visual), 64)
        
        vector = json.loads(device.vector_caracteristicas)
        self.assertEqual(len(vector), 1280)
        self.assertEqual(vector[0], 0.42)

        # Eliminar archivo físico creado en la carpeta media por la prueba
        if device.url_imagen_referencia:
            try:
                os.remove(device.url_imagen_referencia.path)
            except OSError:
                pass

    def test_calcular_similitud_coseno(self):
        # Vectores idénticos
        vec_a = [1.0] * 1280
        vec_b = [1.0] * 1280
        self.assertAlmostEqual(AIService.calcular_similitud_coseno(vec_a, vec_b), 1.0, places=5)

        # Vectores ortogonales
        vec_c = [1.0, 0.0] + [0.0] * 1278
        vec_d = [0.0, 1.0] + [0.0] * 1278
        self.assertAlmostEqual(AIService.calcular_similitud_coseno(vec_c, vec_d), 0.0, places=5)

        # Cero vector
        vec_zero = [0.0] * 1280
        self.assertEqual(AIService.calcular_similitud_coseno(vec_a, vec_zero), 0.0)

    @patch("apps.devices.ai_service.AIService.extraer_vector_caracteristicas")
    def test_device_physical_verification_endpoint_authentic(self, mock_extraer):
        # Registrar un dispositivo con un vector de referencia de 1.0s
        vector_ref = [1.0] * 1280
        device = Dispositivo.objects.create(
            hash_adn_hardware="HW_REF_123",
            hash_imei="IMEI_REF_123",
            marca_modelo="Model Reference",
            id_usuario_propietario=self.user,
            hash_visual="some_visual_hash",
            vector_caracteristicas=json.dumps(vector_ref),
            url_imagen_referencia=SimpleUploadedFile("ref.jpg", b"image_content", content_type="image/jpeg")
        )

        # Autenticar cliente con JWT
        refresh = RefreshToken.for_user(self.user)
        token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # Simular que la imagen en vivo extrae un vector idéntico (similitud 1.0)
        mock_extraer.return_value = [1.0] * 1280

        # Subir imagen de verificación física
        with open(self.img_path, "rb") as f:
            uploaded_verification = SimpleUploadedFile(
                name="verification.jpg",
                content=f.read(),
                content_type="image/jpeg"
            )

            response = self.client.post(
                "/api/devices/verify/",
                {
                    "imei": "IMEI_REF_123",
                    "imagen_verificacion": uploaded_verification
                }
            )

        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertTrue(res_data["autentico"])
        self.assertAlmostEqual(res_data["similitud"], 1.0, places=5)
        self.assertIn("coincide con el registro original", res_data["mensaje"])

        # Eliminar archivo físico creado en la carpeta media por la prueba
        if device.url_imagen_referencia:
            try:
                os.remove(device.url_imagen_referencia.path)
            except OSError:
                pass

    @patch("apps.devices.ai_service.AIService.extraer_vector_caracteristicas")
    def test_device_physical_verification_endpoint_mismatch(self, mock_extraer):
        # Registrar un dispositivo
        vector_ref = [1.0] * 1280
        device = Dispositivo.objects.create(
            hash_adn_hardware="HW_REF_456",
            hash_imei="IMEI_REF_456",
            marca_modelo="Model Reference 2",
            id_usuario_propietario=self.user,
            hash_visual="some_visual_hash_2",
            vector_caracteristicas=json.dumps(vector_ref),
            url_imagen_referencia=SimpleUploadedFile("ref2.jpg", b"image_content_2", content_type="image/jpeg")
        )

        # Autenticar cliente con JWT
        refresh = RefreshToken.for_user(self.user)
        token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # Simular que la imagen en vivo extrae un vector ortogonal (similitud 0.0)
        mock_extraer.return_value = [0.0] * 1280

        # Subir imagen de verificación física
        with open(self.img_path, "rb") as f:
            uploaded_verification = SimpleUploadedFile(
                name="verification2.jpg",
                content=f.read(),
                content_type="image/jpeg"
            )

            response = self.client.post(
                "/api/devices/verify/",
                {
                    "imei": "IMEI_REF_456",
                    "imagen_verificacion": uploaded_verification
                }
            )

        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertFalse(res_data["autentico"])
        self.assertAlmostEqual(res_data["similitud"], 0.0, places=5)
        self.assertIn("NO coincide con el registro original", res_data["mensaje"])

        if device.url_imagen_referencia:
            try:
                os.remove(device.url_imagen_referencia.path)
            except OSError:
                pass


class HistorialTrazabilidadTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test_trazabilidad_user",
            correo_electronico="test_trazabilidad@example.com",
            password="password123",
            plan_suscripcion="PREMIUM"
        )
        self.device = Dispositivo.objects.create(
            hash_adn_hardware="HW_TRAZ_123",
            hash_imei="IMEI_TRAZ_123",
            marca_modelo="Test Phone",
            id_usuario_propietario=self.user,
            estado="LIBRE"
        )
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_report_stolen_creates_traceability_record(self):
        # Initial state
        self.assertEqual(self.device.estado, "LIBRE")

        # Call endpoint to report stolen
        response = self.client.post(
            "/api/devices/v1/report-stolen/",
            {
                "device_id": self.device.id_dispositivo,
                "motivo": "Robo en la calle"
            }
        )

        self.assertEqual(response.status_code, 200)

        # Refresh device from DB
        self.device.refresh_from_db()
        self.assertEqual(self.device.estado, "ROBADO")

        # Verify traceability record was created
        from apps.devices.models import HistorialTrazabilidad
        historial = HistorialTrazabilidad.objects.filter(id_celular=self.device)
        self.assertEqual(historial.count(), 1)
        
        registro = historial.first()
        self.assertEqual(registro.estado_anterior, "LIBRE")
        self.assertEqual(registro.estado_nuevo, "ROBADO")
        self.assertEqual(registro.motivo, "Robo en la calle")

    def test_report_state_creates_traceability_record(self):
        self.assertEqual(self.device.estado, "LIBRE")
        
        response = self.client.patch(
            f"/api/devices/report-state/{self.device.id_dispositivo}/",
            {
                "estado": "EXTRAVIADO",
                "motivo": "Perdido en el transporte público"
            }
        )

        self.assertEqual(response.status_code, 200)

        self.device.refresh_from_db()
        self.assertEqual(self.device.estado, "EXTRAVIADO")

        from apps.devices.models import HistorialTrazabilidad
        historial = HistorialTrazabilidad.objects.filter(id_celular=self.device)
        self.assertEqual(historial.count(), 1)
        
        registro = historial.first()
        self.assertEqual(registro.estado_anterior, "LIBRE")
        self.assertEqual(registro.estado_nuevo, "EXTRAVIADO")
        self.assertEqual(registro.motivo, "Perdido en el transporte público")
