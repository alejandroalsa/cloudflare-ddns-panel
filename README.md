# Cloudflare DDNS Panel

Panel web para gestionar el actualizador de DNS dinámico de Cloudflare: alta de
dominios, registros, usuarios (admin / solo lectura) y configuración de SMTP,
todo desde una interfaz web en lugar de editar `config.json` a mano.

## 📁 Estructura

```
cloudflare-ddns-panel/
├── backend/                # API FastAPI + SQLite + scheduler DDNS
│   ├── app/
│   │   ├── main.py         # arranque, crea tablas y usuario admin inicial
│   │   ├── models.py       # User, Zone, Record, Setting, UpdateLog
│   │   ├── scheduler.py    # sustituye al bucle while de cloudflare-ddns.py
│   │   ├── routers/        # /api/auth /api/users /api/zones /api/settings /api/status
│   │   └── ...
│   ├── templates/email.html
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/                # Vue 3 + Vite + Tailwind + componentes estilo shadcn-vue
│   ├── src/
│   │   ├── views/           # Login, Dashboard, Domains, Settings, Users
│   │   ├── components/ui/   # Button, Input, Card, Dialog, Badge...
│   │   └── ...
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
└── docs/systemd/             # plantillas para correr sin Docker
```

## 🔑 Conceptos clave

- **Ya no existe `config.json`.** Los dominios, registros, usuarios y ajustes
  viven en una base de datos SQLite (`backend/data/ddns.db`), gestionable
  desde el panel.
- **Roles de usuario**: `admin` (gestiona dominios, usuarios y ajustes) y
  `viewer` (solo puede ver dashboard y dominios).
- **El scheduler sigue funcionando igual que antes** (comprueba la IP pública
  cada X segundos y actualiza los registros A en Cloudflare), pero ahora corre
  integrado en el proceso del backend y lee la configuración de la base de
  datos en lugar de ficheros.
- Al arrancar por primera vez se crea automáticamente un usuario admin con las
  credenciales de `ADMIN_USERNAME` / `ADMIN_PASSWORD` (por defecto
  `admin` / `admin`). **Cámbialas en el primer login.**

## ✨ Funcionalidades del panel

- **Comprobación manual**: botón "Comprobar ahora" a nivel global (Dashboard),
  por dominio y por registro individual (vista Dominios) — no hace falta
  esperar al intervalo automático.
- **Edición manual de IP y proxy**: cada registro tiene un botón de lápiz para
  fijar directamente una IP y activar/desactivar la nube de Cloudflare
  (proxied), sin pasar por la comprobación automática.
- **Historial borrable**: botón para vaciar el log de comprobaciones desde el
  Dashboard.
- **Múltiples destinatarios de email**: en Ajustes puedes indicar varios
  destinatarios (Para), CC y CCO, separados por comas.
- **Mostrar/ocultar contraseñas y tokens**: icono de ojo en los campos de
  contraseña (login, usuarios, SMTP) y en el API Token de Cloudflare.
- **Acordeón de registros por dominio**: cada dominio se puede expandir o
  colapsar; los que tienen pocos registros se muestran abiertos por defecto,
  el resto colapsados, para no saturar la vista si tienes muchos.
- **Buscador de dominios/registros**: filtra en vivo por nombre de dominio o
  de registro en la vista Dominios.
- **Mi perfil**: cualquier usuario puede cambiar su propio nombre de usuario,
  email y contraseña desde "Mi perfil" (en el menú lateral), sin necesitar
  permisos de admin.
- **Badges con icono**: los estados (proxied/DNS only, OK/pendiente,
  actualizado/error/sin cambios, activo/deshabilitado, admin/solo lectura)
  muestran un icono junto al texto para identificarlos de un vistazo.

---

## 🐳 Opción A: Despliegue con Docker (recomendado)

1. Configura las variables de entorno del backend:

   ```bash
   cp backend/.env.example backend/.env
   nano backend/.env   # cambia JWT_SECRET, ADMIN_PASSWORD, etc.
   ```

2. Levanta todo:

   ```bash
   docker compose up -d --build
   ```

3. Abre `http://<tu-servidor>` (puerto 80, servido por el frontend/Nginx, que
   redirige `/api` al backend). Inicia sesión con el usuario admin definido en
   `.env`.

4. Los datos persisten en el volumen `ddns_data` (SQLite), aunque
   reconstruyas los contenedores.

Comandos útiles:

```bash
docker compose logs -f backend   # ver logs del scheduler / actualizaciones
docker compose restart backend
docker compose down              # detener (los datos persisten en el volumen)
```

---

## 🖥️ Opción B: Como servicio systemd (sin Docker)

### 1. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env   # ajusta JWT_SECRET, ADMIN_PASSWORD, DATABASE_URL si quieres otra ruta
```

Copia y ajusta el servicio:

```bash
sudo cp ../docs/systemd/ddns-backend.service /etc/systemd/system/
sudo nano /etc/systemd/system/ddns-backend.service   # revisa rutas y usuario
sudo systemctl daemon-reload
sudo systemctl enable --now ddns-backend
sudo systemctl status ddns-backend
```

### 2. Frontend (build estático)

```bash
cd frontend
npm install
npm run build   # genera frontend/dist
```

Sirve `frontend/dist` con cualquier servidor web. Tienes una plantilla lista
en `docs/systemd/nginx-ddns-panel.conf.example` que sirve los estáticos y
redirige `/api` al backend (puerto 8000):

```bash
sudo cp docs/systemd/nginx-ddns-panel.conf.example /etc/nginx/sites-available/ddns-panel
sudo nano /etc/nginx/sites-available/ddns-panel   # ajusta server_name y rutas
sudo ln -s /etc/nginx/sites-available/ddns-panel /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

---

## ☁️ Obtener credenciales de Cloudflare

Igual que antes: **My Profile → API Tokens** en el dashboard de Cloudflare,
con permisos `Zone.DNS:Edit` y `Zone.Zone:Read`. El Zone ID se obtiene desde
la sección **API** de cada dominio en el dashboard. Ahora simplemente los
introduces desde el panel al crear un dominio nuevo, en vez de editar
`config.json`.

## 🔄 Migrar desde config.json

Si ya tenías un `config.json` con dominios configurados, entra al panel como
admin → **Dominios** → **Nuevo dominio**, e introduce para cada entrada de
`config.json`: el dominio, su `zone_id`, `api_token` y la lista de `records`.
No hace falta migrar nada a mano en la base de datos.

## 🔐 Notas de seguridad

- Cambia `JWT_SECRET` y la contraseña del admin por defecto antes de exponer
  el panel a Internet.
- Los tokens de API de Cloudflare se guardan en la base de datos; protege el
  acceso al fichero `ddns.db` / al volumen Docker.
- Se recomienda poner el panel detrás de HTTPS (por ejemplo con un reverse
  proxy tipo Caddy/Traefik o certificados de Let's Encrypt en tu Nginx).

## 📝 Licencia

MIT, igual que el proyecto original.
