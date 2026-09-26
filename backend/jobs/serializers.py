from rest_framework import serializers

from .models import Job


class JobSerializer(serializers.ModelSerializer):
    university = serializers.CharField(source="university.name", read_only=True)
    university_id = serializers.IntegerField(source="university.id", read_only=True)
    city = serializers.CharField(source="university.city", read_only=True)
    province = serializers.CharField(source="university.province", read_only=True)

    class Meta:
        model = Job
        fields = (
            "id",
            "title",
            "description",
            "university",
            "university_id",
            "city",
            "province",
            "source",
            "external_id",
            "url",
            "status",
            "location",
            "department",
            "employment_type",
            "discipline",
            "required_degree",
            "salary",
            "contract_type",
            "language",
            "remote",
            "keywords",
            "posted_date",
            "deadline_date",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields
