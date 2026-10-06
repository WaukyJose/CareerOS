from django.db import migrations


GENERIC_COLLECTOR = "collectors.generic_html.GenericHTMLCollector"

SOURCES = {
    "unach": {
        "university": "Universidad Nacional de Chimborazo",
        "url": "https://www.unach.edu.ec/",
        "priority": 170,
        "selectors": {
            "list_selector": "//a[contains(normalize-space(.), 'Ver detalles')]",
            "title_selector": "./preceding::text()[normalize-space()][1]",
            "link_selector": "./@href",
            "description_selector": "./preceding::text()[normalize-space()][1]",
            "include_patterns": "personal acad[eé]mico\ndocente\ndocentes autores\napoyo acad[eé]mico\nservicios profesionales",
            "exclude_patterns": "movilidad\nbecas\nestudiantil\nidioma\ningl[eé]s\nfranc[eé]s\njornadas\ncapacitaci[oó]n\nfinalizad[ao]\ncerrad[ao]\nexpirad[ao]\narchivo\nhist[oó]ric",
        },
    },
    "ikiam": {
        "university": "Universidad Regional Amazonica Ikiam",
        "url": "https://www.ikiam.edu.ec/index.php/trabaja-con-nosotros/",
        "priority": 180,
        "selectors": {
            "list_selector": "//a[contains(., 'PERSONAL ACAD') or contains(., 'APOYO ACAD') or contains(., 'TÉCNICO DOCENTE')]",
            "title_selector": "./self::*",
            "link_selector": "./@href",
            "include_patterns": "personal acad[eé]mico\napoyo acad[eé]mico\nt[eé]cnico docente\ndocente",
            "exclude_patterns": "analista\nasistente\nbibliotecario\nfinanciero\ninfraestructura\nseguridad de la informaci[oó]n\ncontrataci[oó]n p[uú]blica\nrelaciones interinstitucionales\ntalento humano\nacta de ganador\nterna\nfinalizad[ao]\ncerrad[ao]\nexpirad[ao]\narchivo\nhist[oó]ric",
        },
    },
    "uartes": {
        "university": "Universidad de las Artes",
        "url": "https://www.uartes.edu.ec/sitio/en/trabaja-en-la-uartes/",
        "priority": 190,
        "selectors": {
            "list_selector": "//div[contains(concat(' ', normalize-space(@class), ' '), ' media ')][.//a[contains(@class, 'wpdm-download-link')]]",
            "title_selector": ".//div[contains(concat(' ', normalize-space(@class), ' '), ' media-body ')]",
            "link_selector": ".//a[contains(@class, 'wpdm-download-link')]/@data-downloadurl",
            "description_selector": ".//div[contains(concat(' ', normalize-space(@class), ' '), ' media-body ')]",
            "include_patterns": "docente ocasional\nt[eé]cnico docente\napoyo acad[eé]mico\nconvocatoria de personal",
            "exclude_patterns": "acta de ganador\ndeclaratoria\nprocesos anteriores\nfinalizad[ao]\ncerrad[ao]\nexpirad[ao]\narchivo\nhist[oó]ric",
        },
    },
}


def configure_vs021_academic_sources(apps, schema_editor):
    Collector = apps.get_model("collectors", "Collector")
    University = apps.get_model("universities", "University")

    for name, source in SOURCES.items():
        university = University.objects.filter(name=source["university"]).first()
        if university is None:
            continue

        university.jobs_url = source["url"]
        university.save(update_fields=["jobs_url", "updated_at"])

        Collector.objects.update_or_create(
            name=name,
            defaults={
                "university": university,
                "template": None,
                "module_path": GENERIC_COLLECTOR,
                "enabled": True,
                "priority": source["priority"],
                "timeout": 30,
                "max_age_days": 30,
                "status": "idle",
                **source["selectors"],
            },
        )


def remove_vs021_academic_sources(apps, schema_editor):
    Collector = apps.get_model("collectors", "Collector")
    University = apps.get_model("universities", "University")

    Collector.objects.filter(name__in=SOURCES).delete()
    for source in SOURCES.values():
        University.objects.filter(name=source["university"], jobs_url=source["url"]).update(jobs_url="")


class Migration(migrations.Migration):
    dependencies = [
        ("collectors", "0010_seed_vs019_udla_collector"),
    ]

    operations = [
        migrations.RunPython(configure_vs021_academic_sources, remove_vs021_academic_sources),
    ]
