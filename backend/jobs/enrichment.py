import re
import unicodedata


class JobEnrichmentService:
    DEGREE_PATTERNS = (
        ("PhD", r"\b(?:ph\.?d\.?|doctorado|doctoral|doctorate)\b"),
        ("Master's", r"\b(?:master|masters|maestria|msc|m\.?sc\.?)\b"),
        ("Bachelor's", r"\b(?:bachelor|licenciatura|ingenieria|grado universitario)\b"),
    )
    EMPLOYMENT_PATTERNS = (
        ("Full-time", r"\b(?:full[ -]?time|tiempo completo|jornada completa)\b"),
        ("Part-time", r"\b(?:part[ -]?time|medio tiempo|tiempo parcial)\b"),
        ("Internship", r"\b(?:internship|intern|pasantia|practicas)\b"),
        ("Temporary", r"\b(?:temporary|temporal|ocasional)\b"),
    )
    CONTRACT_PATTERNS = (
        ("Permanent", r"\b(?:permanent|indefinido|nombramiento)\b"),
        ("Fixed-term", r"\b(?:fixed[ -]?term|plazo fijo|contrato temporal)\b"),
        ("Contractor", r"\b(?:contractor|servicios profesionales|contrato civil)\b"),
    )
    DISCIPLINE_PATTERNS = (
        ("Artificial Intelligence", r"\b(?:artificial intelligence|inteligencia artificial|ai)\b"),
        ("Computer Science", r"\b(?:computer science|computacion|informatica)\b"),
        ("Data Science", r"\b(?:data science|ciencia de datos)\b"),
        ("Education", r"\b(?:education|educacion|pedagogia)\b"),
        ("Engineering", r"\b(?:engineering|ingenieria)\b"),
        ("Biology", r"\b(?:biology|biologia)\b"),
    )
    KEYWORD_PATTERNS = (
        ("Artificial Intelligence", r"\b(?:artificial intelligence|inteligencia artificial|ai)\b"),
        ("Machine Learning", r"\b(?:machine learning|aprendizaje automatico)\b"),
        ("NLP", r"\b(?:nlp|natural language processing|procesamiento de lenguaje natural)\b"),
        ("Data Science", r"\b(?:data science|ciencia de datos)\b"),
        ("Python", r"\bpython\b"),
        ("Research", r"\b(?:research|investigacion)\b"),
        ("Teaching", r"\b(?:teaching|docencia|ensenanza)\b"),
    )

    @classmethod
    def enrich(cls, job):
        text = cls._normalize(" ".join((job.title, job.description, job.department, job.discipline)))
        employment_text = cls._normalize(f"{job.employment_type} {text}")
        return {
            "discipline": cls._normalize_discipline(job.discipline, text),
            "department": cls._normalize_department(job.department, text),
            "required_degree": cls._first_match(text, cls.DEGREE_PATTERNS),
            "employment_type": (
                cls._first_match(employment_text, cls.EMPLOYMENT_PATTERNS)
                or job.employment_type.strip()
            ),
            "salary": cls._extract_salary(job.description),
            "contract_type": cls._first_match(text, cls.CONTRACT_PATTERNS),
            "language": cls._extract_language(text),
            "remote": cls._extract_remote(text),
            "keywords": [
                keyword
                for keyword, pattern in cls.KEYWORD_PATTERNS
                if re.search(pattern, text)
            ],
        }

    @classmethod
    def _normalize_discipline(cls, value, text):
        normalized_value = cls._normalize(value)
        for label, pattern in cls.DISCIPLINE_PATTERNS:
            if re.search(pattern, normalized_value):
                return label
        return cls._first_match(text, cls.DISCIPLINE_PATTERNS) or value.strip()

    @classmethod
    def _normalize_department(cls, value, text):
        if value.strip():
            return " ".join(value.split())
        match = re.search(
            r"\b(?:department of|departamento de)\s+([a-z0-9 ]+?)(?:[.,;]|\b(?:requires|requiere|seeks|busca)\b|$)",
            text,
        )
        return match.group(1).strip().title() if match else ""

    @staticmethod
    def _extract_salary(value):
        match = re.search(
            r"(?i)(?:salary|remuneracion|sueldo)?\s*:?[ \t]*(?P<amount>(?:USD\s*)?\$\s*[\d.,]+|USD\s*[\d.,]+)",
            value or "",
        )
        return " ".join(match.group("amount").split()).rstrip(".,") if match else ""

    @staticmethod
    def _extract_language(text):
        english = bool(re.search(r"\b(?:english|ingles)\b", text))
        spanish = bool(re.search(r"\b(?:spanish|espanol)\b", text))
        if english and spanish:
            return "English and Spanish"
        if english:
            return "English"
        if spanish:
            return "Spanish"
        if re.search(r"\b(?:bilingual|bilingue)\b", text):
            return "Bilingual"
        return ""

    @staticmethod
    def _extract_remote(text):
        if re.search(r"\b(?:remote|remoto|teletrabajo|work from home)\b", text):
            return True
        if re.search(r"\b(?:on[ -]?site|presencial)\b", text):
            return False
        return None

    @staticmethod
    def _first_match(text, patterns):
        for label, pattern in patterns:
            if re.search(pattern, text):
                return label
        return ""

    @staticmethod
    def _normalize(value):
        value = unicodedata.normalize("NFKD", value or "")
        value = "".join(character for character in value if not unicodedata.combining(character))
        return " ".join(re.findall(r"[a-z0-9$.,]+", value.casefold()))
