from django.db import migrations


GENERIC_COLLECTOR = "collectors.generic_html.GenericHTMLCollector"
UNIVERSITY_NAME = "Universidad de Las Americas"
JOBS_URL = "https://empleos.udla.edu.ec/search/?q=&locationsearch="
TEMPLATE_NAME = "SAP SuccessFactors job results"


def configure_vs019_udla(apps, schema_editor):
    Collector = apps.get_model("collectors", "Collector")
    CollectorTemplate = apps.get_model("collectors", "CollectorTemplate")
    University = apps.get_model("universities", "University")

    university = University.objects.filter(name=UNIVERSITY_NAME).first()
    if university is None:
        return

    university.jobs_url = JOBS_URL
    university.save(update_fields=["jobs_url", "updated_at"])
    template, _ = CollectorTemplate.objects.update_or_create(
        name=TEMPLATE_NAME,
        defaults={
            "description": "Reusable selectors for server-rendered SAP SuccessFactors job results.",
            "list_selector": "#searchresults tbody tr.data-row",
            "title_selector": ".jobTitle.hidden-phone .jobTitle-link",
            "link_selector": ".jobTitle.hidden-phone .jobTitle-link",
            "date_selector": ".colDate .jobDate",
            "description_selector": "./self::*",
            "exclude_patterns": "cerrad[ao]\nfinalizad[ao]\nexpirad[ao]\narchivo\nhist[oó]ric",
        },
    )
    Collector.objects.update_or_create(
        name="udla",
        defaults={
            "university": university,
            "template": template,
            "module_path": GENERIC_COLLECTOR,
            "enabled": True,
            "priority": 160,
            "timeout": 30,
            "max_age_days": 30,
            "status": "idle",
        },
    )


def remove_vs019_udla(apps, schema_editor):
    Collector = apps.get_model("collectors", "Collector")
    CollectorTemplate = apps.get_model("collectors", "CollectorTemplate")
    University = apps.get_model("universities", "University")

    Collector.objects.filter(name="udla").delete()
    CollectorTemplate.objects.filter(name=TEMPLATE_NAME).delete()
    University.objects.filter(name=UNIVERSITY_NAME, jobs_url=JOBS_URL).update(jobs_url="")


class Migration(migrations.Migration):
    dependencies = [
        ("collectors", "0009_collector_deadline_selector_collector_max_age_days_and_more"),
    ]

    operations = [
        migrations.RunPython(configure_vs019_udla, remove_vs019_udla),
    ]
