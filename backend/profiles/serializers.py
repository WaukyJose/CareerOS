from rest_framework import serializers

from .models import JobMatch, ResearcherProfile


class JobMatchSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="job.title", read_only=True)
    university = serializers.CharField(source="job.university.name", read_only=True)
    university_id = serializers.IntegerField(source="job.university_id", read_only=True)
    profile_name = serializers.CharField(source="researcher_profile.full_name", read_only=True)
    matched_role = serializers.CharField(source="matched_role.name", read_only=True, allow_null=True)

    class Meta:
        model = JobMatch
        fields = (
            "id",
            "job",
            "job_title",
            "university",
            "university_id",
            "researcher_profile",
            "profile_name",
            "score",
            "matched",
            "matched_role",
            "explanation",
            "computed_at",
        )
        read_only_fields = fields


class ResearcherProfileSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = ResearcherProfile
        fields = (
            "id",
            "user",
            "full_name",
            "highest_degree",
            "current_position",
            "country",
            "city",
            "preferred_employment_types",
            "preferred_locations",
            "minimum_match_score",
            "is_active",
            "research_interests",
            "preferred_roles",
        )
        read_only_fields = ("id", "user")
