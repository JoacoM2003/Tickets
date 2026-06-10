from django.contrib import admin
from .models import Ticket, Comentario, HistorialEstado


class ComentarioInline(admin.TabularInline):
    model = Comentario
    extra = 0
    readonly_fields = ('fecha',)


class HistorialEstadoInline(admin.TabularInline):
    model = HistorialEstado
    extra = 0
    readonly_fields = ('usuario', 'estado_anterior', 'estado_nuevo', 'nota', 'fecha')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False  # El historial solo se crea programáticamente


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'estado', 'prioridad', 'asignado_a', 'creado_por', 'fecha_creacion')
    list_filter = ('estado', 'prioridad')
    search_fields = ('titulo', 'descripcion')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    inlines = [ComentarioInline, HistorialEstadoInline]


@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'autor', 'fecha')
    readonly_fields = ('fecha',)


@admin.register(HistorialEstado)
class HistorialEstadoAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'usuario', 'estado_anterior', 'estado_nuevo', 'fecha')
    list_filter = ('estado_nuevo',)
    readonly_fields = ('ticket', 'usuario', 'estado_anterior', 'estado_nuevo', 'nota', 'fecha')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
