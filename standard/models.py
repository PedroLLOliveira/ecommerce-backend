'''
  Esse arquivo serve para gerenciar as classes padroes que vamos herdar
  em nossos models.
  Por exemplo, se quisermos adicionar campos de auditoria (data de criacao,
  data de modificacao, usuario que criou, usuario que modificou) em todos
  os models, podemos criar uma classe base aqui e fazer com que todos os
  models herdem dessa classe.
'''

import uuid
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class TimeStampedModel(models.Model):
    '''
      Adiciona campos de data de criacao, data de modificacao e delecao logica.
    '''
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    '''
      Adiciona um campo UUID como chave primaria.
    '''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class UserStampedModel(models.Model):
    '''
      Adiciona campos para rastrear o usuario que criou e modificou o registro.
    '''
    created_by = models.ForeignKey(
        User,
        related_name='%(class)s_created',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    updated_by = models.ForeignKey(
        User,
        related_name='%(class)s_updated',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        abstract = True


class StandardModel(TimeStampedModel, UUIDModel, UserStampedModel):
    '''
      Classe base que combina TimeStampedModel, UUIDModel e UserStampedModel.
      Todos os models podem herdar dessa classe para ter esses campos padroes.
    '''
    class Meta:
        abstract = True
