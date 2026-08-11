from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView, FormView
from django.urls import reverse_lazy
from django.db.models import Count, Q
from django.contrib.auth.models import User
from django.contrib.auth.forms import SetPasswordForm

from .models import Ticket, Comentario, HistorialEstado
from .forms import TicketForm, ActualizarTicketForm, ComentarioForm, UsuarioCrearForm, UsuarioEditarForm


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Vista del panel principal con métricas generales.
    Muestra conteos agrupados por estado y por prioridad,
    más los últimos 5 tickets creados.
    """
    template_name = 'tickets/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Optimización: Realizar un único query de agregación para obtener todos los conteos
        counts = Ticket.objects.aggregate(
            total=Count('id'),
            # Estado
            pendiente=Count('id', filter=Q(estado=Ticket.Estado.PENDIENTE)),
            en_proceso=Count('id', filter=Q(estado=Ticket.Estado.EN_PROCESO)),
            resuelto=Count('id', filter=Q(estado=Ticket.Estado.RESUELTO)),
            # Prioridad
            baja=Count('id', filter=Q(prioridad=Ticket.Prioridad.BAJA)),
            media=Count('id', filter=Q(prioridad=Ticket.Prioridad.MEDIA)),
            alta=Count('id', filter=Q(prioridad=Ticket.Prioridad.ALTA)),
        )

        total = counts['total']
        context['total'] = total

        # Conteos por estado
        context['por_estado'] = [
            {
                'label': label,
                'valor': value,
                'count': counts.get(value, 0),
            }
            for value, label in Ticket.Estado.choices
        ]

        # Conteos por prioridad
        context['por_prioridad'] = [
            {
                'label': label,
                'valor': value,
                'count': counts.get(value, 0),
            }
            for value, label in Ticket.Prioridad.choices
        ]

        context['ultimos_tickets'] = (
            Ticket.objects
            .select_related('asignado_a', 'creado_por')
            .order_by('-fecha_actualizacion')[:5]
        )
        return context


class TicketListView(LoginRequiredMixin, ListView):
    """
    Lista todos los tickets con opción de filtrar por estado y/o prioridad.
    Los filtros se pasan como query params: ?estado=pendiente&prioridad=alta
    """
    model = Ticket
    template_name = 'tickets/ticket_list.html'
    context_object_name = 'tickets'
    paginate_by = 10

    def get_queryset(self):
        qs = (
            Ticket.objects
            .select_related('asignado_a', 'creado_por')
            .annotate(num_comentarios=Count('comentarios'))
        )
        estado = self.request.GET.get('estado')
        prioridad = self.request.GET.get('prioridad')
        buscar = self.request.GET.get('buscar')
        sort = self.request.GET.get('sort', 'fecha_creacion')
        order = self.request.GET.get('order', 'desc')

        if estado and estado in dict(Ticket.Estado.choices):
            qs = qs.filter(estado=estado)
        if prioridad and prioridad in dict(Ticket.Prioridad.choices):
            qs = qs.filter(prioridad=prioridad)
        if buscar:
            qs = qs.filter(
                Q(titulo__icontains=buscar) | Q(descripcion__icontains=buscar)
            )

        sort_fields = {
            'fecha_creacion': 'fecha_creacion',
            'fecha_actualizacion': 'fecha_actualizacion',
            'titulo': 'titulo',
            'prioridad': 'prioridad',
            'estado': 'estado',
            'responsable': 'asignado_a__username',
        }
        sort_field = sort_fields.get(sort, 'fecha_creacion')
        if order != 'asc':
            sort_field = f'-{sort_field}'

        return qs.order_by(sort_field)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['estados'] = Ticket.Estado.choices
        context['prioridades'] = Ticket.Prioridad.choices
        context['filtro_estado'] = self.request.GET.get('estado', '')
        context['filtro_prioridad'] = self.request.GET.get('prioridad', '')
        context['buscar'] = self.request.GET.get('buscar', '')
        context['sort'] = self.request.GET.get('sort', 'fecha_creacion')
        context['order'] = self.request.GET.get('order', 'desc')
        return context


class TicketDetailView(LoginRequiredMixin, DetailView):
    """
    Detalle completo de un ticket.
    Incluye la lista de comentarios y el formulario para publicar uno nuevo.
    """
    model = Ticket
    template_name = 'tickets/ticket_detail.html'
    context_object_name = 'ticket'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comentarios = list(
            self.object.comentarios.select_related('autor').order_by('fecha')
        )
        context['comentarios'] = comentarios
        context['total_comentarios'] = len(comentarios)
        context['historial'] = self.object.historial.select_related('usuario').all()
        context['comentario_form'] = ComentarioForm()
        context['actualizar_form'] = ActualizarTicketForm(instance=self.object, user=self.request.user)
        return context


class TicketCreateView(LoginRequiredMixin, CreateView):
    """
    Formulario para crear un nuevo ticket.
    Asigna automáticamente el usuario actual como 'creado_por'.
    """
    model = Ticket
    form_class = TicketForm
    template_name = 'tickets/ticket_form.html'
    success_url = reverse_lazy('tickets:lista')

    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        response = super().form_valid(form)
        # Registrar estado inicial en el historial
        HistorialEstado.objects.create(
            ticket=self.object,
            usuario=self.request.user,
            estado_anterior='',
            estado_nuevo=self.object.estado,
            nota='Ticket creado.',
        )
        messages.success(self.request, 'Ticket creado correctamente.')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Nuevo Ticket'
        context['accion'] = 'Crear'
        return context




@login_required
def actualizar_ticket(request, pk):
    """
    Vista funcional para actualizar estado y/o prioridad del ticket.
    Registra en HistorialEstado: quién cambió, desde qué estado, a cuál, y nota opcional,
    SOLO si el estado efectivamente cambió.
    Solo acepta POST.
    """
    ticket = get_object_or_404(Ticket, pk=pk)
    if request.method == 'POST':
        estado_anterior = ticket.estado  # capturar ANTES de guardar
        form = ActualizarTicketForm(request.POST, instance=ticket, user=request.user)
        if form.is_valid():
            form.save()
            ticket.refresh_from_db()   # obtener datos actualizados
            
            # Registrar historial SOLO si cambió el estado
            if estado_anterior != ticket.estado:
                nota = form.cleaned_data.get('nota', '')
                HistorialEstado.objects.create(
                    ticket=ticket,
                    usuario=request.user,
                    estado_anterior=estado_anterior,
                    estado_nuevo=ticket.estado,
                    nota=nota,
                )
                
            messages.success(request, 'Ticket actualizado correctamente.')
        else:
            # Mostrar errores de validación de negocio (ej. "no puedes cambiar estado")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
                    
    return redirect('tickets:detalle', pk=pk)


@login_required
def comentar_ticket(request, pk):
    """
    Publica un comentario en un ticket.
    Solo acepta POST; el autor se asigna desde request.user.
    """
    ticket = get_object_or_404(Ticket, pk=pk)
    if request.method == 'POST':
        form = ComentarioForm(request.POST)
        if form.is_valid():
            comentario = form.save(commit=False)
            comentario.ticket = ticket
            comentario.autor = request.user
            comentario.save()
            messages.success(request, 'Comentario publicado correctamente.')
        else:
            messages.error(request, 'El comentario no puede estar vacío.')
    return redirect('tickets:detalle', pk=pk)


class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin que restringe el acceso solo a usuarios con is_staff=True."""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff


class UsuarioListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """Listado de todos los usuarios para administradores."""
    model = User
    template_name = 'tickets/usuario_list.html'
    context_object_name = 'usuarios'
    paginate_by = 15

    def get_queryset(self):
        qs = User.objects.all().order_by('username')
        buscar = self.request.GET.get('buscar')
        if buscar:
            qs = qs.filter(
                Q(username__icontains=buscar) |
                Q(first_name__icontains=buscar) |
                Q(last_name__icontains=buscar) |
                Q(email__icontains=buscar)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['buscar'] = self.request.GET.get('buscar', '')
        return context


class UsuarioCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    """Vista para crear un nuevo usuario."""
    model = User
    form_class = UsuarioCrearForm
    template_name = 'tickets/usuario_form.html'
    success_url = reverse_lazy('tickets:usuario_lista')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Usuario "{self.object.username}" creado correctamente.')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = 'Nuevo Usuario'
        context['accion'] = 'Crear'
        return context


class UsuarioUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    """Vista para editar un usuario existente."""
    model = User
    form_class = UsuarioEditarForm
    template_name = 'tickets/usuario_form.html'
    success_url = reverse_lazy('tickets:usuario_lista')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Usuario "{self.object.username}" actualizado correctamente.')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = f'Editar Usuario: {self.object.username}'
        context['accion'] = 'Guardar'
        context['es_edicion'] = True
        return context


class UsuarioPasswordResetView(LoginRequiredMixin, StaffRequiredMixin, FormView):
    """Vista para que un administrador restablezca la contraseña de un usuario."""
    template_name = 'tickets/usuario_password_reset.html'
    form_class = SetPasswordForm
    success_url = reverse_lazy('tickets:usuario_lista')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = get_object_or_404(User, pk=self.kwargs['pk'])
        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs['class'] = 'form-control'
        return form

    def form_valid(self, form):
        form.save()
        user = get_object_or_404(User, pk=self.kwargs['pk'])
        messages.success(self.request, f'Contraseña de "{user.username}" restablecida correctamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['u'] = get_object_or_404(User, pk=self.kwargs['pk'])
        return context
