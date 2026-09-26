from rest_framework import mixins, viewsets

from .models import Application
from .serializers import ApplicationSerializer


class ApplicationViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ApplicationSerializer

    def get_queryset(self):
        queryset = Application.objects.filter(
            researcher_profile__user=self.request.user,
        ).select_related(
            "job__university",
            "researcher_profile",
        )
        params = self.request.query_params

        profile = params.get("profile")
        if profile and profile.isdigit():
            queryset = queryset.filter(researcher_profile_id=profile)

        status = params.get("status")
        if status:
            queryset = queryset.filter(status=status.upper())

        university = params.get("university")
        if university:
            if university.isdigit():
                queryset = queryset.filter(job__university_id=university)
            else:
                queryset = queryset.filter(job__university__name__icontains=university)

        if params.get("ordering") == "applied_at":
            return queryset.order_by("-applied_at", "-saved_at", "-id")
        return queryset.order_by("-saved_at", "-id")
