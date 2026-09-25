from django.db import migrations


def create_espe_collector(apps, schema_editor):
    Collector = apps.get_model("collectors", "Collector")
    University = apps.get_model("universities", "University")
    university = University.objects.filter(
        name="Universidad de las Fuerzas Armadas ESPE"
    ).first()
    if not university:
        return
    Collector.objects.update_or_create(
        name="espe",
        defaults={
            "university": university,
            "module_path": "collectors.espe.ESPECollector",
            "enabled": True,
            "priority": 100,
            "timeout": 20,
            "status": "idle",
        },
    )


def remove_espe_collector(apps, schema_editor):
    Collector = apps.get_model("collectors", "Collector")
    Collector.objects.filter(name="espe").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("collectors", "0002_collector"),
        ("universities", "0003_set_espe_jobs_url"),
    ]

    operations = [
        migrations.RunPython(create_espe_collector, remove_espe_collector),
    ]
