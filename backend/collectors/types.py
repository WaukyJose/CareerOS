from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class JobRecord:
    source: str
    source_id: str
    title: str
    institution_name: str
    source_url: str
    location: str = ""
    department: str = ""
    employment_type: str = ""
    discipline: str = ""
    description: str = ""
    posted_date: date | None = None
    deadline_date: date | None = None
    raw_data: dict = field(default_factory=dict)


@dataclass
class CollectorResult:
    new: int = 0
    updated: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def succeeded(self):
        return not self.errors

    def add_error(self, message):
        self.errors.append(message)
