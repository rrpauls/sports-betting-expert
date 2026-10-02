"""Offline validator for the subset used by the vendored Agent Plugins 1.0 schema.

Unsupported constraints fail closed. This keeps previously installed updater
runtimes compatible without installing new dependencies into their working venv.
"""
from __future__ import annotations
import re

SUPPORTED = {'$schema', '$id', 'title', 'description', 'type', 'const', 'properties',
             'additionalProperties', 'required', 'items', 'minLength', 'maxLength', 'pattern'}


def validate(value, schema: dict, path: str = '$') -> None:
    unknown = set(schema) - SUPPORTED
    if unknown:
        raise ValueError(f'unsupported schema constraints at {path}: {sorted(unknown)}')
    kinds = {'object': dict, 'array': list, 'string': str}
    kind = schema.get('type')
    if kind is not None:
        if kind not in kinds:
            raise ValueError(f'unsupported schema type: {kind}')
        if not isinstance(value, kinds[kind]):
            raise ValueError(f'{path} must be {kind}')
    if 'const' in schema and value != schema['const']:
        raise ValueError(f'{path} does not match required constant')
    if isinstance(value, str):
        if len(value) < schema.get('minLength', 0) or len(value) > schema.get('maxLength', float('inf')):
            raise ValueError(f'{path} violates string length constraints')
        if 'pattern' in schema and not re.search(schema['pattern'], value):
            raise ValueError(f'{path} violates pattern')
    if isinstance(value, dict):
        for required in schema.get('required', []):
            if required not in value:
                raise ValueError(f'{path} is missing {required}')
        properties = schema.get('properties', {})
        extra = schema.get('additionalProperties', True)
        for name, item in value.items():
            if name in properties:
                validate(item, properties[name], f'{path}.{name}')
            elif extra is False:
                raise ValueError(f'{path} has unknown property {name}')
            elif isinstance(extra, dict):
                validate(item, extra, f'{path}.{name}')
    if isinstance(value, list) and 'items' in schema:
        for index, item in enumerate(value):
            validate(item, schema['items'], f'{path}[{index}]')
