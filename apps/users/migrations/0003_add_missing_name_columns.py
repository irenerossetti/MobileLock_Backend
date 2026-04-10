from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_profile"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE users_usuario
                ADD COLUMN IF NOT EXISTS first_name varchar(150) NOT NULL DEFAULT '';
            """,
            reverse_sql="""
                ALTER TABLE users_usuario
                DROP COLUMN IF EXISTS first_name;
            """,
        ),
        migrations.RunSQL(
            sql="""
                ALTER TABLE users_usuario
                ADD COLUMN IF NOT EXISTS last_name varchar(150) NOT NULL DEFAULT '';
            """,
            reverse_sql="""
                ALTER TABLE users_usuario
                DROP COLUMN IF EXISTS last_name;
            """,
        ),
    ]
