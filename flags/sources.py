
from django.apps import apps
from django.conf import settings
from django.utils.module_loading import import_string

from flags.conditions import get_condition


DEFAULT_FLAG_SOURCES = (
    'flags.sources.SettingsFlagsSource',
    'flags.sources.DatabaseFlagsSource',
)


class Condition(object):
    """ A simple wrapper around conditions """

    def __init__(self, condition, value):
        self.condition = condition
        self.value = value
        self.checkers = get_condition(self.condition)

    def __eq__(self, other):
        return other.condition == self.condition and other.value == self.value

    def __repr__(self):
        return 'Condition("{condition}", "{value}")'.format(
            condition=self.condition, value=self.value
        )

    def check(self, **kwargs):
        return any(c(self.value, **kwargs) for c in self.checkers)


class Flag(object):
    """ A simple wrapper around feature flags and their conditions """

    def __init__(self, name, conditions=[]):
        self.name = name
        self.conditions = conditions

    def __eq__(self, other):
        """ There can be only one feature flag of a given name """
        return other.name == self.name

    def __repr__(self):
        return 'Flag("{name}", {conditions})'.format(
            name=self.name, conditions=self.conditions
        )

    def check_state(self, **kwargs):
        """ Determine this flag's state based on any of its conditions """
        return any(c.check(**kwargs) for c in self.conditions)


class SettingsFlagsSource(object):

    def get_flags(self):
        settings_flags = getattr(settings, 'FLAGS', {})
        flags = {}
        for flag, conditions in settings_flags.items():
            flags[flag] = self.get_flag(flag, conditions=conditions)

        return flags

    def get_flag(self, flag_name, conditions=None):
        settings_flags = getattr(settings, 'FLAGS', {})
        if conditions is None:
            conditions = settings_flags.get(flag_name, [])

        if isinstance(conditions, dict):
            conditions = conditions.items()

        conditions_objs = [Condition(c, v) for c, v in conditions]
        return conditions_objs


class DatabaseCondition(Condition):
    """ Condition that includes the FlagState database object """

    def __init__(self, condition, value, obj=None):
        super(DatabaseCondition, self).__init__(condition, value)
        self.obj = obj


class DatabaseFlagsSource(object):

    def get_queryset(self):
        FlagState = apps.get_model('flags', 'FlagState')
        return FlagState.objects.all()

    def get_flags(self):
        flags = {}
        for o in self.get_queryset():
            if o.name not in flags:
                flags[o.name] = []
            flags[o.name].append(DatabaseCondition(
                o.condition, o.value, obj=o
            ))

        return flags

    def get_flag(self, flag_name, queryset=None):
        if queryset is None:
            queryset = self.get_queryset().filter(name=flag_name)

        conditions_objs = [
            DatabaseCondition(o.condition, o.value, obj=o)
            for o in queryset
        ]
        return conditions_objs


def get_flags(sources=None):
    """ Get all flag sources sources defined in settings.FLAG_SOURCES.
    FLAG_SOURCES is expected to be a list of Python paths to classes providing
    a get_flags() method that returns a dict with the same format as the
    FLAG setting. """
    flags = {}

    if sources is None:
        sources = getattr(settings, 'FLAG_SOURCES', DEFAULT_FLAG_SOURCES)

    for source_str in sources:
        source_cls = import_string(source_str)
        source_obj = source_cls()
        source_flags = source_obj.get_flags()

        for flag, conditions in source_flags.items():
            if flag in flags:
                flags[flag].conditions += conditions
            else:
                flags[flag] = Flag(flag, conditions)

    return flags


def get_flag(flag_name, sources=None):
    """ Get a single flag and all its conditions """
    if sources is None:
        sources = getattr(settings, 'FLAG_SOURCES', DEFAULT_FLAG_SOURCES)

    conditions = []
    for source_str in sources:
        source_cls = import_string(source_str)
        source_obj = source_cls()
        conditions += source_obj.get_flag(flag_name)

    return Flag(flag_name, conditions)
