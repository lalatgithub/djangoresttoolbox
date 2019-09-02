"""
Supports the concept of optional fields.

E.g.:

class User(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    email = serializers.CharField()
    profile = ProfileSerializer()

    class Meta:
        fields = ('username', 'password', 'email', 'profile')
        owner_attr = '*'
        owner_fields = ('email',)
        optional_fields = ('profile',)
        write_only_fields = ('password',)
"""
import copy
from rest_framework.fields import get_attribute


OWNER_FIELDS_NO_ATTR = 'May not set `owner_fields` without `owner_attr.`'


class OptionalFieldsMixin(object):
    def __init__(self, *args, **kwargs):
        super(OptionalFieldsMixin, self).__init__(*args, **kwargs)

        meta = getattr(self, 'Meta', None)
        has_owner_fields = hasattr(meta, 'owner_fields')
        has_owner_attr = hasattr(meta, 'owner_attr')

        assert has_owner_attr or not has_owner_fields, OWNER_FIELDS_NO_ATTR

    def get_fields(self):
        fields = super(OptionalFieldsMixin, self).get_fields()

        for name, field in fields.copy().items():
            if self.allow_field(name, field) and self.show_field(name, field):
                continue
            fields.pop(name)

        return fields

    def get_owner_of(self, obj):
        try:
            meta = getattr(self, 'Meta', None)
            owner_attr = getattr(meta, 'owner_attr')
        except KeyError:
            return None

        if owner_attr == '*':
            return obj

        return get_attribute(obj, owner_attr.split('.'))

    def user_is_owner(self, user, obj):
        if user.is_superuser:
            return True

        if user == self.get_owner_of(obj):
            return True

        return False

    def allow_field(self, field_name, field):
        meta = getattr(self, 'Meta', None)
        request = self.context.get('request', None)

        # Do not hide fields that are not owner.
        if field_name not in getattr(meta, 'owner_fields', ()):
            return True

        if not hasattr(meta, 'owner_fields'):
            return True
        else:
            if not request:
                return False
            return self.user_is_owner(request.user, self.instance)

    def get_show_field_param(self, field_name):
        return 'show_%s_field' % field_name

    def show_field(self, field_name, field):
        """
        Determines whether or not a field should be shown.
        """
        show_func_name = 'show_%s' % field_name
        request = self.context.get('request', None)

        # Do not hide fields in write cases.
        if not self.instance:
            return True

        # Do not hide fields that are not optional.
        if field_name not in getattr(self.Meta, 'optional_fields', ()):
            return True

        # Run a function named show_{field} if one exists.
        if hasattr(self, show_func_name):
            show_func = getattr(self, show_func_name)
            if callable(show_func):
                result = show_func(instance=self.instance, field_name=field_name,
                                   field=field)
                if result is not None:
                    return result

        # Do not hide optional fields if they are explicitly requested.
        if request is not None:
            field_param = self.get_show_field_param(field_name)
            if field_param in request.query_params:
                return request.query_params[field_param].lower() in ['1', 'y', 'true']

        return False
