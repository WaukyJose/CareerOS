from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string

from .base import BaseCollector
from .models import Collector


class CollectorRegistry:
    def __init__(self):
        self._collectors = {}

    def register(self, collector_class):
        name = getattr(collector_class, "name", "")
        if not name:
            raise ValueError("Collector class must define a non-empty name.")
        if name in self._collectors:
            raise ValueError(f"Collector already registered: {name}")
        self._collectors[name] = collector_class
        return collector_class

    def get(self, name):
        return self._collectors[name]

    def all(self):
        return dict(self._collectors)

    def clear(self):
        self._collectors.clear()

    def load_class(self, module_path):
        try:
            collector_class = import_string(module_path)
        except ImportError as exc:
            raise ImproperlyConfigured(
                f"Unable to import collector '{module_path}'."
            ) from exc

        if not issubclass(collector_class, BaseCollector):
            raise ImproperlyConfigured(
                f"Collector '{module_path}' must inherit BaseCollector."
            )
        return collector_class

    def enabled_definitions(self, names=None):
        queryset = Collector.objects.select_related("university").filter(enabled=True)
        if names:
            queryset = queryset.filter(name__in=names)
        return list(queryset.order_by("priority", "name"))


registry = CollectorRegistry()
