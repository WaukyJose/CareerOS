from django.db.models import Q
from rest_framework import viewsets

from .models import Job
from .serializers import JobSerializer


class JobViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = JobSerializer

    def get_queryset(self):
        queryset = Job.objects.select_related("university").all()
        params = self.request.query_params

        university = params.get("university")
        if university:
            queryset = queryset.filter(university__name__icontains=university)

        province = params.get("province")
        if province:
            queryset = queryset.filter(university__province__iexact=province)

        city = params.get("city")
        if city:
            queryset = queryset.filter(university__city__iexact=city)

        status = params.get("status")
        if status:
            queryset = queryset.filter(status=status)

        source = params.get("source")
        if source:
            queryset = queryset.filter(source=source)

        query = params.get("q")
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | Q(description__icontains=query)
            )

        ordering = params.get("ordering")
        if ordering == "newest":
            queryset = queryset.order_by("-created_at", "-id")
        elif ordering == "deadline":
            queryset = queryset.order_by("deadline_date", "title")
        elif ordering == "university":
            queryset = queryset.order_by("university__name", "title")

        return queryset
