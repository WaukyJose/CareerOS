import logging
from html.parser import HTMLParser
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from universities.models import University

from .base import BaseCollector
from .registry import registry
from .retry import retry_with_backoff
from .types import JobRecord


logger = logging.getLogger("collectors.espe")


class ESPEListingParser(HTMLParser):
    keywords = (
        "convocatoria",
        "concurso",
        "merito",
        "mérito",
        "docente",
        "academico",
        "académico",
        "titular",
    )

    def __init__(self, base_url):
        super().__init__()
        self.base_url = base_url
        self.links = []
        self._active_href = None
        self._active_text = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        attrs = dict(attrs)
        href = attrs.get("href", "").strip()
        if href:
            self._active_href = href
            self._active_text = []

    def handle_data(self, data):
        if self._active_href:
            self._active_text.append(data)

    def handle_endtag(self, tag):
        if tag != "a" or not self._active_href:
            return
        title = " ".join(" ".join(self._active_text).split())
        href = self._active_href
        haystack = f"{title} {href}".lower()
        if title and any(keyword in haystack for keyword in self.keywords):
            self.links.append(
                {
                    "title": title,
                    "url": urljoin(self.base_url, href),
                    "href": href,
                }
            )
        self._active_href = None
        self._active_text = []


class ESPECollector(BaseCollector):
    name = "espe"
    university_name = "Universidad de las Fuerzas Armadas ESPE"

    def __init__(self, fetcher=None, logger=None, collector_config=None):
        super().__init__(logger=logger, collector_config=collector_config)
        self.fetcher = fetcher or self._fetch_url

    def collect(self):
        university = self._get_university()
        if not university:
            self.logger.warning("ESPE university record was not found.")
            return []
        if not university.jobs_url:
            self.logger.warning("ESPE university record does not define jobs_url.")
            return []

        html = retry_with_backoff(lambda: self.fetcher(university.jobs_url), attempts=3)
        records = self.parse(html, university)
        self.logger.info("ESPE jobs found: %s", len(records))
        return records

    def parse(self, html, university):
        parser = ESPEListingParser(university.jobs_url)
        try:
            parser.feed(html)
        except Exception:
            self.logger.exception("Failed to parse ESPE listings.")
            return []

        records = []
        seen_urls = set()
        for link in parser.links:
            if link["url"] in seen_urls:
                continue
            seen_urls.add(link["url"])
            records.append(
                JobRecord(
                    source=self.name,
                    source_id=link["url"],
                    title=link["title"],
                    institution_name=university.name,
                    source_url=link["url"],
                    location=f"{university.city}, {university.province}",
                    raw_data={
                        "href": link["href"],
                        "source_page": university.jobs_url,
                    },
                )
            )
        return records

    def _get_university(self):
        if self.collector_config:
            return self.collector_config.university
        return University.objects.filter(name=self.university_name).first()

    def _fetch_url(self, url):
        timeout = self.collector_config.timeout if self.collector_config else 20
        request = Request(url, headers={"User-Agent": "CareerOS/0.1"})
        with urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="replace")
