# TicketSystem (TicketLite Cloud)

Aplicación de gestión de incidencias desarrollada con Django. Permite crear, asignar y seguir tickets, registrar comentarios y ver el historial de cambios de estado. Además, envía notificaciones asíncronas mediante servicios de AWS, sugiere la prioridad inicial de cada ticket con IA y permite reportar incidencias sin necesidad de tener una cuenta.

## Descripción

TicketSystem resuelve la gestión interna de solicitudes e incidencias dentro de un equipo o una organización. La aplicación centraliza la creación de tickets, el seguimiento por estado y prioridad, la asignación de responsables y el registro de comentarios e historial.

El objetivo es ofrecer un sistema sencillo para controlar el ciclo de vida de cada incidencia sin depender de herramientas externas.

## Funcionalidades implementadas

- Autenticación de usuarios con login/logout.
- Gestión de usuarios por administradores (`is_staff`): listado, creación, edición y restablecimiento de contraseña.
- Creación y consulta de tickets.
- Estados de tickets: `Pendiente`, `En proceso`, `Resuelto`.
- Prioridades de tickets: `Baja`, `Media`, `Alta`.
- Asignación de responsables de ticket.
- Reglas de permisos para actualización de tickets:
  - solo el responsable asignado o un administrador puede cambiar estado/prioridad;
  - los tickets sin responsable pueden autoasignarse por el propio usuario.
- Comentarios en cada ticket.
- Historial de cambios de estado.
- Dashboard con métricas por estado y prioridad, y últimos tickets actualizados.
- Filtros, búsqueda y ordenamiento en la lista de tickets.
- Paginación en listados de tickets y usuarios.
- Notificaciones asíncronas: cada cambio de estado publica un evento en Amazon SQS, que dispara una función AWS Lambda y envía un email mediante Amazon SNS.
- Prioridad inicial con IA: al crear un ticket, la API de Gemini sugiere la prioridad a partir del ticket. Si la IA no responde a tiempo o falla, el ticket se crea con prioridad `Media`. Luego el responsable o un administrador puede modificarla.
- Reporte público: cualquier persona puede reportar un problema sin iniciar sesión y seguir el estado de ese ticket con un código de seguimiento único. El ticket queda sin responsable y se gestiona desde el sistema interno como cualquier otro.

## Roles y permisos

- **Visitante (sin sesión)**:
  - puede reportar un problema (título y descripción).
  - puede consultar el estado del ticket que reportó usando su código de seguimiento, y solo de ese ticket.

- **Usuario autenticado**:
  - puede ver dashboard y lista de tickets.
  - puede crear tickets.
  - puede ver el detalle de un ticket y agregar comentarios.
  - puede autoasignarse un ticket cuando éste aún no tiene responsable.

- **Responsable de un ticket**:
  - puede cambiar el estado y la prioridad del ticket asignado.
  - puede agregar comentarios sobre el ticket.

- **Administrador (`is_staff=True`)**:
  - puede gestionar usuarios desde el panel de administración interno.
  - puede editar cualquier ticket y reasignar responsables.
  - puede restablecer contraseñas de otros usuarios.

## Stack tecnológico

- Python 3
- Django 6
- Bootstrap 5
- PostgreSQL (Neon en producción)
- Gunicorn y WhiteNoise
- Docker / Docker Compose
- AWS: SQS, Lambda, SNS, CloudWatch e IAM
- API de Gemini (paquete `google-genai`)
- Render (deploy)
- Git / GitHub

## Arquitectura del proyecto

El proyecto está organizado como una aplicación Django clásica:

- `config/`: configuración del proyecto, URLs globales y WSGI.
- `tickets/`: aplicación principal con modelos, vistas, formularios, URLs y templates.
- `tickets/templates/`: vistas HTML para dashboard, lista de tickets, detalle de ticket, administración de usuarios y reporte público.
- `tickets/models.py`: entidades de `Ticket`, `Comentario` e `HistorialEstado`.
- `tickets/views.py`: vistas basadas en clases y funciones para el flujo de la aplicación.
- `tickets/forms.py`: formularios de creación y actualización de tickets y usuarios, y formulario del reporte público.
- `tickets/signals.py`: publica en SQS un mensaje por cada registro nuevo del historial de estados.
- `tickets/services.py`: consulta a la API de Gemini para sugerir la prioridad inicial.
- `tickets/tests.py`: pruebas automatizadas de rutas, permisos, creación, validación, notificaciones y reporte público.
- `docs/`: documentación y entregas del proyecto.
- `AI-DECISIONS.md`: registro de las decisiones tomadas con asistencia de IA.
- `Dockerfile`, `docker-compose.yml` y `entrypoint.sh`: ejecución con contenedores.
- `requirements.txt`: dependencias del proyecto.

### Flujo de notificaciones

Cuando cambia el estado de un ticket, un signal de Django publica un mensaje en una cola de Amazon SQS. La cola dispara una función AWS Lambda que publica el aviso en un topic de Amazon SNS, y SNS envía el email a la casilla suscripta al topic. La ejecución de la Lambda queda registrada en CloudWatch.

Los recursos de AWS (cola, función, topic y usuario IAM) se crearon desde la consola de AWS. El envío a SQS es "best effort": si falla, el ticket se crea igual.

## Modelo de datos

- `Ticket`: representa una incidencia con título, descripción, estado, prioridad, responsable asignado, creador y código de seguimiento (UUID único, opcional para los tickets anteriores al reporte público).
- `Comentario`: comentario asociado a un ticket con autor y fecha.
- `HistorialEstado`: registro de cada cambio de estado de un ticket, con usuario (vacío si lo reportó un visitante) y nota opcional.
- `User`: modelo de usuario de Django utilizado para creadores y responsables.

## Instalación y configuración local

1. Clonar el repositorio:
   ```bash
   git clone <url-del-repositorio>
   cd Tickets
   ```

2. Crear y activar un entorno virtual:
   ```bash
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Crear el archivo de entorno local:
   ```bash
   copy .env.example .env
   ```

5. Configurar variables de entorno en `.env`:
   - `SECRET_KEY`: clave secreta de Django.
   - `DEBUG=True` para desarrollo.
   - `ALLOWED_HOSTS=localhost,127.0.0.1`.
   - `DATABASE_URL=postgresql://usuario:password@localhost:5432/tickets`.
   - `CSRF_TRUSTED_ORIGINS=` si es necesario. Cada valor debe incluir el esquema, por ejemplo `https://mi-app.onrender.com`.
   - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION` y `SQS_QUEUE_URL`: credenciales y cola de AWS para las notificaciones.
   - `GEMINI_API_KEY`: clave de la API de Gemini. Si falta, la prioridad inicial queda en `Media`.
   - `GEMINI_MODEL` (opcional): modelo de Gemini a utilizar.

6. Configurar PostgreSQL local:
   - crear la base de datos `tickets`.
   - asegurar que el usuario y contraseña usados en `DATABASE_URL` existan.

7. Ejecutar migraciones:
   ```bash
   python manage.py migrate
   ```

8. Crear un superusuario:
   ```bash
   python manage.py createsuperuser
   ```

9. Iniciar el servidor de desarrollo:
   ```bash
   python manage.py runserver
   ```

### Ejecución con Docker

Como alternativa a los pasos 6 a 9, se puede levantar todo con contenedores:

```bash
docker compose up --build
```

Esto inicia la aplicación (con Gunicorn) y un contenedor de PostgreSQL, y aplica las migraciones al arrancar. La aplicación queda disponible en `http://localhost:8000`. En este modo la base de datos es la del contenedor, no la definida en `DATABASE_URL` del `.env`.

## Tests

Ejecutar las pruebas con:

```bash
python manage.py test
```

Las pruebas usan SQLite y simulan las llamadas a AWS y a la API de IA. Cubren:

- acceso y autenticación de usuarios.
- creación y actualización de tickets.
- comentarios en tickets.
- filtros, búsqueda, ordenamiento y paginación.
- reglas de permisos y administración de usuarios.
- historial de cambios de estado.
- notificaciones a SQS y prioridad inicial con IA.
- reporte público y seguimiento por código.

## Deploy

La aplicación está desplegada en Render, con base de datos PostgreSQL en Neon y las variables de entorno cargadas desde el panel de Render.

- Build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput`
- Start command: `gunicorn config.wsgi:application`

## Uso básico

1. Iniciar sesión en la aplicación.
2. Crear un nuevo ticket desde el dashboard o la lista de tickets. La prioridad inicial se asigna automáticamente.
3. Consultar el ticket en el listado y ver su detalle.
4. Asignar responsables o autoasignarse si el ticket no tiene responsable.
5. Cambiar estado y prioridad desde el detalle del ticket.
6. Agregar comentarios para registrar observaciones.
7. Revisar el historial de estados y las métricas del dashboard.

Sin iniciar sesión, desde la pantalla de login se puede reportar un problema o consultar el estado de un ticket ingresando su código de seguimiento.

## Documentación

- `docs/`: entregas y documentación del proyecto.
- `AI-DECISIONS.md`: decisiones técnicas asistidas por IA, con el problema, el prompt, la propuesta de la IA y la validación o corrección posterior.

## Estado del proyecto

TicketSystem es una aplicación funcional de gestión de tickets con autenticación, administración de usuarios, seguimiento de incidencias, historial de estados y un dashboard de métricas. Incorpora notificaciones asíncronas con servicios de AWS, prioridad inicial sugerida por IA y un canal público para reportar incidencias. Está desplegada en Render y lista para ampliarse con nuevas funcionalidades según las necesidades.