import cv2
import numpy as np
import hashlib
import logging

logger = logging.getLogger(__name__)

class AIService:
    _model = None
    _device = None

    @classmethod
    def _get_model(cls):
        """
        Carga el modelo de forma perezosa (lazy loading) para evitar el consumo de recursos
        cuando no se requiere realizar procesamiento de IA.
        """
        if cls._model is None:
            try:
                import torch
                from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights

                cls._device = torch.device("cpu")
                logger.info("Inicializando modelo de Inteligencia Artificial (EfficientNet-B0) en CPU...")
                
                # Cargamos pesos oficiales pre-entrenados en ImageNet
                weights = EfficientNet_B0_Weights.DEFAULT
                model = efficientnet_b0(weights=weights)
                
                # Reemplazamos la capa clasificadora final por una Identidad para extraer embeddings directos
                model.classifier = torch.nn.Identity()
                model.eval()
                
                cls._model = model.to(cls._device)
                logger.info("Modelo EfficientNet-B0 cargado exitosamente.")
            except Exception as e:
                logger.error(f"Error cargando PyTorch/Torchvision: {str(e)}")
                raise RuntimeError("No se pudo inicializar el motor de IA en el servidor.") from e
        return cls._model, cls._device

    @staticmethod
    def preprocesar_imagen(image_path):
        """
        Lee una imagen, la redimensiona y la normaliza utilizando OpenCV y NumPy.
        Sigue los parámetros recomendados para modelos entrenados en ImageNet.
        """
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"No se pudo cargar la imagen en la ruta: {image_path}")

        # Conversión de color: OpenCV lee por defecto en BGR, pero la red espera RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Redimensionar a 224x224 (entrada estándar de EfficientNet-B0)
        image = cv2.resize(image, (224, 224))

        # Normalización: Escalar a rango [0.0, 1.0]
        image = image.astype(np.float32) / 255.0

        # Normalización con los promedios y desviaciones estándar de ImageNet
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        image = (image - mean) / std

        # Cambiar el formato de (Alto, Ancho, Canales) a (Canales, Alto, Ancho)
        image = image.transpose((2, 0, 1))

        # Agregar dimensión de batch/lote: (1, Canales, Alto, Ancho)
        image = np.expand_dims(image, axis=0)
        return image

    @classmethod
    def extraer_vector_caracteristicas(cls, image_path):
        """
        Extrae un vector de 1280 floats correspondiente a las características visuales del dispositivo.
        """
        import torch
        
        # Preprocesar imagen
        input_np = cls.preprocesar_imagen(image_path)
        
        # Obtener modelo e inferir en modo evaluación
        model, device = cls._get_model()
        input_tensor = torch.tensor(input_np).to(device)

        with torch.no_grad():
            # forward pass
            features = model(input_tensor)
            # Aplanar salida y convertir a lista nativa de floats
            vector = features.squeeze().cpu().numpy().tolist()

        return vector

    @staticmethod
    def generar_hash_visual(vector):
        """
        Genera un hash SHA-256 determinista a partir de los floats formateados con 6 decimales.
        """
        # Formatear el vector a una cadena estructurada para garantizar el mismo hash
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
