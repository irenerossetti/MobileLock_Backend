import logging
import requests
import hashlib
import numpy as np
from django.conf import settings

logger = logging.getLogger(__name__)

class AIService:

    @classmethod
    def extraer_vector_caracteristicas(cls, image_path):
        """
        Extrae un vector de 1280 floats correspondiente a las características visuales del dispositivo
        haciendo una petición HTTP POST al microservicio de IA (FastAPI).
        """
        url = f"{settings.AI_MICROSERVICE_URL}/extract-features/"
        logger.info(f"Enviando imagen al microservicio de IA en {url}...")
        
        try:
            with open(image_path, "rb") as image_file:
                files = {"file": (image_path.split("/")[-1], image_file, "image/jpeg")}
                response = requests.post(url, files=files, timeout=30)
                
            if response.status_code == 200:
                data = response.json()
                logger.info("Características visuales extraídas exitosamente desde el microservicio de IA.")
                return data["vector"]
            else:
                logger.error(f"El microservicio de IA devolvió un error ({response.status_code}): {response.text}")
                raise RuntimeError(f"Error del microservicio de IA: {response.text}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de red intentando conectar al microservicio de IA: {str(e)}")
            raise RuntimeError("No se pudo establecer conexión con el microservicio de IA en el puerto 8002.") from e
        except Exception as e:
            logger.error(f"Error inesperado al invocar el microservicio de IA: {str(e)}")
            raise RuntimeError(f"Error al procesar la huella visual: {str(e)}") from e

    @staticmethod
    def generar_hash_visual(vector):
        """
        Genera un hash SHA-256 determinista a partir de los floats formateados con 6 decimales.
        """
        vector_str = ",".join(f"{x:.6f}" for x in vector)
        return hashlib.sha256(vector_str.encode("utf-8")).hexdigest()

    @staticmethod
    def calcular_similitud_coseno(vector_a, vector_b):
        """
        Calcula la similitud coseno entre dos vectores numéricos usando NumPy.
        Retorna un flotante en el rango [0.0, 1.0].
        """
        a = np.array(vector_a, dtype=np.float32)
        b = np.array(vector_b, dtype=np.float32)

        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        cos_sim = np.dot(a, b) / (norm_a * norm_b)
        
        # Recortar el valor al rango de seguridad [0.0, 1.0] para evitar imprecisiones de coma flotante
        return float(np.clip(cos_sim, 0.0, 1.0))

