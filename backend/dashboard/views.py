from rest_framework.response import Response
from rest_framework.views import APIView

from jobs.serializers import JobSerializer
from profiles.serializers import JobMatchSerializer

from .serializers import DashboardSummarySerializer
from .services import DashboardService


class DashboardSummaryView(APIView):
    def get(self, request):
        serializer = DashboardSummarySerializer(DashboardService.summary(user=request.user))
        return Response(serializer.data)


class DashboardTopMatchesView(APIView):
    def get(self, request):
        serializer = JobMatchSerializer(DashboardService.top_matches(user=request.user), many=True)
        return Response(serializer.data)


class DashboardRecentJobsView(APIView):
    def get(self, request):
        serializer = JobSerializer(DashboardService.recent_jobs(), many=True)
        return Response(serializer.data)


class DashboardClosingSoonView(APIView):
    def get(self, request):
        serializer = JobSerializer(DashboardService.closing_soon(), many=True)
        return Response(serializer.data)
