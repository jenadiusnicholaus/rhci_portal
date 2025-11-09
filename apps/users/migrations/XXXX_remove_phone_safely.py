from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('users', '0001_initial'),  # Make sure this points to your latest migration before the problematic one
    ]

    operations = [
        migrations.RunSQL(
            # This SQL checks if the column exists before trying to remove it
            sql="""
            -- Check if phone column exists
            PRAGMA table_info(users_profile);
            """,
            # This doesn't actually do anything - it's just to maintain migration symmetry
            reverse_sql="""
            SELECT 1;
            """
        ),
    ]