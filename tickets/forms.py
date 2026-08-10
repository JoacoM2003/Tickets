from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from .models import Ticket, Comentario


class TicketForm(forms.ModelForm):
    """
    Formulario para crear y editar tickets.
    Excluye campos auto-generados y el campo creado_por (se asigna en la vista).
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'asignado_a' in self.fields:
            self.fields['asignado_a'].queryset = User.objects.filter(is_active=True).order_by('username')

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

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if 'asignado_a' in self.fields:
            if self.user and self.user.is_staff:
                queryset = User.objects.filter(is_active=True)
            else:
                if self.instance and self.instance.asignado_a:
                    queryset = User.objects.filter(pk=self.instance.asignado_a.pk)
                else:
                    queryset = User.objects.filter(pk=self.user.pk)
            self.fields['asignado_a'].queryset = queryset.order_by('username')

    def clean(self):
        cleaned_data = super().clean()
        estado_nuevo = cleaned_data.get('estado')
        prioridad_nueva = cleaned_data.get('prioridad')
        asignado_a_nuevo = cleaned_data.get('asignado_a')

        is_admin = self.user and self.user.is_staff
        current_asignado = self.instance.asignado_a
        is_responsable = current_asignado == self.user
        is_self_assign = asignado_a_nuevo == self.user

        # Tickets sin responsable pueden autoasignarse al propio usuario.
        if current_asignado is None:
            if 'asignado_a' in self.changed_data and not is_admin:
                if not is_self_assign:
                    self.add_error('asignado_a', 'Solo puede autoasignarse a sí mismo a un ticket sin responsable.')
            if any(field in self.changed_data for field in ['estado', 'prioridad']):
                if not (is_self_assign or is_admin):
                    self.add_error(None, 'Solo el responsable asignado o un administrador puede modificar el estado y la prioridad.')

        else:
            if 'asignado_a' in self.changed_data and not is_admin:
                self.add_error('asignado_a', 'Solo un administrador puede cambiar el responsable del ticket.')
            if any(field in self.changed_data for field in ['estado', 'prioridad']):
                if not (is_responsable or is_admin):
                    self.add_error(None, 'Solo el responsable asignado o un administrador puede modificar el estado y la prioridad.')

        if 'estado' in self.changed_data and asignado_a_nuevo != self.user and not is_admin:
            self.add_error('estado', 'Solo el responsable puede realizar cambios de estado. Asígnese el ticket primero o al mismo tiempo.')

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
