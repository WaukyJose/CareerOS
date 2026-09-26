from rest_framework import serializers


class DashboardSummarySerializer(serializers.Serializer):
    total_jobs = serializers.IntegerField()
    active_jobs = serializers.IntegerField()
    matched_jobs = serializers.IntegerField()
    saved_jobs = serializers.IntegerField()
    applied_jobs = serializers.IntegerField()
    interviews = serializers.IntegerField()
    offers = serializers.IntegerField()
    accepted = serializers.IntegerField()
    closing_soon = serializers.IntegerField()
    new_jobs_last_7_days = serializers.IntegerField()
    average_match_score = serializers.FloatField()
    top_match_score = serializers.IntegerField()
