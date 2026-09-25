import os
import json
import boto3
from botocore.config import Config
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import HistorialEstado

sqs = boto3.client(
    'sqs',
    region_name=os.environ.get('AWS_REGION'),
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
    config=Config(connect_timeout=3, read_timeout=5, retries={'max_attempts': 1}),
)

@receiver(post_save, sender=HistorialEstado)
def notificar_cambio_estado(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        sqs.send_message(
            QueueUrl=os.environ.get('SQS_QUEUE_URL'),
            MessageBody=json.dumps({
                'ticket_id': instance.ticket_id,
                'titulo': instance.ticket.titulo,
                'estado_anterior': instance.estado_anterior,
                'estado_nuevo': instance.estado_nuevo,
                'usuario': instance.usuario.username if instance.usuario else 'desconocido',
            })
        )
    except Exception as e:
        print(f'Error al enviar la notificacion a SQS: {e}')