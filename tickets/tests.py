from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from tickets.models import Ticket, Comentario, HistorialEstado


class ComentarioTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='ticketuser',
            password='ticketpassword',
            first_name='Ana',
            last_name='García',
        )
        self.ticket = Ticket.objects.create(
            titulo='Ticket de prueba',
            descripcion='Descripción de prueba',
            creado_por=self.user,
        )
        self.client.login(username='ticketuser', password='ticketpassword')

    def test_detalle_muestra_seccion_comentarios(self):
        url = reverse('tickets:detalle', kwargs={'pk': self.ticket.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Comentarios')
        self.assertContains(response, 'Nuevo comentario')
        self.assertContains(response, 'Este ticket aún no tiene comentarios')
        self.assertContains(response, 'id="comentarios"')

    def test_publicar_comentario(self):
        url = reverse('tickets:comentar', kwargs={'pk': self.ticket.pk})
        response = self.client.post(url, {'texto': '  Comentario de prueba  '})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Comentario.objects.count(), 1)
        comentario = Comentario.objects.get()
        self.assertEqual(comentario.texto, 'Comentario de prueba')
        self.assertEqual(comentario.autor, self.user)
        self.assertEqual(comentario.ticket, self.ticket)

    def test_comentario_vacio_rechazado(self):
        url = reverse('tickets:comentar', kwargs={'pk': self.ticket.pk})
        response = self.client.post(url, {'texto': '   '})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Comentario.objects.count(), 0)

    def test_lista_muestra_cantidad_comentarios(self):
        Comentario.objects.create(
            ticket=self.ticket,
            autor=self.user,
            texto='Uno',
        )
        Comentario.objects.create(
            ticket=self.ticket,
            autor=self.user,
            texto='Dos',
        )
        url = reverse('tickets:lista')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'title="2 comentario(s)"')

    def test_detalle_muestra_autor_y_total(self):
        Comentario.objects.create(
            ticket=self.ticket,
            autor=self.user,
            texto='Hola equipo',
        )
        url = reverse('tickets:detalle', kwargs={'pk': self.ticket.pk})
        response = self.client.get(url)
        self.assertContains(response, 'Ana García')
        self.assertContains(response, 'Hola equipo')
        self.assertContains(response, 'href="#comentarios"')
        self.assertEqual(response.context['total_comentarios'], 1)


