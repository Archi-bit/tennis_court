from django.db import migrations


LEGACY_MODELS = (
    ('core', 'clubinfo'),
    ('core', 'clubrule'),
    ('courts', 'courttype'),
    ('courts', 'court'),
    ('coaches', 'coach'),
    ('services', 'service'),
    ('services', 'pricecategory'),
    ('services', 'priceitem'),
    ('news', 'news'),
    ('news', 'galleryimage'),
    ('tournaments', 'tournament'),
)


def verify_schema(apps, connection):
    """Refuse adoption if the existing SQLite schema differs from our models."""
    if connection.vendor != 'sqlite':
        raise RuntimeError('The Tennis consolidation was verified for SQLite only.')
    try:
        apps.get_app_config('tennis')
    except LookupError as error:
        raise RuntimeError(
            'Incomplete legacy migration history. Apply all eight original '
            'migrations with the original source before consolidating Tennis.'
        ) from error

    with connection.cursor() as cursor:
        tables = set(connection.introspection.table_names(cursor))
        for _, model_name in LEGACY_MODELS:
            model = apps.get_model('tennis', model_name)
            table = model._meta.db_table
            if table not in tables:
                raise RuntimeError(f'Missing legacy table: {table}')
            columns = {
                column.name: column
                for column in connection.introspection.get_table_description(cursor, table)
            }
            fields = model._meta.local_fields
            if set(columns) != {field.column for field in fields}:
                raise RuntimeError(f'Unexpected columns in {table}')
            constraints = list(connection.introspection.get_constraints(cursor, table).values())
            for field in fields:
                column = columns[field.column]
                if (
                    column.type_code.lower() != field.db_type(connection).lower()
                    or column.null_ok != field.null
                    or bool(column.pk) != field.primary_key
                ):
                    raise RuntimeError(f'Unexpected field schema: {table}.{field.column}')
                field_constraints = [
                    constraint for constraint in constraints
                    if constraint['columns'] == [field.column]
                ]
                if field.unique and not any(
                    c['unique'] or c['primary_key'] for c in field_constraints
                ):
                    raise RuntimeError(f'Missing unique constraint: {table}.{field.column}')
                if field.db_index and not field.unique and not any(
                    c['index'] for c in field_constraints
                ):
                    raise RuntimeError(f'Missing index: {table}.{field.column}')
                if field.db_check(connection) and not any(c['check'] for c in field_constraints):
                    raise RuntimeError(f'Missing check constraint: {table}.{field.column}')
                if field.is_relation:
                    target = (field.related_model._meta.db_table, field.target_field.column)
                    if not any(c['foreign_key'] == target for c in field_constraints):
                        raise RuntimeError(f'Unexpected foreign key: {table}.{field.column}')
    connection.check_constraints()


def preserve_content_types(apps, schema_editor):
    verify_schema(apps, schema_editor.connection)
    content_types = apps.get_model('contenttypes', 'ContentType').objects.using(
        schema_editor.connection.alias
    )
    changes = []
    # Check every collision before changing any row. Never delete/merge IDs.
    for old_label, model_name in LEGACY_MODELS:
        old = content_types.filter(app_label=old_label, model=model_name).first()
        new = content_types.filter(app_label='tennis', model=model_name).first()
        if old is not None and new is not None:
            raise RuntimeError(
                f'Conflicting ContentTypes for {old_label}.{model_name} and '
                f'tennis.{model_name}; no ContentTypes were changed.'
            )
        if old is not None:
            changes.append(old.pk)
    # Auth permissions, user/group grants and admin logs reference these IDs.
    content_types.filter(pk__in=changes).update(app_label='tennis')


class Migration(migrations.Migration):
    dependencies = [
        ('tennis', '0001_initial'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    # Deliberately irreversible: restore the backup with its original source
    # instead of rolling back CreateModel operations and dropping legacy tables.
    operations = [migrations.RunPython(preserve_content_types)]
