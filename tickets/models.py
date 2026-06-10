from django.db import models
from django.contrib.auth.models import User


class Ticket(models.Model):
    """
    Modelo principal que representa una incidencia (ticket).
    
    Campos:
    - titulo: Nombre corto descriptivo del problema.
    - descripcion: Detalle completo de la incidencia.
    - estado: Ciclo de vida del ticket (pendiente → en_proceso → resuelto).
    - prioridad: Urgencia de atención (baja, media, alta).
    - fecha_creacion: Se setea automáticamente al crear (auto_now_add).
    - fecha_actualizacion: Se actualiza automáticamente en cada save (auto_now).
    - asignado_a: FK opcional al modelo User de Django.
    - creado_por: FK al usuario que creó el ticket.
    """

    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        EN_PROCESO = 'en_proceso', 'En proceso'
        RESUELTO = 'resuelto', 'Resuelto'

    class Prioridad(models.TextChoices):
        BAJA = 'baja', 'Baja'
        MEDIA = 'media', 'Media'
        ALTA = 'alta', 'Alta'

    titulo = models.CharField(max_length=200, verbose_name='Título')
    descripcion = models.TextField(verbose_name='Descripción')
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
        verbose_name='Estado',
    )
    prioridad = models.CharField(
        max_length=10,
        choices=Prioridad.choices,
        default=Prioridad.MEDIA,
        verbose_name='Prioridad',
    )
    asignado_a = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets_asignados',
        verbose_name='Asignado a',
    )
    creado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='tickets_creados',
        verbose_name='Creado por',
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name='Última actualización')

    class Meta:
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f'[{self.get_prioridad_display()}] {self.titulo}'

    def get_estado_badge_class(self):
        """Devuelve la clase Bootstrap del badge según el estado."""
        mapping = {
            self.Estado.PENDIENTE: 'warning',
            self.Estado.EN_PROCESO: 'primary',
            self.Estado.RESUELTO: 'success',
        }
        return mapping.get(self.estado, 'secondary')

    def get_prioridad_badge_class(self):
        """Devuelve la clase Bootstrap del badge según la prioridad."""
        mapping = {
            self.Prioridad.BAJA: 'success',
            self.Prioridad.MEDIA: 'warning',
            self.Prioridad.ALTA: 'danger',
        }
        return mapping.get(self.prioridad, 'secondary')


class Comentario(models.Model):
    """
    Comentario asociado a un ticket.
    Permite registrar el historial de acciones y notas sobre una incidencia.
    """
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='comentarios',
        verbose_name='Ticket',
    )
    autor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Autor',
    )
    texto = models.TextField(verbose_name='Comentario')
    fecha = models.DateTimeField(auto_now_add=True, verbose_name='Fecha')

    class Meta:
        verbose_name = 'Comentario'
        verbose_name_plural = 'Comentarios'
        ordering = ['fecha']

    def __str__(self):
        return f'Comentario de {self.autor} en Ticket #{self.ticket_id}'


class HistorialEstado(models.Model):
    """
    Registra cada cambio de estado de un ticket.

    Se crea automáticamente en la vista `cambiar_estado` y también
    en la creación del ticket (estado inicial = pendiente).

    Campos:
    - ticket: FK al ticket modificado.
    - usuario: quién realizó el cambio (puede ser null si el usuario fue eliminado).
    - estado_anterior: valor del estado ANTES del cambio (vacío en la creación).
    - estado_nuevo: valor del estado DESPUÉS del cambio.
    - nota: texto libre opcional que el usuario puede dejar al cambiar el estado.
    - fecha: timestamp automático del momento del cambio.
    """

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='historial',
        verbose_name='Ticket',
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Usuario',
    )
    estado_anterior = models.CharField(
        max_length=20,
        choices=Ticket.Estado.choices,
        blank=True,
        verbose_name='Estado anterior',
    )
    estado_nuevo = models.CharField(
        max_length=20,
        choices=Ticket.Estado.choices,
        verbose_name='Estado nuevo',
    )
    nota = models.TextField(
        blank=True,
        verbose_name='Nota',
        help_text='Observación opcional al realizar el cambio.',
    )
    fecha = models.DateTimeField(auto_now_add=True, verbose_name='Fecha')

    class Meta:
        verbose_name = 'Historial de estado'
        verbose_name_plural = 'Historial de estados'
        ordering = ['fecha']

    def __str__(self):
        if self.estado_anterior:
            return (
                f'Ticket #{self.ticket_id}: '
                f'{self.estado_anterior} → {self.estado_nuevo} '
                f'({self.usuario})'
            )
        return f'Ticket #{self.ticket_id}: creado en {self.estado_nuevo}'

