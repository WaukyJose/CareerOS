import re
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import PurePosixPath
from urllib.parse import urljoin, urlparse

from lxml import html

from .types import JobRecord


DEFAULT_BLOCKED_EXTENSIONS = {
    "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "zip",
    "jpg", "jpeg", "png", "gif", "webp", "svg", "bmp", "tif", "tiff",
}
VACANCY_TERMS = (
    "vacante", "convocatoria", "concurso", "docente", "profesor", "investigador",
    "research", "lecturer", "fellow", "position", "job", "career", "empleo",
)
NON_VACANCY_RE = re.compile(
    r"(?:^|[\s/_?&=.-])(viewer|download|descargar|menu|navigation|footer|login)(?:$|[\s/_?&=.-])",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ExtractedLink:
    title: str
    url: str
    raw_url: str
    description: str = ""
    department: str = ""
    discipline: str = ""
    employment_type: str = ""
    posted_date: date | None = None
    deadline_date: date | None = None


class LinkFilter:
    def __init__(self, include_patterns="", exclude_patterns="", allowed_extensions="", blocked_extensions=""):
        self.include_patterns = self._compile(include_patterns)
        self.exclude_patterns = self._compile(exclude_patterns)
        self.allowed_extensions = self._extensions(allowed_extensions)
        self.blocked_extensions = DEFAULT_BLOCKED_EXTENSIONS | self._extensions(blocked_extensions)

    def allow(self, title, url, *, context=""):
        text = f"{title} {url} {context}".lower()
        parsed = urlparse(url)
        extension = PurePosixPath(parsed.path).suffix.lower().lstrip(".")
        if extension in self.blocked_extensions:
            return False
        if extension and self.allowed_extensions and extension not in self.allowed_extensions:
            return False
        if NON_VACANCY_RE.search(text) or "/wp-content/uploads/" in parsed.path.lower():
            return False
        if self.exclude_patterns and any(pattern.search(text) for pattern in self.exclude_patterns):
            return False
        if self.include_patterns:
            return any(pattern.search(text) for pattern in self.include_patterns)
        return any(term in text for term in VACANCY_TERMS)

    @staticmethod
    def _compile(patterns):
        return [re.compile(pattern.strip(), re.IGNORECASE) for pattern in (patterns or "").splitlines() if pattern.strip()]

    @staticmethod
    def _extensions(value):
        values = value if isinstance(value, (set, tuple, list)) else re.split(r"[,\s]+", value or "")
        return {str(item).strip().lower().lstrip(".") for item in values if str(item).strip()}


class JobExtractor:
    def __init__(self, *, base_url, include_patterns="", exclude_patterns="", allowed_extensions="", blocked_extensions=""):
        self.base_url = base_url
        self.link_filter = LinkFilter(include_patterns, exclude_patterns, allowed_extensions, blocked_extensions)

    def extract_links(self, page):
        document = html.fromstring(page)
        links = []
        for element in document.xpath("//a[@href]"):
            title = self.normalize(element.text_content())
            raw_url = self.normalize(element.get("href"))
            url = urljoin(self.base_url, raw_url)
            container = self._container(element)
            context = self.normalize(container.text_content()) if container is not None else ""
            if title and raw_url and not self._inside_navigation(element):
                if self.link_filter.allow(title, url, context=context):
                    links.append(self._extracted_link(element, container, title, url, raw_url))
        return self._dedupe(links)

    def record_from_link(self, *, link, source, university):
        department, discipline, employment_type = self.infer_fields(link.title)
        return JobRecord(
            source=source, source_id=link.url, title=link.title,
            institution_name=university.name, source_url=link.url,
            location=f"{university.city}, {university.province}",
            department=link.department or department,
            discipline=link.discipline or discipline,
            employment_type=link.employment_type or employment_type,
            posted_date=link.posted_date, deadline_date=link.deadline_date,
            description=link.description,
            raw_data={"href": link.raw_url, "source_page": self.base_url},
        )

    def _extracted_link(self, element, container, title, url, raw_url):
        return ExtractedLink(
            title=title, url=url, raw_url=raw_url,
            description=self._field(container, "description"),
            department=self._field(container, "department"),
            discipline=self._field(container, "discipline"),
            employment_type=self._field(container, "employment-type"),
            posted_date=self.parse_date(self._field(container, "posted-date")),
            deadline_date=self.parse_date(self._field(container, "deadline-date")),
        )

    @staticmethod
    def _container(element):
        matches = element.xpath("ancestor::*[self::article or self::li or self::tr][1]")
        return matches[0] if matches else element.getparent()

    def _field(self, container, name):
        if container is None:
            return ""
        value = container.get(f"data-{name}")
        if value:
            return self.normalize(value)
        matches = container.xpath(f".//*[contains(concat(' ', normalize-space(@class), ' '), ' {name} ')][1]")
        return self.normalize(matches[0].text_content()) if matches else ""

    @staticmethod
    def _inside_navigation(element):
        return bool(element.xpath(
            "ancestor-or-self::*[self::nav or self::header or self::footer or @role='navigation' "
            "or contains(concat(' ', normalize-space(@class), ' '), ' menu ') "
            "or contains(concat(' ', normalize-space(@class), ' '), ' navigation ')][1]"
        ))

    @staticmethod
    def _dedupe(links):
        seen = set()
        result = []
        for link in links:
            if link.url not in seen:
                seen.add(link.url)
                result.append(link)
        return result

    @staticmethod
    def normalize(value):
        return " ".join((value or "").split())

    @staticmethod
    def parse_date(value, *, today=None):
        text = JobExtractor.normalize(value).lower()
        iso_match = re.search(r"\d{4}-\d{2}-\d{2}", text)
        if iso_match:
            try:
                return date.fromisoformat(iso_match.group(0))
            except ValueError:
                return None

        relative_match = re.search(r"hace\s+(\d+)\s+d[ií]as?", text)
        if relative_match:
            return (today or date.today()) - timedelta(days=int(relative_match.group(1)))

        months = {
            "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
            "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
            "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
        }
        spanish_match = re.search(
            r"(\d{1,2})\s+de\s+(" + "|".join(months) + r")(?:,|\s+de)?\s+(\d{4})",
            text,
        )
        if spanish_match:
            try:
                return date(
                    int(spanish_match.group(3)),
                    months[spanish_match.group(2)],
                    int(spanish_match.group(1)),
                )
            except ValueError:
                return None
        return None

    @staticmethod
    def infer_fields(title):
        text = (title or "").lower()
        department = "Docencia" if "docente" in text or "lecturer" in text else ""
        employment_type = "Tiempo completo" if "tiempo completo" in text else ""
        discipline = ""
        for candidate in ("sistemas", "electrónica", "electronica", "biology", "data science"):
            if candidate in text:
                discipline = candidate.title()
                break
        return department, discipline, employment_type