class UserABMTests(TestCase):
    def setUp(self):
        # Create a regular user
        self.regular_user = User.objects.create_user(
            username='regularuser',
            password='regularpassword',
            first_name='Regular',
            last_name='User',
            email='regular@example.com'
        )
        # Create a staff user
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='staffpassword',
            first_name='Staff',
            last_name='User',
            email='staff@example.com',
            is_staff=True
        )

    def test_anonymous_user_redirected(self):
        """Unauthenticated users should be redirected to login page."""
        urls = [
            reverse('tickets:usuario_lista'),
            reverse('tickets:usuario_crear'),
            reverse('tickets:usuario_editar', kwargs={'pk': self.regular_user.pk}),
            reverse('tickets:usuario_password', kwargs={'pk': self.regular_user.pk}),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn('/accounts/login/', response.url)

    def test_regular_user_forbidden(self):
        """Logged-in users without is_staff=True should get 403 Forbidden."""
        self.client.login(username='regularuser', password='regularpassword')
        urls = [
            reverse('tickets:usuario_lista'),
            reverse('tickets:usuario_crear'),
            reverse('tickets:usuario_editar', kwargs={'pk': self.regular_user.pk}),
            reverse('tickets:usuario_password', kwargs={'pk': self.regular_user.pk}),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 403)

    def test_staff_user_access(self):
        """Logged-in staff users should access the views successfully (HTTP 200)."""
        self.client.login(username='staffuser', password='staffpassword')
        urls = [
            reverse('tickets:usuario_lista'),
            reverse('tickets:usuario_crear'),
            reverse('tickets:usuario_editar', kwargs={'pk': self.regular_user.pk}),
            reverse('tickets:usuario_password', kwargs={'pk': self.regular_user.pk}),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

    def test_user_creation(self):
        """Staff user can create a new user."""
        self.client.login(username='staffuser', password='staffpassword')
        url = reverse('tickets:usuario_crear')
        data = {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'new@example.com',
            'password1': 'newsecurepassword123',
            'password2': 'newsecurepassword123',
            'is_active': True,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Should redirect to list on success
        
        # Verify user exists
        new_user = User.objects.filter(username='newuser').first()
        self.assertIsNotNone(new_user)
        self.assertEqual(new_user.first_name, 'New')
        self.assertEqual(new_user.last_name, 'User')
        self.assertEqual(new_user.email, 'new@example.com')
        self.assertTrue(new_user.is_active)
        self.assertFalse(new_user.is_staff)

    def test_user_editing_and_deactivation(self):
        """Staff user can edit and deactivate a user."""
        self.client.login(username='staffuser', password='staffpassword')
        url = reverse('tickets:usuario_editar', kwargs={'pk': self.regular_user.pk})
        data = {
            'username': 'regularuser',
            'first_name': 'UpdatedRegular',
            'last_name': 'UpdatedUser',
            'email': 'updated@example.com',
            # Uncheck active and staff
            'is_active': False,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        # Verify user attributes are updated
        self.regular_user.refresh_from_db()
        self.assertEqual(self.regular_user.first_name, 'UpdatedRegular')
        self.assertEqual(self.regular_user.last_name, 'UpdatedUser')
        self.assertEqual(self.regular_user.email, 'updated@example.com')
        self.assertFalse(self.regular_user.is_active)

    def test_user_password_reset(self):
        """Staff user can reset another user's password."""
        self.client.login(username='staffuser', password='staffpassword')
        url = reverse('tickets:usuario_password', kwargs={'pk': self.regular_user.pk})
        data = {
            'new_password1': 'brandnewpassword123',
            'new_password2': 'brandnewpassword123',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        # Verify user can log in with new password
        login_success = self.client.login(username='regularuser', password='brandnewpassword123')
        self.assertTrue(login_success)


class DashboardTests(TestCase):
    def setUp(self):
        # Create regular user
        self.user = User.objects.create_user(
            username='dashboarduser',
            password='dashboardpassword',
            first_name='Juan',
            last_name='Pérez'
        )
        
    def test_anonymous_user_redirected_to_login(self):
        """Unauthenticated user accessing the root / dashboard should be redirected."""
        response = self.client.get(reverse('tickets:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_authenticated_user_can_access_dashboard(self):
        """Authenticated user can load the dashboard with code 200."""
        self.client.login(username='dashboarduser', password='dashboardpassword')
        response = self.client.get(reverse('tickets:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')
        self.assertContains(response, 'Resumen general del sistema de incidencias')
        # Check welcome banner is shown since no tickets exist
        self.assertContains(response, '¡Te damos la bienvenida a TicketSystem!')
        self.assertEqual(response.context['total'], 0)

    def test_dashboard_metrics_and_recent_tickets(self):
        """Dashboard shows correct ticket counts and order by recent updates."""
        self.client.login(username='dashboarduser', password='dashboardpassword')
        
        # Create tickets with different statuses and priorities
        Ticket.objects.create(
            titulo='Ticket Pendiente Alta',
            descripcion='Desc 1',
            estado=Ticket.Estado.PENDIENTE,
            prioridad=Ticket.Prioridad.ALTA,
            creado_por=self.user
        )
        Ticket.objects.create(
            titulo='Ticket Proceso Media',
            descripcion='Desc 2',
            estado=Ticket.Estado.EN_PROCESO,
            prioridad=Ticket.Prioridad.MEDIA,
            creado_por=self.user
        )
        Ticket.objects.create(
            titulo='Ticket Resuelto Baja',
            descripcion='Desc 3',
            estado=Ticket.Estado.RESUELTO,
            prioridad=Ticket.Prioridad.BAJA,
            creado_por=self.user
        )
        
        response = self.client.get(reverse('tickets:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total'], 3)
        
        # Verify counts in state context list
        por_estado = {x['valor']: x['count'] for x in response.context['por_estado']}
        self.assertEqual(por_estado['pendiente'], 1)
        self.assertEqual(por_estado['en_proceso'], 1)
        self.assertEqual(por_estado['resuelto'], 1)
        
        # Verify counts in priority context list
        por_prioridad = {x['valor']: x['count'] for x in response.context['por_prioridad']}
        self.assertEqual(por_prioridad['alta'], 1)
        self.assertEqual(por_prioridad['media'], 1)
        self.assertEqual(por_prioridad['baja'], 1)
        
        # Verify latest tickets contains our tickets
        self.assertEqual(len(response.context['ultimos_tickets']), 3)
        latest_titles = {ticket.titulo for ticket in response.context['ultimos_tickets']}
        self.assertEqual(latest_titles, {
            'Ticket Pendiente Alta',
            'Ticket Proceso Media',
            'Ticket Resuelto Baja',
        })


class AuthTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='authuser',
            password='authpassword',
        )

    def test_login_page_accessible(self):
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Iniciar sesión')

    def test_login_success_redirects_to_dashboard(self):
        response = self.client.post('/accounts/login/', {
            'username': 'authuser',
            'password': 'authpassword',
        })
        self.assertRedirects(response, '/', fetch_redirect_response=False)

    def test_login_invalid_credentials(self):
        response = self.client.post('/accounts/login/', {
            'username': 'authuser',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Usuario o contraseña incorrectos')

    def test_logout_redirects_to_login(self):
        self.client.login(username='authuser', password='authpassword')
        response = self.client.post('/accounts/logout/')
        self.assertRedirects(response, '/accounts/login/')

    def test_protected_views_require_login(self):
        urls = [
            reverse('tickets:lista'),
            reverse('tickets:crear'),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn('/accounts/login/', response.url)


class TicketCRUDTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='ticketcrud',
            password='ticketcrudpass',
            first_name='Carlos',
            last_name='López',
        )
        self.assignee = User.objects.create_user(
            username='assignee',
            password='assigneepass',
        )
        self.client.login(username='ticketcrud', password='ticketcrudpass')

    def test_crear_ticket(self):
        url = reverse('tickets:crear')
        response = self.client.post(url, {
            'titulo': 'Nuevo incidente',
            'descripcion': 'Descripción detallada del problema',
            'estado': Ticket.Estado.PENDIENTE,
            'prioridad': Ticket.Prioridad.ALTA,
            'asignado_a': self.assignee.pk,
        })
        self.assertEqual(response.status_code, 302)
        ticket = Ticket.objects.get(titulo='Nuevo incidente')
        self.assertEqual(ticket.creado_por, self.user)
        self.assertEqual(ticket.asignado_a, self.assignee)
        self.assertEqual(ticket.prioridad, Ticket.Prioridad.ALTA)

    def test_crear_ticket_registra_historial_inicial(self):
        url = reverse('tickets:crear')
        self.client.post(url, {
            'titulo': 'Con historial',
            'descripcion': 'Desc',
            'estado': Ticket.Estado.PENDIENTE,
            'prioridad': Ticket.Prioridad.MEDIA,
        })
        ticket = Ticket.objects.get(titulo='Con historial')
        historial = HistorialEstado.objects.filter(ticket=ticket)
        self.assertEqual(historial.count(), 1)
        entrada = historial.get()
        self.assertEqual(entrada.estado_anterior, '')
        self.assertEqual(entrada.estado_nuevo, Ticket.Estado.PENDIENTE)
        self.assertEqual(entrada.usuario, self.user)
        self.assertEqual(entrada.nota, 'Ticket creado.')

    def test_no_puede_asignar_usuario_inactivo(self):
        inactive_user = User.objects.create_user(
            username='inactive',
            password='inactivepass',
            is_active=False,
        )
        url = reverse('tickets:crear')
        response = self.client.post(url, {
            'titulo': 'Ticket con responsable inactivo',
            'descripcion': 'No debe permitirse asignar un usuario inactivo',
            'estado': Ticket.Estado.PENDIENTE,
            'prioridad': Ticket.Prioridad.MEDIA,
            'asignado_a': inactive_user.pk,
        })
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIn('asignado_a', form.errors)
        self.assertIn(
            'Seleccione una opción válida. La opción seleccionada no es una de las disponibles.',
            form.errors['asignado_a'],
        )
        self.assertFalse(Ticket.objects.filter(titulo='Ticket con responsable inactivo').exists())

    def test_detalle_muestra_ticket(self):
        ticket = Ticket.objects.create(
            titulo='Ver detalle',
            descripcion='Contenido visible',
            creado_por=self.user,
        )
        url = reverse('tickets:detalle', kwargs={'pk': ticket.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ver detalle')
        self.assertContains(response, 'Contenido visible')

    def test_lista_muestra_tickets(self):
        Ticket.objects.create(
            titulo='Ticket en lista',
            descripcion='Desc',
            creado_por=self.user,
        )
        response = self.client.get(reverse('tickets:lista'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ticket en lista')


class TicketUpdateTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            username='creator',
            password='creatorpass',
        )
        self.assignee = User.objects.create_user(
            username='responsable',
            password='responsablepass',
        )
        self.other = User.objects.create_user(
            username='otrousuario',
            password='otropass',
        )
        self.ticket = Ticket.objects.create(
            titulo='Ticket actualizable',
            descripcion='Desc',
            estado=Ticket.Estado.PENDIENTE,
            prioridad=Ticket.Prioridad.MEDIA,
            creado_por=self.creator,
        )

    def test_responsable_puede_cambiar_estado(self):
        self.ticket.asignado_a = self.assignee
        self.ticket.save()
        self.client.login(username='responsable', password='responsablepass')
        url = reverse('tickets:actualizar_ticket', kwargs={'pk': self.ticket.pk})
        response = self.client.post(url, {
            'estado': Ticket.Estado.EN_PROCESO,
            'prioridad': Ticket.Prioridad.MEDIA,
            'asignado_a': self.assignee.pk,
            'nota': 'Comenzando trabajo',
        })
        self.assertEqual(response.status_code, 302)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.estado, Ticket.Estado.EN_PROCESO)

    def test_no_responsable_no_puede_cambiar_estado(self):
        self.ticket.asignado_a = self.assignee
        self.ticket.save()
        self.client.login(username='otrousuario', password='otropass')
        url = reverse('tickets:actualizar_ticket', kwargs={'pk': self.ticket.pk})
        response = self.client.post(url, {
            'estado': Ticket.Estado.EN_PROCESO,
            'prioridad': Ticket.Prioridad.MEDIA,
            'asignado_a': self.assignee.pk,
        })
        self.assertEqual(response.status_code, 302)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.estado, Ticket.Estado.PENDIENTE)

    def test_asignarse_y_cambiar_estado_simultaneamente(self):
        self.client.login(username='otrousuario', password='otropass')
        url = reverse('tickets:actualizar_ticket', kwargs={'pk': self.ticket.pk})
        response = self.client.post(url, {
            'estado': Ticket.Estado.EN_PROCESO,
            'prioridad': Ticket.Prioridad.MEDIA,
            'asignado_a': self.other.pk,
        })
        self.assertEqual(response.status_code, 302)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.estado, Ticket.Estado.EN_PROCESO)
        self.assertEqual(self.ticket.asignado_a, self.other)

    def test_no_resolver_sin_responsable(self):
        self.client.login(username='creator', password='creatorpass')
        url = reverse('tickets:actualizar_ticket', kwargs={'pk': self.ticket.pk})
        response = self.client.post(url, {
            'estado': Ticket.Estado.RESUELTO,
            'prioridad': Ticket.Prioridad.MEDIA,
            'asignado_a': '',
        })
        self.assertEqual(response.status_code, 302)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.estado, Ticket.Estado.PENDIENTE)

    def test_cambiar_prioridad_sin_cambiar_estado(self):
        self.ticket.asignado_a = self.assignee
        self.ticket.save()
        self.client.login(username='responsable', password='responsablepass')
        url = reverse('tickets:actualizar_ticket', kwargs={'pk': self.ticket.pk})
        self.client.post(url, {
            'estado': Ticket.Estado.PENDIENTE,
            'prioridad': Ticket.Prioridad.ALTA,
            'asignado_a': self.assignee.pk,
        })
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.prioridad, Ticket.Prioridad.ALTA)
        self.assertEqual(
            HistorialEstado.objects.filter(ticket=self.ticket).count(),
            0,
        )


class HistorialEstadoTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='histuser',
            password='histpass',
        )
        self.ticket = Ticket.objects.create(
            titulo='Ticket historial',
            descripcion='Desc',
            estado=Ticket.Estado.PENDIENTE,
            creado_por=self.user,
            asignado_a=self.user,
        )
        HistorialEstado.objects.create(
            ticket=self.ticket,
            usuario=self.user,
            estado_anterior='',
            estado_nuevo=Ticket.Estado.PENDIENTE,
            nota='Ticket creado.',
        )
        self.client.login(username='histuser', password='histpass')

    def test_cambio_estado_registra_historial(self):
        url = reverse('tickets:actualizar_ticket', kwargs={'pk': self.ticket.pk})
        self.client.post(url, {
            'estado': Ticket.Estado.EN_PROCESO,
            'prioridad': Ticket.Prioridad.MEDIA,
            'asignado_a': self.user.pk,
            'nota': 'En análisis',
        })
        entradas = HistorialEstado.objects.filter(ticket=self.ticket).order_by('fecha')
        self.assertEqual(entradas.count(), 2)
        cambio = entradas.last()
        self.assertEqual(cambio.estado_anterior, Ticket.Estado.PENDIENTE)
        self.assertEqual(cambio.estado_nuevo, Ticket.Estado.EN_PROCESO)
        self.assertEqual(cambio.nota, 'En análisis')

    def test_detalle_muestra_historial(self):
        HistorialEstado.objects.create(
            ticket=self.ticket,
            usuario=self.user,
            estado_anterior=Ticket.Estado.PENDIENTE,
            estado_nuevo=Ticket.Estado.EN_PROCESO,
            nota='Avance',
        )
        url = reverse('tickets:detalle', kwargs={'pk': self.ticket.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Historial de estados')
        self.assertContains(response, 'Cambio de estado')
        self.assertContains(response, 'Avance')


class TicketFilterTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='filteruser',
            password='filterpass',
        )
        self.client.login(username='filteruser', password='filterpass')
        Ticket.objects.create(
            titulo='Alta pendiente',
            descripcion='Problema de red',
            estado=Ticket.Estado.PENDIENTE,
            prioridad=Ticket.Prioridad.ALTA,
            creado_por=self.user,
        )
        Ticket.objects.create(
            titulo='Media resuelta',
            descripcion='Problema de software',
            estado=Ticket.Estado.RESUELTO,
            prioridad=Ticket.Prioridad.MEDIA,
            creado_por=self.user,
        )
        Ticket.objects.create(
            titulo='Baja en proceso',
            descripcion='Consulta general',
            estado=Ticket.Estado.EN_PROCESO,
            prioridad=Ticket.Prioridad.BAJA,
            creado_por=self.user,
        )

    def test_filtro_por_estado(self):
        response = self.client.get(reverse('tickets:lista'), {'estado': 'pendiente'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alta pendiente')
        self.assertNotContains(response, 'Media resuelta')

    def test_filtro_por_prioridad(self):
        response = self.client.get(reverse('tickets:lista'), {'prioridad': 'alta'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alta pendiente')
        self.assertNotContains(response, 'Baja en proceso')

    def test_busqueda_por_titulo(self):
        response = self.client.get(reverse('tickets:lista'), {'buscar': 'software'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Media resuelta')
        self.assertNotContains(response, 'Alta pendiente')

    def test_busqueda_por_descripcion(self):
        response = self.client.get(reverse('tickets:lista'), {'buscar': 'Consulta'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Baja en proceso')

    def test_filtros_combinados(self):
        response = self.client.get(reverse('tickets:lista'), {
            'estado': 'pendiente',
            'prioridad': 'alta',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alta pendiente')
        self.assertNotContains(response, 'Baja en proceso')
        self.assertNotContains(response, 'Media resuelta')

    def test_filtro_estado_invalido_ignorado(self):
        response = self.client.get(reverse('tickets:lista'), {'estado': 'invalido'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['tickets']), 3)
