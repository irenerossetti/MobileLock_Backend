# Guía de Despliegue en Render.com 🚀

## Prerequisitos
- Cuenta en [Render.com](https://render.com/)
- Código subido a GitHub
- Base de datos PostgreSQL (recomendado: Neon o Render Database)

---

## Paso 1: Preparar el Repositorio

✅ **Ya está hecho:**
- `.env.example` - Archivo de ejemplo con variables de entorno
- `Procfile` - Configuración para Render
- `build.sh` - Script de compilación
- `runtime.txt` - Versión de Python
- `requirements.txt` - Dependencias actualizadas
- `settings.py` - Configurado para variables de entorno

## Paso 2: Crear Base de Datos PostgreSQL

### Opción A: Usando Neon (Recomendado)
1. Ve a https://neon.tech
2. Crea una cuenta gratuita
3. Crea un proyecto
4. Anota los detalles de conexión:
   - Host: `ep-xxx.c-5.us-east-1.aws.neon.tech`
   - Database: `neondb`
   - User: `*****`
   - Password: `*****`
   - Port: `5432`

### Opción B: Usando Render Database
1. En Render.com crea un PostgreSQL Database
2. Anota los detalles de conexión

## Paso 3: Crear Variables de Entorno en Render

1. Ve a tu Dashboard de Render.com
2. Crea un nuevo **Web Service** desde GitHub
3. Selecciona el repositorio `MobileLock_Backend`
4. Configura las siguientes variables de entorno:

```
# En Render Environment Variables
SECRET_KEY = <genera-una-clave-segura: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'>
DEBUG = False
ALLOWED_HOSTS = tuapp.onrender.com,localhost,127.0.0.1

DB_ENGINE = django.db.backends.postgresql
DB_NAME = neondb
DB_USER = neondb_owner
DB_PASSWORD = <tu-contraseña-neon>
DB_HOST = ep-xxx.c-5.us-east-1.aws.neon.tech
DB_PORT = 5432

CORS_ALLOWED_ORIGINS = https://tuapp.onrender.com,http://localhost:3000
```

## Paso 4: Configurar el Web Service en Render

### Build Command
```bash
chmod +x build.sh && ./build.sh
```

### Start Command
```bash
gunicorn config.wsgi --bind 0.0.0.0:$PORT
```

### Configuración Recomendada
- **Plan:** Free (o superior)
- **Region:** Los Angeles (usa)
- **Auto-deploy:** Habilitado (opcional)

## Paso 5: Desplegar

1. Push a tu rama main en GitHub
2. Render automáticamente deployará si auto-deploy está habilitado
3. O haz clic en "Deploy" manualmente en Render

## Verificar Despliegue

```bash
# Visita tu URL en Render
https://tuapp.onrender.com

# Checkea los logs
# En Render -> Your App -> Logs
```

## Pasos Post-Despliegue

### 1. Crear Superuser (Admin)
```bash
# En los logs de Render, o ejecuta:
python manage.py createsuperuser
```

### 2. Acceder a Admin
```
https://tuapp.onrender.com/admin
```

### 3. Recolectar Static Files (Ya automatizado)
El script `build.sh` automáticamente ejecuta:
```bash
python manage.py collectstatic --noinput
```

---

## 🔒 Seguridad - Importante

### No hacer:
❌ Commit de `.env` - Ya está en `.gitignore`
❌ Hardcodear contraseñas en código
❌ Usar `DEBUG=True` en producción
❌ Usar `CORS_ALLOW_ALL_ORIGINS=True` en producción

### Lo que ya hicimos:
✅ Usar `python-dotenv` para variables de entorno
✅ Configurar HTTPS automático en Render
✅ Configurar seguridad en settings.py
✅ WhiteNoise para archivos estáticos
✅ Gunicorn como servidor WSGI

---

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'apps'"
```python
# Esto ya está arreglado en settings.py
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))
```

### Error: "Static files not found"
El script build.sh automáticamente ejecuta collectstatic. 
Verifica que `STATIC_ROOT` esté configurado.

### Error: "Connection refused postgresql"
Revisa que `DB_HOST`, `DB_USER`, `DB_PASSWORD` sean correctos en Render.

### Error: "ALLOWED_HOSTS"
Verifica que tu URL de Render esté en `ALLOWED_HOSTS`.

---

## Variables de Entorno - Resumen Completo

| Variable | Ejemplo | Descripción |
|----------|---------|-------------|
| `SECRET_KEY` | `django-insecure-abc123...` | Clave secreta de Django |
| `DEBUG` | `False` | Modo debug (False en producción) |
| `ALLOWED_HOSTS` | `app.onrender.com,localhost` | Hosts permitidos |
| `DB_ENGINE` | `django.db.backends.postgresql` | Motor de BD |
| `DB_NAME` | `neondb` | Nombre de BD |
| `DB_USER` | `neondb_owner` | Usuario BD |
| `DB_PASSWORD` | `npg_xxx` | Contraseña BD |
| `DB_HOST` | `ep-xxx.aws.neon.tech` | Host BD |
| `DB_PORT` | `5432` | Puerto BD |
| `CORS_ALLOWED_ORIGINS` | `https://app.onrender.com` | Orígenes CORS permitidos |

---

## Próximos Pasos

1. ✅ Genera un `SECRET_KEY` seguro
2. ✅ Configura variables en Render
3. ✅ Deploy en Render.com
4. ✅ Prueba tu API

```bash
# Para generar SECRET_KEY:
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

¡Listo! Tu proyecto está configurado para producción en Render ✨
