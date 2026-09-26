from rest_framework import generics, viewsets
from django.shortcuts import get_object_or_404

from .models import JobMatch, ResearcherProfile
from .serializers import JobMatchSerializer, ResearcherProfileSerializer


class JobMatchViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = JobMatchSerializer

    def get_queryset(self):
        queryset = JobMatch.objects.filter(
            researcher_profile__user=self.request.user,
        ).select_related(
            "job__university",
            "researcher_profile",
            "matched_role",
        )
        params = self.request.query_params

        profile = params.get("profile")
        if profile and profile.isdigit():
            queryset = queryset.filter(researcher_profile_id=profile)

        minimum_score = params.get("minimum_score")
        if minimum_score and minimum_score.isdigit():
            queryset = queryset.filter(score__gte=minimum_score)

        if params.get("matched_only", "").casefold() in {"1", "true", "yes"}:
            queryset = queryset.filter(matched=True)

        university = params.get("university")
        if university:
            if university.isdigit():
                queryset = queryset.filter(job__university_id=university)
            else:
                queryset = queryset.filter(job__university__name__icontains=university)

        ordering = params.get("ordering")
        if ordering == "newest":
            return queryset.order_by("-computed_at", "-id")
        return queryset.order_by("-score", "-computed_at", "-id")


class CurrentResearcherProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ResearcherProfileSerializer

    def get_object(self):
        return get_object_or_404(ResearcherProfile, user=self.request.user)
