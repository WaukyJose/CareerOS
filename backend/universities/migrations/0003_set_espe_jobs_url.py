from django.db import migrations


def set_espe_jobs_url(apps, schema_editor):
    University = apps.get_model("universities", "University")
    University.objects.filter(name="Universidad de las Fuerzas Armadas ESPE").update(
        jobs_url="https://uth.espe.edu.ec/concurso-de-meritos/"
    )


def clear_espe_jobs_url(apps, schema_editor):
    University = apps.get_model("universities", "University")
    University.objects.filter(name="Universidad de las Fuerzas Armadas ESPE").update(
        jobs_url=""
    )


class Migration(migrations.Migration):
    dependencies = [
        ("universities", "0002_university_jobs_url"),
    ]

    operations = [
        migrations.RunPython(set_espe_jobs_url, clear_espe_jobs_url),
    ]
