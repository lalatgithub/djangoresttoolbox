from __future__ import unicode_literals, absolute_import

from rest_framework.serializers import HyperlinkedModelSerializer as DefaultHyperlinkedModelSerializer
from rest_framework.serializers import ModelSerializer as DefaultModelSerializer
from rest_framework.serializers import Serializer as DefaultSerializer
from rest_toolbox.optional_fields import OptionalFieldsMixin

# This is here for convenience.
from rest_toolbox.fields import *  # NOQA

# This is here so we can maintain compatibility with Django REST framework.
from rest_framework.relations import *  # NOQA
from rest_framework.fields import *  # NOQA
from rest_framework.serializers import (  # NOQA
    BaseSerializer, SerializerMetaclass, ListSerializer,
)


class Serializer(OptionalFieldsMixin, DefaultSerializer):
    pass


class ModelSerializer(OptionalFieldsMixin, DefaultModelSerializer):
    pass


class HyperlinkedModelSerializer(OptionalFieldsMixin, DefaultHyperlinkedModelSerializer):
    pass
