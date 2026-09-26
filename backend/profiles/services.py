import re
import unicodedata


class MatchService:
    WEIGHTS = {
        "research_interest": 35,
        "position_type": 20,
        "degree": 15,
        "institution_preference": 10,
        "employment_type": 10,
        "location": 10,
    }

    DEGREE_RANKS = {
        "bachelor": 1,
        "licenciatura": 1,
        "ingenieria": 1,
        "master": 2,
        "maestria": 2,
        "msc": 2,
        "doctorate": 3,
        "doctoral": 3,
        "doctorado": 3,
        "phd": 3,
    }
    @classmethod
    def match(cls, job, profile):
        points = {}
        missing = []

        job_text = cls._normalize(
            " ".join((job.title, job.discipline, job.department, *job.keywords))
        )
        interests = list(profile.research_interests.all())
        total_interest_weight = sum(interest.weight for interest in interests)
        matched_interest_weight = sum(
            interest.weight
            for interest in interests
            if cls._normalize(interest.name) in job_text
        )
        points["research_interest"] = (
            cls.WEIGHTS["research_interest"] * matched_interest_weight / total_interest_weight
            if total_interest_weight
            else 0
        )

        matched_role = cls._match_role(job.title, profile)
        points["position_type"] = cls.WEIGHTS["position_type"] if matched_role else 0

        required_degree = cls._degree_rank(cls._normalize(job.required_degree))
        profile_degree = cls._degree_rank(cls._normalize(profile.highest_degree))
        degree_match = bool(required_degree and profile_degree >= required_degree)
        points["degree"] = cls.WEIGHTS["degree"] if degree_match else 0

        institution_match = profile.preferred_institutions.filter(
            university_id=job.university_id
        ).exists()
        points["institution_preference"] = (
            cls.WEIGHTS["institution_preference"] if institution_match else 0
        )

        employment_match = cls._matches_any(
            job.employment_type,
            profile.preferred_employment_types,
        )
        points["employment_type"] = (
            cls.WEIGHTS["employment_type"] if employment_match else 0
        )

        job_location = " ".join(
            (job.location, job.university.city, job.university.province)
        )
        location_match = cls._matches_any(job_location, profile.preferred_locations)
        points["location"] = cls.WEIGHTS["location"] if location_match else 0

        for criterion, value in points.items():
            if value == 0:
                missing.append(criterion)

        score = max(0, min(100, round(sum(points.values()))))
        matched = score >= profile.minimum_match_score
        earned = [name for name, value in points.items() if value > 0]
        explanation = (
            f"Score {score}/100; matched role: {matched_role.name if matched_role else 'none'}; "
            f"matched: {', '.join(earned) or 'none'}; "
            f"missing: {', '.join(missing) or 'none'}."
        )
        return {
            "score": score,
            "matched": matched,
            "matched_role": matched_role,
            "missing": missing,
            "explanation": explanation,
        }

    @classmethod
    def _degree_rank(cls, text):
        ranks = [rank for term, rank in cls.DEGREE_RANKS.items() if term in text]
        return max(ranks, default=0)

    @classmethod
    def _match_role(cls, job_title, profile):
        normalized_title = cls._normalize(job_title)
        candidates = []
        for role in profile.preferred_roles.filter(is_active=True):
            terms = [role.name, *role.aliases]
            for term in terms:
                normalized_term = cls._normalize(term)
                if normalized_term and re.search(
                    rf"(?:^|\s){re.escape(normalized_term)}(?:$|\s)",
                    normalized_title,
                ):
                    candidates.append((len(normalized_term), role.name.casefold(), role))
                    break
        if not candidates:
            return None
        return max(candidates, key=lambda candidate: (candidate[0], candidate[1]))[2]

    @classmethod
    def _matches_any(cls, value, preferences):
        normalized_value = cls._normalize(value)
        return bool(normalized_value) and any(
            cls._normalize(preference) in normalized_value
            for preference in preferences
            if cls._normalize(preference)
        )

    @staticmethod
    def _normalize(value):
        value = unicodedata.normalize("NFKD", value or "")
        value = "".join(character for character in value if not unicodedata.combining(character))
        return " ".join(re.findall(r"[a-z0-9]+", value.casefold()))
