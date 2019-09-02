from django.utils import six
from rest_framework.exceptions import ValidationError
from rest_framework.fields import get_attribute, empty
from rest_framework.serializers import BaseSerializer


class PolymorphicSerializerMetaclass(type):
    @classmethod
    def _get_type_fields(cls, bases, attrs):
        fields = {}
        if 'Types' in attrs:
            for name, data in attrs['Types'].__dict__.items():
                if name.startswith('_'):
                    continue
                fields[name] = data

        for base in reversed(bases):
            if hasattr(base, '_type_fields'):
                parent = base._type_fields.copy()
                parent.update(fields)
                fields = parent

        return fields

    @classmethod
    def _get_declared_types(cls, bases, attrs):
        return {
            name: (cls, serializer)
            for name, (cls, serializer)
            in attrs['_type_fields'].items()
        }

    @classmethod
    def _get_declared_classes(cls, bases, attrs):
        return {
            cls: (name, serializer)
            for name, (cls, serializer)
            in attrs['_type_fields'].items()
        }

    def __new__(cls, name, bases, attrs):
        attrs['_type_fields'] = cls._get_type_fields(bases, attrs)
        attrs['_declared_types'] = cls._get_declared_types(bases, attrs)
        attrs['_declared_classes'] = cls._get_declared_classes(bases, attrs)
        return super(PolymorphicSerializerMetaclass, cls).__new__(cls, name, bases, attrs)


@six.add_metaclass(PolymorphicSerializerMetaclass)
class PolymorphicSerializer(BaseSerializer):
    """
    A `PolymorphicSerializer` is a special serializer that, itself, does not
    perform serialization or validation, but rather delegates those tasks to
    another serializer, specified either by the data's `type` field, or the
    class type of the instance.

    The purpose of a `PolymorphicSerializer` is to allow idiomatic
    handling of polymorphic objects in a serializer. Through the `type_field`,
    the concrete classes of a polymorphic object can be specified, allowing
    both read and write of polymorphic objects.

    # Example
    ```python
    class FurnitureSerializer(PolymorphicSerializer):
        class Types:
            table = (Table, TableSerializer)
            couch = (Couch, CouchSerializer)
    ```
    """

    def __init__(self, *args, **kwargs):
        meta = getattr(self, 'Meta', None)
        self.type_field = str(getattr(meta, 'type_field', 'type'))

        assert not hasattr(meta, 'type_field') or self.type_field != 'type', \
            'Redundant type_field. Simply omit the type_field from meta.'

        super(PolymorphicSerializer, self).__init__(*args, **kwargs)

    def get_serializer_class(self, instance=None, data=empty):
        """
        Returns the appropriate serializer to use for given data or instance.
        """
        if instance is not None:
            for cls, (name, serializer) in self._declared_classes.items():
                if cls == instance.__class__:
                    return serializer
        elif data is not empty:
            try:
                type_value = get_attribute(data, [self.type_field])
            except KeyError:
                raise ValidationError('No type specified.')

            for name, (cls, serializer) in self._declared_types.items():
                if name == type_value:
                    return serializer
        return

    def get_serializer(self, instance=None, data=empty):
        sargs = {
            'instance': self.instance,
            'partial': self.partial,
            'context': self._context,
        }

        if hasattr(self, 'initial_data'):
            sargs['data'] = self.initial_data

        try:
            return self.get_serializer_class(instance, data)(**sargs)
        except TypeError:
            raise ValidationError('Bad type.')

    def run_validation(self, data=empty):
        # Make sure we maintain the type field!
        if data is empty:
            data = self.initial_data

        type = data.get(self.type_field, None)
        data = self.get_serializer(data=data).run_validation(data)
        data[self.type_field] = type
        return data

    def to_internal_value(self, data):
        return self.get_serializer(data=data).to_internal_value(data)

    def to_representation(self, instance):
        data = self.get_serializer(instance=instance).to_representation(instance)
        data[self.type_field] = self._declared_classes[instance.__class__][0]
        return data

    def create(self, validated_data):
        serializer = self.get_serializer(data=validated_data)
        return serializer.create(validated_data)

    def update(self, instance, validated_data):
        serializer = self.get_serializer(instance=instance)
        return serializer.update(instance, validated_data)
