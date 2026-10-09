from django.urls import path
from . import views

app_name = 'tickets'

urlpatterns = [
    # Dashboard / inicio
    path('', views.DashboardView.as_view(), name='dashboard'),

    # Reporte y seguimiento público (sin login)
    path('reportar/', views.TicketPublicoCreateView.as_view(), name='reportar'),
    path(
        'reportar/confirmacion/<uuid:codigo>/',
        views.TicketReporteConfirmacionView.as_view(),
        name='reporte_confirmacion',
    ),
    path(
        'seguimiento/<uuid:codigo>/',
        views.TicketSeguimientoPublicoView.as_view(),
        name='seguimiento_publico',
    ),
    path('consultar/', views.ConsultaCodigoView.as_view(), name='consultar_codigo'),

    # CRUD de tickets
    path('tickets/', views.TicketListView.as_view(), name='lista'),
    path('tickets/nuevo/', views.TicketCreateView.as_view(), name='crear'),
    path('tickets/<int:pk>/', views.TicketDetailView.as_view(), name='detalle'),

    # Acciones POST
    path('tickets/<int:pk>/actualizar/', views.actualizar_ticket, name='actualizar_ticket'),
    path('tickets/<int:pk>/comentar/', views.comentar_ticket, name='comentar'),

    # CRUD de usuarios
    path('usuarios/', views.UsuarioListView.as_view(), name='usuario_lista'),
    path('usuarios/nuevo/', views.UsuarioCreateView.as_view(), name='usuario_crear'),
    path('usuarios/<int:pk>/editar/', views.UsuarioUpdateView.as_view(), name='usuario_editar'),
    path('usuarios/<int:pk>/password/', views.UsuarioPasswordResetView.as_view(), name='usuario_password'),
]
