from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    authentication_classes: list = []

    @extend_schema(
        responses=inline_serializer("Health", {"status": serializers.CharField()}),
        tags=["health"],
    )
    def get(self, request) -> Response:
        return Response({"status": "ok"})
