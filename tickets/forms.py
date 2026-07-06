from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Ticket, Comentario


class TicketForm(forms.ModelForm):
    """
    Formulario para crear y editar tickets.
    Excluye campos auto-generados y el campo creado_por (se asigna en la vista).
    """
    class Meta:
        model = Ticket
        fields = ['titulo', 'descripcion', 'estado', 'prioridad', 'asignado_a']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título breve y descriptivo',
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe el problema detalladamente...',
            }),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'prioridad': forms.Select(attrs={'class': 'form-select'}),
            'asignado_a': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'titulo': 'Título',
            'descripcion': 'Descripción',
            'estado': 'Estado',
            'prioridad': 'Prioridad',
            'asignado_a': 'Asignar a',
        }


class ActualizarTicketForm(forms.ModelForm):
    """Formulario para actualizar el estado y/o la prioridad de un ticket.
    Incluye una nota opcional que se guardará en el historial si cambia el estado.
    """
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    nota = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Nota opcional al cambiar de estado',
        }),
        label='Nota (opcional)',
    )

    class Meta:
        model = Ticket
        fields = ['estado', 'prioridad', 'asignado_a']
        widgets = {
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'prioridad': forms.Select(attrs={'class': 'form-select'}),
            'asignado_a': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        estado_nuevo = cleaned_data.get('estado')
        asignado_a_nuevo = cleaned_data.get('asignado_a')

        # Regla: Cualquier cambio de estado exige que el ejecutante sea el responsable
        if 'estado' in self.changed_data:
            if asignado_a_nuevo != self.user and not self.user.is_superuser:
                self.add_error('estado', 'Solo el responsable puede realizar cambios de estado. Asígnese el ticket primero o al mismo tiempo.')

        # Regla: No resolver sin un responsable
        if estado_nuevo == Ticket.Estado.RESUELTO and not asignado_a_nuevo:
            self.add_error('estado', 'No se puede marcar el ticket como Resuelto sin un responsable asignado.')

        return cleaned_data



class ComentarioForm(forms.ModelForm):
    """Formulario para publicar un comentario en un ticket."""

    class Meta:
        model = Comentario
        fields = ['texto']
        widgets = {
            'texto': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Escriba su comentario...',
                'aria-label': 'Texto del comentario',
            }),
        }
        labels = {
            'texto': '',
        }
        error_messages = {
            'texto': {
                'required': 'El comentario no puede estar vacío.',
            },
        }

    def clean_texto(self):
        texto = self.cleaned_data.get('texto', '').strip()
        if not texto:
            raise forms.ValidationError('El comentario no puede estar vacío.')
        return texto


class UsuarioCrearForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active']
        labels = {
            'username': 'Nombre de usuario',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo electrónico',
            'is_staff': 'Es administrador (Staff)',
            'is_active': 'Activo',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'


class UsuarioEditarForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active']
        labels = {
            'username': 'Nombre de usuario',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo electrónico',
            'is_staff': 'Es administrador (Staff)',
            'is_active': 'Activo',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'
