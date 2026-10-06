# VS021 validation

Verified 2026-10-06. Only the three VS021 institutions were configured. No custom collectors, framework changes, enrichment changes, matching changes, PDF parsing, or SSL bypasses were introduced.

| Institution | Official URL | Collector / template used | Active jobs extracted | Skipped items | Skip reason / issue |
|---|---|---:|---:|---:|---|
| Universidad Nacional de Chimborazo (UNACH) | https://www.unach.edu.ec/ | `GenericHTMLCollector`; direct collector selectors, no template | 5 | 39 | 16 listing links did not match academic-hiring include patterns; 23 matched exclusions such as becas, movilidad, idioma, capacitación, or closed/historical terms. |
| Universidad Regional Amazónica Ikiam | https://www.ikiam.edu.ec/index.php/trabaja-con-nosotros/ | `GenericHTMLCollector`; direct collector selectors, no template | 0 | 64 | The official careers page exposes academic listings as direct PDF/upload links. The shared extraction safety filter blocks PDF and `/wp-content/uploads/` URLs, so the collector succeeds with zero jobs rather than importing attachments. |
| Universidad de las Artes (UArtes) | https://www.uartes.edu.ec/sitio/en/trabaja-en-la-uartes/ | `GenericHTMLCollector`; direct collector selectors, no template | 0 | 10 | The official page exposes WordPress Download Manager links through `/download/` URLs and many result notices. The shared extraction safety filter blocks download URLs; result notices are also excluded. |

## Commands run

```bash
python manage.py migrate
python manage.py test_collector unach
python manage.py test_collector ikiam
python manage.py test_collector uartes
python manage.py test collectors
python manage.py makemigrations --check --dry-run
python manage.py check
```

## Results

```text
python manage.py test_collector unach
Extracted 5 job(s).

python manage.py test_collector ikiam
Extracted 0 job(s).

python manage.py test_collector uartes
Extracted 0 job(s).

python manage.py test collectors
Ran 56 tests in 1.675s
OK

python manage.py makemigrations --check --dry-run
No changes detected

python manage.py check
System check identified no issues (0 silenced).
```

## Final collector health

| Collector | Health status | Last job count | Notes |
|---|---:|---:|---|
| `unach` | healthy | 5 | Active HTML detail links extracted. |
| `ikiam` | empty | 0 | Official source is configured; current academic links are blocked attachment URLs. |
| `uartes` | empty | 0 | Official source is configured; current links are blocked download URLs. |
