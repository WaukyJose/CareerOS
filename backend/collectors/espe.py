import logging
from urllib.request import Request, urlopen

from universities.models import University

from .base import BaseCollector
from .extraction import JobExtractor
from .retry import retry_with_backoff


logger = logging.getLogger("collectors.espe")


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

        page = retry_with_backoff(lambda: self.fetcher(university.jobs_url), attempts=3)
        extractor = JobExtractor(
            base_url=university.jobs_url,
            include_patterns=self._include_patterns(),
            exclude_patterns=self._exclude_patterns(),
            allowed_extensions=self._config_value("allowed_extensions"),
            blocked_extensions=self._config_value("blocked_extensions"),
        )
        links = extractor.extract_links(page)
        records = [
            extractor.record_from_link(link=link, source=self.name, university=university)
            for link in links
        ]
        self.logger.info("ESPE jobs found: %s", len(records))
        return records

    def parse(self, page, university):
        extractor = JobExtractor(
            base_url=university.jobs_url,
            include_patterns=self._include_patterns(),
            exclude_patterns=self._exclude_patterns(),
            allowed_extensions=self._config_value("allowed_extensions"),
            blocked_extensions=self._config_value("blocked_extensions"),
        )
        return [
            extractor.record_from_link(link=link, source=self.name, university=university)
            for link in extractor.extract_links(page)
        ]

    def _include_patterns(self):
        if self.collector_config and self.collector_config.include_patterns:
            return self.collector_config.include_patterns
        return "\n".join(("vacante", "convocatoria docente", "concurso docente"))

    def _exclude_patterns(self):
        if self.collector_config and self.collector_config.exclude_patterns:
            return self.collector_config.exclude_patterns
        return "\n".join(("bases", "cronograma", "resultado", "reglamento"))

    def _config_value(self, field):
        return getattr(self.collector_config, field, "") if self.collector_config else ""

    def _get_university(self):
        if self.collector_config:
            return self.collector_config.university
        return University.objects.filter(name=self.university_name).first()

    def _fetch_url(self, url):
        timeout = self.collector_config.timeout if self.collector_config else 20
        request = Request(url, headers={"User-Agent": "CareerOS/0.1"})
        with urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="replace")
