# Settings

## Defining flags

### `FLAGS_SOURCES`

Default: `('flags.sources.SettingsFlagsSource', 'flags.sources.DatabaseFlagsSource',)`

A list or tuple containing the full Python path strings to classes that provides a [`get_flags()` method](api/sources/#flag-sources). The `get_flags()` method is expected to return a dictionary of flags and [`Condition` objects](api/sources/#conditioncondition-value-sourcenone-objnone). All flags returned by all flag sources will be available to check.

### `FLAGS`

Default: `{}`

A dictionary of feature flags and optional conditions used when `'flags.sources.SettingsFlagsSource'` is in [`FLAGS_SOURCES`](#flag_sources).

Conditions can either be included as:

- A dictionary with the condition name as the key and expected value as value
- A list of 2-tuples with the format `(condition name: expected value)`

```python
FLAGS = {
  'FLAG_WITH_EMPTY_CONDITIONS': {}
  'FLAG_WITH_DICT_CONDITIONS': {
    'condition name': 'value flag is expected to match to be enabled',
  },
  'FLAG_WITH_LISTED_CONDITIONS': [
    ('path matches',  r'^/matching-path.*'),
    ('path matches',  r'^/other-path.*'),
  ]
}
```

The advantage of a list of 2-tuples is that the same condition can be repeated for different expected values.
