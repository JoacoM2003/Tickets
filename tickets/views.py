from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.urls import reverse_lazy
from django.db.models import Count, Q

from .models import Ticket, Comentario, HistorialEstado
from .forms import TicketForm, ActualizarTicketForm, ComentarioForm


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Vista del panel principal con métricas generales.
    Muestra conteos agrupados por estado y por prioridad,
    más los últimos 5 tickets creados.
    """
    template_name = 'tickets/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Conteos por estado
        estados = Ticket.Estado.choices
        context['por_estado'] = [
            {
                'label': label,
                'valor': value,
                'count': Ticket.objects.filter(estado=value).count(),
            }
            for value, label in estados
        ]

        # Conteos por prioridad
        prioridades = Ticket.Prioridad.choices
        context['por_prioridad'] = [
            {
                'label': label,
                'valor': value,
                'count': Ticket.objects.filter(prioridad=value).count(),
            }
            for value, label in prioridades
        ]

        context['total'] = Ticket.objects.count()
        context['ultimos_tickets'] = Ticket.objects.select_related('asignado_a', 'creado_por')[:5]
        return context


class TicketListView(LoginRequiredMixin, ListView):
    """
    Lista todos los tickets con opción de filtrar por estado y/o prioridad.
    Los filtros se pasan como query params: ?estado=pendiente&prioridad=alta
    """
    model = Ticket
    template_name = 'tickets/ticket_list.html'
    context_object_name = 'tickets'
    paginate_by = 15

    def get_queryset(self):
        qs = Ticket.objects.select_related('asignado_a', 'creado_por')
        estado = self.request.GET.get('estado')
        prioridad = self.request.GET.get('prioridad')
        buscar = self.request.GET.get('buscar')

        if estado and estado in dict(Ticket.Estado.choices):
            qs = qs.filter(estado=estado)
        if prioridad and prioridad in dict(Ticket.Prioridad.choices):
            qs = qs.filter(prioridad=prioridad)
        if buscar:
            qs = qs.filter(
                Q(titulo__icontains=buscar) | Q(descripcion__icontains=buscar)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['estados'] = Ticket.Estado.choices
        context['prioridades'] = Ticket.Prioridad.choices
        context['filtro_estado'] = self.request.GET.get('estado', '')
        context['filtro_prioridad'] = self.request.GET.get('prioridad', '')
        context['buscar'] = self.request.GET.get('buscar', '')
        return context


class TicketDetailView(LoginRequiredMixin, DetailView):
    """
    Detalle completo de un ticket.
    Incluye el historial de comentarios y el formulario para agregar uno nuevo.
    """
    model = Ticket
    template_name = 'tickets/ticket_detail.html'
    context_object_name = 'ticket'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comentarios'] = self.object.comentarios.select_related('autor').all()
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
def agregar_comentario(request, pk):
    """
    Vista funcional para agregar un comentario a un ticket.
    Solo acepta POST. El autor se asigna desde request.user.
    """
    ticket = get_object_or_404(Ticket, pk=pk)
    if request.method == 'POST':
        form = ComentarioForm(request.POST)
        if form.is_valid():
            comentario = form.save(commit=False)
            comentario.ticket = ticket
            comentario.autor = request.user
            comentario.save()
            messages.success(request, 'Comentario agregado.')
        else:
            messages.error(request, 'El comentario no puede estar vacío.')
    return redirect('tickets:detalle', pk=pk)
