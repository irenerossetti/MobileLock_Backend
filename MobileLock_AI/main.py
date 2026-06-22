import hashlib
import logging
import cv2
import numpy as np
import torch
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MobileLock_AI")

app = FastAPI(
    title="MobileLock AI Microservice",
    description="Microservicio dedicado para la extracción de características físicas y huella visual de dispositivos utilizando EfficientNet-B0.",
    version="1.0.0"
)

# Global variables for model lazy-loading
_model = None
_device = None

def get_model():
    global _model, _device
    if _model is None:
        try:
            logger.info("Cargando modelo EfficientNet-B0 y pesos pre-entrenados...")
            _device = torch.device("cpu")
            weights = EfficientNet_B0_Weights.DEFAULT
            model = efficientnet_b0(weights=weights)
            
            # Reemplazar la capa clasificadora final con una Identidad para obtener embeddings de 1280 floats
            model.classifier = torch.nn.Identity()
            model.eval()
            
            _model = model.to(_device)
            logger.info("Modelo cargado exitosamente en CPU.")
        except Exception as e:
            logger.error(f"Error inicializando el modelo PyTorch: {str(e)}", exc_info=True)
            raise RuntimeError("No se pudo inicializar el modelo de IA en el servidor.") from e
    return _model, _device

def preprocesar_imagen(image_bytes: bytes) -> np.ndarray:
    """
    Decodifica los bytes de la imagen, la convierte a RGB, la redimensiona a 224x224
    y la normaliza con los valores medios de ImageNet.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if image is None:
        raise ValueError("No se pudo decodificar la imagen. Asegúrate de enviar un archivo de imagen válido.")

    # Convertir de BGR (OpenCV) a RGB
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Redimensionar a 224x224 (entrada estándar de EfficientNet-B0)
    image = cv2.resize(image, (224, 224))

    # Normalizar escala a [0.0, 1.0]
    image = image.astype(np.float32) / 255.0

    # Normalizar con la media y desviación estándar de ImageNet
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    image = (image - mean) / std

    # Cambiar dimensiones a (Canales, Alto, Ancho)
    image = image.transpose((2, 0, 1))

    # Añadir dimensión de batch: (1, Canales, Alto, Ancho)
    image = np.expand_dims(image, axis=0)
    return image

def generar_hash_visual(vector: list) -> str:
    """
    Genera un hash SHA-256 determinista a partir de los floats formateados con 6 decimales.
    """
    vector_str = ",".join(f"{x:.6f}" for x in vector)
    return hashlib.sha256(vector_str.encode("utf-8")).hexdigest()

@app.get("/")
def read_root():
    return {"status": "ok", "message": "MobileLock AI Microservice is running."}

@app.post("/extract-features/")
async def extract_features(file: UploadFile = File(...)):
    """
    Recibe un archivo de imagen (Multipart), extrae el vector de características de 1280 flotantes
    y genera el hash visual único determinista.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo enviado debe ser una imagen.")

    try:
        # Leer bytes
        image_bytes = await file.read()
        
        # Preprocesar
        preprocessed_img = preprocesar_imagen(image_bytes)
        
        # Obtener modelo e inferir
        model, device = get_model()
        input_tensor = torch.tensor(preprocessed_img).to(device)
        
        with torch.no_grad():
            features = model(input_tensor)
            # Aplanar vector y convertir a lista de Python
            vector = features.squeeze().cpu().numpy().tolist()
            
        # Generar hash visual
        visual_hash = generar_hash_visual(vector)
        
        return JSONResponse(
            status_code=200,
            content={
                "vector": vector,
                "visual_hash": visual_hash
            }
        )
        
    except ValueError as val_err:
        logger.warning(f"Error de validación de imagen: {str(val_err)}")
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as e:
        logger.error(f"Error inesperado procesando la imagen: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno procesando imagen: {str(e)}")
