# Cloudflare DDNS Panel

Panel web de administración para un servicio de actualización dinámica de DNS (DDNS) sobre Cloudflare. Sustituye la configuración basada en `config.json` y ejecución por línea de comandos por una aplicación completa con base de datos, autenticación multiusuario, panel visual, auditoría y automatización de comprobaciones de IP.

Creado por [alejandroalsa](https://github.com/alejandroalsa/cloudflare-ddns-updater).

## Tabla de contenidos

- [Descripción general](#descripción-general)
- [Características](#características)
- [Arquitectura y stack tecnológico](#arquitectura-y-stack-tecnológico)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Requisitos previos](#requisitos-previos)
- [Instalación con Docker (recomendado)](#instalación-con-docker-recomendado)
- [Instalación como servicio systemd (sin Docker)](#instalación-como-servicio-systemd-sin-docker)
- [Variables de entorno](#variables-de-entorno)
- [Primer acceso](#primer-acceso)
- [Uso del panel](#uso-del-panel)
- [Migración desde config.json](#migración-desde-configjson)
- [Cambios de esquema de base de datos](#cambios-de-esquema-de-base-de-datos)
- [Seguridad](#seguridad)
- [Resolución de problemas](#resolución-de-problemas)
- [Licencia](#licencia)

## Descripción general

El proyecto está dividido en dos servicios independientes:

- **Backend**: API REST construida con FastAPI y SQLAlchemy sobre una base de datos SQLite. Incluye un planificador en segundo plano (APScheduler) que sustituye al script original `cloudflare-ddns.py`, comprobando periódicamente la IP pública y actualizando los registros DNS necesarios en Cloudflare.
- **Frontend**: aplicación de página única construida con Vue 3, Vite y TypeScript, con un sistema de componentes propio de estilo shadcn-vue sobre Tailwind CSS.

Ambos servicios se despliegan juntos mediante Docker Compose, o por separado como servicios systemd tradicionales.

## Características

### Gestión de dominios y registros DNS

- Alta, edición y baja de dominios (zonas de Cloudflare), cada uno con su propio API Token y Zone ID.
- Registros de tipo A (IPv4) y AAAA (IPv6).
- Comprobación automática periódica de la IP pública, con intervalo configurable.
- Comprobación manual bajo demanda: de todos los dominios a la vez, de un dominio concreto o de un registro individual.
- Edición manual de IP, estado de proxy (nube de Cloudflare) y TTL, tanto de un registro individual como de varios registros seleccionados a la vez (edición en bloque), siempre que sean del mismo tipo.
- Posibilidad de crear un registro directamente en Cloudflare desde el panel (indicando la IP inicial), en lugar de tener que crearlo antes manualmente desde el dashboard de Cloudflare.
- Prueba de conexión con Cloudflare (validación de API Token y Zone ID) antes de guardar un dominio.
- Búsqueda en vivo de dominios y registros.
- Importación y exportación de dominios en formato JSON, compatible con el antiguo `config.json`. Incluye plantilla descargable de ejemplo.

### Notificaciones

- Envío de correo electrónico cuando cambia la IP pública, con plantilla HTML personalizable.
- Múltiples destinatarios, con campos independientes de Para, CC y CCO.
- Botón de envío de correo de prueba para verificar la configuración SMTP sin esperar a un cambio real de IP.

### Usuarios y control de acceso

- Roles de usuario: administrador (gestión completa) y solo lectura (consulta).
- Cada usuario puede editar su propio nombre de usuario, correo electrónico y contraseña.
- Los administradores pueden crear, editar y eliminar cualquier usuario.
- Límite de intentos de inicio de sesión: tras varios intentos fallidos, la cuenta queda bloqueada temporalmente.

### Verificación en dos pasos (2FA)

- Activación mediante aplicación de autenticación TOTP estándar (Google Authenticator, Authy, 1Password, etc.), con código QR.
- Códigos de recuperación de un solo uso, generados al activar el 2FA y regenerables en cualquier momento.
- Un usuario puede desactivar su propio 2FA con su contraseña.
- Un administrador puede desactivar el 2FA de cualquier otro usuario, por ejemplo si ha perdido el acceso a su aplicación de autenticación y a sus códigos de recuperación.

### Panel y visualización

- Panel principal con estado actual (IP pública, dominios y registros gestionados), gráfica de evolución histórica de la IP y tabla de comprobaciones recientes.
- Historial de comprobaciones paginado, con filtro por rango de fechas.
- Registro de auditoría de acciones administrativas (creación, edición y borrado de dominios, registros, usuarios y ajustes; inicios de sesión; comprobaciones manuales; cambios de 2FA), también paginado y filtrable por fecha, con exportación a CSV o JSON. Cada entrada puede desplegarse para ver una comparación clara entre el estado anterior y el posterior al cambio.
- Tema claro, oscuro o según el sistema operativo, configurable por cada usuario desde su perfil. Sin sesión iniciada, se usa siempre el tema del sistema.
- Diseño adaptado a dispositivos móviles: en pantallas pequeñas el menú lateral se sustituye por un menú desplegable.
- Confirmación mediante diálogo en toda acción de borrado, sin depender de los cuadros de confirmación nativos del navegador.

## Arquitectura y stack tecnológico

| Componente        | Tecnología                                             |
|-------------------|---------------------------------------------------------|
| Backend           | Python, FastAPI, SQLAlchemy, SQLite                     |
| Autenticación      | JWT, bcrypt (contraseñas), TOTP (pyotp) para 2FA         |
| Tareas periódicas | APScheduler                                              |
| Frontend          | Vue 3, TypeScript, Vite, Pinia, Vue Router               |
| Estilos           | Tailwind CSS, componentes propios de estilo shadcn-vue   |
| Gráficas          | Chart.js                                                  |
| Contenedores      | Docker, Docker Compose, Nginx (para servir el frontend)  |

## Estructura del proyecto

```
cloudflare-ddns-panel/
├── backend/
│   ├── app/
│   │   ├── main.py            # Punto de entrada, arranque y creación de tablas
│   │   ├── models.py          # Modelos SQLAlchemy (usuarios, zonas, registros, auditoría...)
│   │   ├── schemas.py         # Esquemas Pydantic de entrada y salida de la API
│   │   ├── auth.py            # Hashing de contraseñas, JWT, límite de intentos de login
│   │   ├── totp.py            # Generación de secretos, QR y códigos de recuperación 2FA
│   │   ├── audit.py           # Utilidad de registro de auditoría
│   │   ├── scheduler.py       # Lógica de comprobación y actualización de DNS
│   │   ├── email_utils.py     # Envío de notificaciones por correo
│   │   └── routers/           # Endpoints de la API (auth, zones, users, settings, status, audit)
│   ├── templates/email.html   # Plantilla HTML de los correos de notificación
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── views/              # Login, Dashboard, Domains, Settings, Users, Profile, Audit
│   │   ├── components/         # Layout y componentes de interfaz reutilizables
│   │   ├── stores/              # Estado global (autenticación, confirmaciones)
│   │   ├── lib/                 # Cliente de API, utilidades, gestión de tema
│   │   └── router/              # Definición de rutas y control de acceso
│   ├── public/                  # Logo y favicon
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
├── docs/systemd/                # Plantillas para despliegue sin Docker
└── README.md
```

## Requisitos previos

- Docker y Docker Compose (para la instalación recomendada), o
- Python 3.11 o superior y Node.js 20 o superior (para instalación manual / systemd)
- Una cuenta de Cloudflare con al menos un dominio gestionado, y un API Token con permisos `Zone.DNS:Edit` y `Zone.Zone:Read`

## Instalación con Docker (recomendado)

1. Clona o copia el proyecto en el servidor y accede al directorio raíz.

2. Configura las variables de entorno del backend:

   ```bash
   cp backend/.env.example backend/.env
   nano backend/.env
   ```

   Como mínimo, cambia `JWT_SECRET` por un valor aleatorio propio y `ADMIN_PASSWORD` por una contraseña segura. Puedes generar un secreto con:

   ```bash
   openssl rand -hex 32
   ```

3. (Opcional) Si el puerto 80 ya está en uso en el servidor, copia también el `.env` de la raíz para cambiar los puertos publicados:

   ```bash
   cp .env.example .env
   nano .env
   ```

   ```
   FRONTEND_PORT=8080
   BACKEND_PORT=8000
   ```

4. Levanta los contenedores:

   ```bash
   docker compose up -d --build
   ```

5. Accede al panel en `http://<host>` (o en el puerto que hayas configurado) e inicia sesión con las credenciales definidas en `backend/.env`.

Comandos habituales:

```bash
docker compose logs -f backend      # ver logs del backend y del planificador
docker compose restart backend      # reiniciar solo el backend
docker compose down                 # detener los contenedores (los datos persisten)
docker compose down -v              # detener y BORRAR también los datos (usar con cuidado)
docker compose up -d --build        # reconstruir tras actualizar el código
```

Los datos se almacenan en el volumen Docker `ddns_data`, montado en `/app/data` dentro del contenedor del backend, por lo que persisten entre reinicios y reconstrucciones mientras no se use `down -v`.

## Instalación como servicio systemd (sin Docker)

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env
```

Copia y ajusta el archivo de servicio:

```bash
sudo cp ../docs/systemd/ddns-backend.service /etc/systemd/system/
sudo nano /etc/systemd/system/ddns-backend.service
sudo systemctl daemon-reload
sudo systemctl enable --now ddns-backend
sudo systemctl status ddns-backend
```

### Frontend

```bash
cd frontend
npm install
npm run build
```

Esto genera los archivos estáticos en `frontend/dist`. Sírvelos con cualquier servidor web, redirigiendo `/api` al backend. Hay una plantilla de Nginx lista en `docs/systemd/nginx-ddns-panel.conf.example`:

```bash
sudo cp docs/systemd/nginx-ddns-panel.conf.example /etc/nginx/sites-available/ddns-panel
sudo nano /etc/nginx/sites-available/ddns-panel
sudo ln -s /etc/nginx/sites-available/ddns-panel /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

## Variables de entorno

### `backend/.env`

| Variable              | Descripción                                                                 | Valor por defecto            |
|-----------------------|-------------------------------------------------------------------------------|-------------------------------|
| `DATABASE_URL`        | Cadena de conexión a la base de datos SQLite                                 | `sqlite:///./data/ddns.db`   |
| `JWT_SECRET`          | Clave usada para firmar los tokens de sesión. Cámbiala siempre.              | (debe personalizarse)        |
| `JWT_ALGORITHM`       | Algoritmo de firma del token                                                  | `HS256`                      |
| `JWT_EXPIRE_MINUTES`  | Minutos de validez de la sesión                                              | `10080` (7 días)             |
| `ADMIN_USERNAME`      | Usuario administrador creado en el primer arranque                           | `admin`                      |
| `ADMIN_PASSWORD`      | Contraseña de ese usuario administrador                                      | `admin`                      |
| `ADMIN_EMAIL`         | Correo asociado al usuario administrador inicial                             | `admin@example.com`          |
| `CORS_ORIGINS`        | Orígenes permitidos para peticiones desde el navegador, separados por comas  | `http://localhost:5173,http://localhost:80` |

El usuario administrador definido por `ADMIN_USERNAME` y `ADMIN_PASSWORD` solo se crea automáticamente si la tabla de usuarios está vacía. Cambiar estas variables después de que la base de datos ya tenga usuarios no modifica ningún usuario existente.

### `.env` (raíz, opcional)

Solo necesario para cambiar los puertos publicados por Docker Compose sin editar `docker-compose.yml`:

| Variable         | Descripción                                    | Valor por defecto |
|------------------|--------------------------------------------------|--------------------|
| `FRONTEND_PORT`  | Puerto en el que se sirve el panel web           | `80`               |
| `BACKEND_PORT`   | Puerto en el que se expone la API directamente   | `8000`             |

El resto de la configuración (servicio de IP pública, SMTP, IPv6, intervalo de comprobación, etc.) se gestiona desde la sección Ajustes del propio panel, no mediante variables de entorno.

## Primer acceso

1. Entra con el usuario y contraseña definidos en `backend/.env`.
2. Cambia la contraseña por defecto desde Mi perfil.
3. (Recomendado) Activa la verificación en dos pasos desde Mi perfil y guarda los códigos de recuperación que se muestran, ya que solo se muestran una vez.
4. Da de alta tus dominios desde la sección Dominios, o impórtalos desde un archivo JSON si ya tenías una configuración previa.
5. Revisa la sección Ajustes para configurar el intervalo de comprobación, el servicio de IP pública, IPv6 (si lo necesitas) y las notificaciones por correo.

## Uso del panel

- **Dashboard**: estado general, gráfica de IP y comprobación manual inmediata de todos los dominios.
- **Dominios**: alta, edición y baja de dominios y registros; comprobación y edición manual; importación y exportación.
- **Ajustes** (solo administradores): parámetros globales de comprobación de IP y notificaciones por correo.
- **Usuarios** (solo administradores): gestión de cuentas, roles y 2FA de otros usuarios.
- **Auditoría** (solo administradores): historial de acciones administrativas, con exportación.
- **Mi perfil**: datos de la cuenta propia, 2FA y preferencia de tema.

## Migración desde config.json

Si ya tenías una instalación del script original con un `config.json`, no es necesario editar la base de datos a mano. Desde el panel:

1. Entra como administrador y ve a Dominios.
2. Usa el botón Importar JSON con un archivo que siga esta estructura (la misma que `config.json`):

   ```json
   {
     "domains": {
       "ejemplo.com": {
         "api_token": "token_de_api_de_cloudflare",
         "zone_id": "zone_id_de_cloudflare",
         "records": ["ejemplo.com", "www.ejemplo.com"]
       }
     }
   }
   ```

3. Los dominios nuevos se crean y los que ya existan con el mismo nombre se actualizan, añadiendo los registros que falten.

También puedes descargar una plantilla de ejemplo con el mismo formato desde el botón Plantilla.

## Cambios de esquema de base de datos

Al arrancar, el backend crea automáticamente las tablas que falten en la base de datos, pero no modifica las tablas que ya existen. Esto significa que si actualizas el código sobre una instalación que ya tiene datos y esa actualización añade columnas nuevas a una tabla existente, el backend puede fallar al arrancar con un error de tipo `no such column`.

Si esto ocurre, la solución es aplicar manualmente los cambios de esquema necesarios contra el archivo de base de datos, por ejemplo:

```bash
docker compose down
docker compose run --rm backend python3 -c "
import sqlite3
conn = sqlite3.connect('/app/data/ddns.db')
cur = conn.cursor()
cur.execute('ALTER TABLE nombre_tabla ADD COLUMN nombre_columna TIPO')
conn.commit()
conn.close()
"
docker compose up -d --build
```

Puedes comprobar la estructura actual de cualquier tabla con:

```bash
docker compose run --rm backend python3 -c "
import sqlite3
conn = sqlite3.connect('/app/data/ddns.db')
cur = conn.cursor()
cur.execute('PRAGMA table_info(nombre_tabla)')
print(cur.fetchall())
"
```

En una instalación completamente nueva no es necesario aplicar ninguna migración: la base de datos se crea desde cero con el esquema completo la primera vez que arranca el backend.

Para evitar este proceso manual en el futuro, la incorporación de una herramienta de migraciones como Alembic queda pendiente como mejora.

## Seguridad

- Cambia siempre `JWT_SECRET` y la contraseña del administrador por defecto antes de exponer el panel a redes no confiables.
- Los tokens de API de Cloudflare se almacenan en la base de datos; protege el acceso al archivo o volumen donde se guarda.
- El límite de intentos de inicio de sesión se mantiene en memoria del proceso y se reinicia si el backend se reinicia.
- El registro de auditoría nunca guarda contraseñas en texto plano, incluida la contraseña SMTP, que se redacta automáticamente.
- No hay revocación de sesiones activas: un token JWT sigue siendo válido hasta que expira, aunque se cambie la contraseña.
- Se recomienda ejecutar el panel detrás de HTTPS, por ejemplo mediante un proxy inverso como Nginx, Caddy o Traefik con un certificado válido.

## Resolución de problemas

**El backend devuelve 502 o no arranca tras actualizar el código**
Consulta los logs con `docker compose logs -f backend`. Si el error menciona `no such column` o `no such table`, revisa la sección [Cambios de esquema de base de datos](#cambios-de-esquema-de-base-de-datos).

**No puedo iniciar sesión y no es un problema de credenciales**
Comprueba en las herramientas de desarrollador del navegador (pestaña Red) el código de estado real de la petición a `/api/auth/login`. Un fallo de red o de CORS puede mostrar el mismo mensaje genérico que unas credenciales incorrectas. Verifica que `CORS_ORIGINS` en `backend/.env` incluye el origen desde el que accedes.

**El puerto 80 ya está en uso**
Define `FRONTEND_PORT` en el `.env` de la raíz con un puerto libre, tal como se explica en la sección de instalación.

**Los cambios de interfaz no se ven tras desplegar**
Refresca el navegador sin caché (Ctrl+Shift+R o equivalente), ya que los archivos estáticos pueden quedar cacheados.

## Licencia

[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)
