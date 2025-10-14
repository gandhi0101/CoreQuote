# CoreQuote en Railway

Esta guía explica paso a paso cómo desplegar este proyecto en [Railway](https://railway.app/) usando el repositorio actual.

## 1. Preparar el repositorio

1. Asegúrate de que tus cambios estén en la rama que vas a conectar con Railway y que el archivo `requirements.txt` del directorio raíz apunte a `backend/requirements.txt` (esto ya está configurado con:
   ```txt
   -r backend/requirements.txt
   ```
   Railway detecta la app de Python gracias a ese archivo).
2. Confirma que el archivo `Procfile` esté presente con el proceso `web: bash backend/start.sh`.
3. Sube todos los cambios al remoto (por ejemplo `git push origin main`).

## 2. Crear el proyecto en Railway

1. En Railway, crea un **New Project** y elige **Deploy from GitHub repo**.
2. Autoriza tu cuenta si es necesario, busca este repositorio y selecciónalo.
3. En la sección **Settings → Build & Deploy**, verifica que:
   - El **Root Directory** sea la raíz del repo (`/`).
   - El **Build Command** se deje vacío para que Railway use el buildpack de Python.
   - El **Start Command** quede vacío (Railway usará el `Procfile`).

## 3. Añadir la base de datos de PostgreSQL

1. En el dashboard del proyecto, abre la pestaña **Resources** y añade un nuevo servicio de tipo **PostgreSQL** (puedes usar Railway Postgres o conectar uno externo).
2. Una vez creado, Railway inyectará automáticamente la variable `DATABASE_URL` en tu servicio web. No necesitas copiarla manualmente.

## 4. Configurar variables de entorno

En **Variables**, añade las siguientes variables (usa valores reales):

| Variable | Ejemplo | Descripción |
| --- | --- | --- |
| `SECRET_KEY` | `django-insecure-...` | Clave secreta de Django. Genera una con `python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"` |
| `DEBUG` | `False` | Mantén `False` en producción. |
| `ALLOWED_HOSTS` | `pleasant-curiosity.up.railway.app` | Incluye el dominio de Railway (lo verás en la pestaña **Settings → Domains**). |
| `CSRF_TRUSTED_ORIGINS` | `https://pleasant-curiosity.up.railway.app` | Igual que el host pero con esquema `https://`. |
| `DJANGO_SETTINGS_MODULE` | `config.settings` | Opcional si deseas forzarlo; Django ya lo infiere desde el `manage.py`. |
| `CONN_MAX_AGE` | `60` | (Opcional) Segundos que Django mantiene abierta la conexión a la base de datos. |

Railway añade automáticamente:

- `PORT`: Puerto donde debe escuchar Gunicorn.
- `RAILWAY_PUBLIC_DOMAIN`: Dominio público (usado en `settings.py`).
- `DATABASE_URL`: Cadena de conexión a Postgres.

## 5. Variables locales para usar los comandos de Django

Si necesitas ejecutar comandos de Django en un **Railway Deployment**, abre la pestaña **Deployments → ... → Launch Console** y usa, por ejemplo:

```bash
python manage.py createsuperuser
```

El script `backend/start.sh` ya corre `migrate` y `collectstatic` antes de iniciar el servidor, por lo que no necesitas hacerlo manualmente en cada despliegue.

## 6. Verificar el despliegue

1. Cuando Railway termine de construir la imagen, verás el estado **Running**.
2. Abre el dominio listado en **Settings → Domains**.
3. Si aparece un error 500, revisa los **Logs** del deployment y confirma que las variables de entorno estén correctas.

## 7. Solución de problemas comunes

| Error | Causa probable | Solución |
| --- | --- | --- |
| `Failed to build image. Please check the build logs for more details.` con referencia a `pip install` | Railway no detectó el buildpack de Python o faltó una dependencia | Verifica que el `requirements.txt` esté en la raíz y contenga `-r backend/requirements.txt`. Railway descargará todas las dependencias listadas en `backend/requirements.txt`. |
| Error de hosts (`DisallowedHost`) | Falta el dominio en `ALLOWED_HOSTS` | Agrega el dominio de Railway en `ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS`. |
| Migraciones sin aplicar | Alguna migración falló por datos o permisos | Revisa los logs y, si es necesario, ejecuta `python manage.py migrate` manualmente desde la consola del deployment. |

## 8. Logos y datos fiscales por usuario

- Cada usuario puede cargar su logotipo y datos fiscales desde **Mis datos → Identidad fiscal y branding**. La información se guarda en la carpeta `backend/media/` bajo `user-assets/<id>/logo.png` y se inserta automáticamente en los PDF.
- En Railway (plan gratuito) la forma más simple de conservar estos archivos entre despliegues es habilitar un [Volume](https://docs.railway.com/reference/volumes) y montarlo en `/workspace/CoreQuote/backend/media` para el servicio web. Así, los logos permanecen disponibles sin volver a subirlos.
- Si prefieres delegar el almacenamiento a un servicio gratuito externo, puedes apuntar `DEFAULT_FILE_STORAGE` a proveedores como [Cloudinary](https://cloudinary.com/) o [Google Cloud Storage](https://cloud.google.com/storage) (tienen capas sin costo) usando `django-storages`. Solo necesitarías añadir la dependencia, credenciales por variable de entorno y actualizar la configuración.

Con esto tu despliegue debería completarse correctamente en Railway. Si necesitas personalizar la configuración (por ejemplo usar Redis, enviar correos, etc.), añade los servicios en Railway y exporta sus variables de entorno siguiendo el mismo patrón.
