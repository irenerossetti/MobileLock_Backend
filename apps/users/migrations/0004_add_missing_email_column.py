from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0003_add_missing_name_columns"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE users_usuario
                ADD COLUMN IF NOT EXISTS email varchar(254) NOT NULL DEFAULT '';
            """,
            reverse_sql="""
                ALTER TABLE users_usuario
                DROP COLUMN IF EXISTS email;
            """,
        ),
    ]
