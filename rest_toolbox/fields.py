import base64
from django.utils.encoding import force_bytes
from rest_framework import fields


class Base64Field(fields.CharField):
    def to_internal_value(self, data):
        return base64.b64decode(force_bytes(data))

    def to_representation(self, value):
        return base64.b64encode(force_bytes(value))
