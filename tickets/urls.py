from django.urls import path
from . import views

app_name = 'tickets'

urlpatterns = [
    # Dashboard / inicio
    path('', views.DashboardView.as_view(), name='dashboard'),

    # CRUD de tickets
    path('tickets/', views.TicketListView.as_view(), name='lista'),
    path('tickets/nuevo/', views.TicketCreateView.as_view(), name='crear'),
    path('tickets/<int:pk>/', views.TicketDetailView.as_view(), name='detalle'),

    # Acciones POST
    path('tickets/<int:pk>/actualizar/', views.actualizar_ticket, name='actualizar_ticket'),
    path('tickets/<int:pk>/comentar/', views.agregar_comentario, name='comentar'),
]
