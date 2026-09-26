from rest_framework import serializers

from .models import Application


class ApplicationSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="job.title", read_only=True)
    university = serializers.CharField(source="job.university.name", read_only=True)
    profile_name = serializers.CharField(source="researcher_profile.full_name", read_only=True)

    ALLOWED_TRANSITIONS = {
        Application.Status.SAVED: {
            Application.Status.APPLIED,
            Application.Status.WITHDRAWN,
        },
        Application.Status.APPLIED: {
            Application.Status.INTERVIEW,
            Application.Status.OFFER,
            Application.Status.ACCEPTED,
            Application.Status.REJECTED,
            Application.Status.WITHDRAWN,
        },
        Application.Status.INTERVIEW: {
            Application.Status.OFFER,
            Application.Status.ACCEPTED,
            Application.Status.REJECTED,
            Application.Status.WITHDRAWN,
        },
        Application.Status.OFFER: {
            Application.Status.ACCEPTED,
            Application.Status.REJECTED,
            Application.Status.WITHDRAWN,
        },
        Application.Status.ACCEPTED: set(),
        Application.Status.REJECTED: set(),
        Application.Status.WITHDRAWN: set(),
    }

    class Meta:
        model = Application
        fields = (
            "id",
            "researcher_profile",
            "profile_name",
            "job",
            "job_title",
            "university",
            "status",
            "saved_at",
            "applied_at",
            "interview_at",
            "offer_at",
            "accepted_at",
            "rejected_at",
            "notes",
        )
        read_only_fields = (
            "id",
            "profile_name",
            "job_title",
            "university",
            "saved_at",
            "applied_at",
            "interview_at",
            "offer_at",
            "accepted_at",
            "rejected_at",
        )

    def validate_status(self, value):
        if not self.instance or value == self.instance.status:
            return value
        allowed = self.ALLOWED_TRANSITIONS[self.instance.status]
        if value not in allowed:
            raise serializers.ValidationError(
                f"Cannot transition from {self.instance.status} to {value}."
            )
        return value

    def validate_researcher_profile(self, value):
        request = self.context.get("request")
        if request and value.user_id != request.user.id:
            raise serializers.ValidationError("You can only manage your own applications.")
        return value
