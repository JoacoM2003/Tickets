# TicketSystem

Aplicación de gestión de incidencias desarrollada con Django. Permite crear, asignar y seguir tickets, registrar comentarios y ver el historial de cambios de estado.

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

## Roles y permisos

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
- PostgreSQL
- WhiteNoise
- Git / GitHub

## Arquitectura del proyecto

El proyecto está organizado como una aplicación Django clásica:

- `config/`: configuración del proyecto, URLs globales y WSGI.
- `tickets/`: aplicación principal con modelos, vistas, formularios, URLs y templates.
- `tickets/templates/`: vistas HTML para dashboard, lista de tickets, detalle de ticket y administración de usuarios.
- `tickets/models.py`: entidades de `Ticket`, `Comentario` e `HistorialEstado`.
- `tickets/views.py`: vistas basadas en clases y funciones para el flujo de la aplicación.
- `tickets/forms.py`: formularios de creación y actualización de tickets y usuarios.
- `tickets/tests.py`: pruebas automatizadas de rutas, permisos, creación y validación.
- `requirements.txt`: dependencias del proyecto.

## Modelo de datos

- `Ticket`: representa una incidencia con título, descripción, estado, prioridad, responsable asignado y creador.
- `Comentario`: comentario asociado a un ticket con autor y fecha.
- `HistorialEstado`: registro de cada cambio de estado de un ticket, con usuario y nota opcional.
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
   - `CSRF_TRUSTED_ORIGINS=` si es necesario.

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

## Tests

Ejecutar las pruebas con:

```bash
python manage.py test
```

Las pruebas cubren:

- acceso y autenticación de usuarios.
- creación y actualización de tickets.
- comentarios en tickets.
- filtros, búsqueda, ordenamiento y paginación.
- reglas de permisos y administración de usuarios.
- historial de cambios de estado.

## Deploy

El proyecto está preparado para desplegarse como una aplicación Django estándar con PostgreSQL y WhiteNoise para archivos estáticos. No se encuentra en el repositorio una configuración específica de despliegue para una plataforma concreta.

## Uso básico

1. Iniciar sesión en la aplicación.
2. Crear un nuevo ticket desde el dashboard o la lista de tickets.
3. Consultar el ticket en el listado y ver su detalle.
4. Asignar responsables o autoasignarse si el ticket no tiene responsable.
5. Cambiar estado y prioridad desde el detalle del ticket.
6. Agregar comentarios para registrar observaciones.
7. Revisar el historial de estados y las métricas del dashboard.

## Uso de IA en el desarrollo

Este proyecto fue desarrollado utilizando asistentes de IA como apoyo en distintas etapas: ChatGPT y Claude para planificación de arquitectura, modelado de datos y definición de reglas de negocio, y Copilot/Cursor para la implementación del código. Las decisiones de diseño y las reglas de negocio fueron guiadas y revisadas de forma manual, y se validaron con una suite de 46 tests automatizados que permitieron detectar y corregir comportamientos generados incorrectamente.

## Estado del proyecto

TicketSystem es una aplicación funcional de gestión de tickets con autenticación, administración de usuarios, seguimiento de incidencias, historial de estados y un dashboard de métricas. Está lista para ejecutarse localmente y ampliarse con nuevas funcionalidades según las necesidades.
