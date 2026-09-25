import logging
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from lxml import html

from .base import BaseCollector
from .retry import retry_with_backoff
from .types import JobRecord


logger = logging.getLogger("collectors.generic_html")


class GenericHTMLCollector(BaseCollector):
    name = "generic_html"

    def __init__(self, fetcher=None, logger=None, collector_config=None):
        super().__init__(logger=logger, collector_config=collector_config)
        self.fetcher = fetcher or self._fetch_url

    def collect(self):
        if not self.collector_config:
            self.logger.warning("GenericHTMLCollector requires collector_config.")
            return []
        university = self.collector_config.university
        if not university.jobs_url:
            self.logger.warning("%s does not define jobs_url.", university.name)
            return []
        if not self.collector_config.list_selector:
            self.logger.warning("%s does not define list_selector.", self.collector_config.name)
            return []

        page = retry_with_backoff(
            lambda: self.fetcher(university.jobs_url),
            attempts=3,
        )
        records = self.parse(page)
        self.logger.info(
            "Generic HTML collector %s found %s jobs.",
            self.collector_config.name,
            len(records),
        )
        return records

    def parse(self, page):
        document = html.fromstring(page)
        items = self._select(document, self.collector_config.list_selector)
        records = []
        seen_urls = set()
        university = self.collector_config.university

        for item in items:
            title = self._text(item, self.collector_config.title_selector)
            link = self._link(item, self.collector_config.link_selector)
            if not title or not link:
                self.logger.warning("Skipping listing with missing title or link.")
                continue

            source_url = urljoin(university.jobs_url, link)
            if source_url in seen_urls:
                continue
            seen_urls.add(source_url)

            description = self._text(item, self.collector_config.description_selector)
            date_text = self._text(item, self.collector_config.date_selector)
            records.append(
                JobRecord(
                    source=self.collector_config.name,
                    source_id=source_url,
                    title=title,
                    institution_name=university.name,
                    source_url=source_url,
                    location=f"{university.city}, {university.province}",
                    description=description,
                    raw_data={
                        "source_page": university.jobs_url,
                        "date_text": date_text,
                    },
                )
            )
        return records

    def _select(self, node, selector):
        if not selector:
            return []
        try:
            if selector.startswith("/") or selector.startswith(".//"):
                return node.xpath(selector)
            return node.cssselect(selector)
        except Exception:
            self.logger.exception("Invalid selector: %s", selector)
            return []

    def _text(self, node, selector):
        if not selector:
            return ""
        matches = self._select(node, selector)
        if not matches:
            return ""
        match = matches[0]
        if isinstance(match, str):
            return self._normalize(match)
        return self._normalize(match.text_content())

    def _link(self, node, selector):
        if not selector:
            return ""
        matches = self._select(node, selector)
        if not matches:
            return ""
        match = matches[0]
        if isinstance(match, str):
            return self._normalize(match)
        href = match.get("href") or match.get("src") or match.text_content()
        return self._normalize(href)

    def _normalize(self, value):
        return " ".join((value or "").split())

    def _fetch_url(self, url):
        timeout = self.collector_config.timeout if self.collector_config else 20
        request = Request(url, headers={"User-Agent": "CareerOS/0.1"})
        with urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="replace")
