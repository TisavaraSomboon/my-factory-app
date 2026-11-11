"""Thin HTTP layer: parse input, call a service, serialize the result."""
from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from . import rules, services
from .filters import OrderFilter
from .models import Order
from .serializers import (
    ApproveInputSerializer,
    FabricRulesSerializer,
    OrderEventSerializer,
    OrderSerializer,
    ReadyDispatchInputSerializer,
    RejectInputSerializer,
)

ERROR_SCHEMA_NOTE = "Errors use the envelope {\"error\": {\"code\", \"message\", \"details\"}}."


class FabricRulesView(APIView):
    @extend_schema(responses=FabricRulesSerializer, tags=["fabric-rules"],
                   summary="Garment type to allowed fabrics table")
    def get(self, request: Request) -> Response:
        return Response(rules.fabric_rules_table())


@extend_schema_view(
    list=extend_schema(summary="List orders (filters: status, garment_type, overdue, search)"),
    create=extend_schema(
        summary="Create an order (R1 fabric compatibility)",
        examples=[OpenApiExample("Kitchen apron", request_only=True, value={
            "name": "Kitchen apron", "garment_type": "HEAT_INSULATION", "fabric_type": "COTTON",
            "requester_username": "somchai", "address": "1 Sukhumvit Rd, Bangkok", "quantity": 10})],
    ),
    partial_update=extend_schema(summary="Edit an order (R2: only in DESIGN)"),
    destroy=extend_schema(summary="Delete an order (R3: only in DESIGN)"),
)
class OrderViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Order.objects.select_related("pattern", "color")
    serializer_class = OrderSerializer
    filterset_class = OrderFilter
    search_fields = ["name", "requester_username"]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]  # PUT disabled

    def perform_create(self, serializer: OrderSerializer) -> None:
        data = dict(serializer.validated_data)
        actor = data.pop("actor", None)
        serializer.instance = services.create_order(actor=actor, **data)

    def perform_update(self, serializer: OrderSerializer) -> None:
        data = dict(serializer.validated_data)
        actor = data.pop("actor", None)
        serializer.instance = services.update_order(serializer.instance, actor=actor, **data)

    def perform_destroy(self, instance: Order) -> None:
        services.delete_order(instance)

    @extend_schema(
        request=ApproveInputSerializer, responses=OrderSerializer,
        summary="Approve the current stage and advance",
        description="Required stage fields depend on the order status. " + ERROR_SCHEMA_NOTE,
        examples=[
            OpenApiExample("FABRIC_PREP", request_only=True, value={
                "actor": "buyer1", "swatch_fabric_type": "COTTON", "measured_fabric_meters": "25.50"}),
            OpenApiExample("STITCHING", request_only=True, value={
                "actor": "sewer1", "assembled_pieces_count": 10}),
            OpenApiExample("QA", request_only=True, value={
                "actor": "qa1", "results": [{"inspection_id": 1, "passed": True}]}),
            OpenApiExample("PACKAGING", request_only=True, value={
                "actor": "packer1", "tracking_number": "TH123456789"}),
        ],
    )
    @action(detail=True, methods=["post"])
    def approve(self, request: Request, pk: str | None = None) -> Response:
        order = self.get_object()
        body = ApproveInputSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        data = dict(body.validated_data)
        actor, note = data.pop("actor"), data.pop("note", "")
        order = services.approve(order, actor, note, **data)
        return Response(OrderSerializer(order).data)

    @extend_schema(
        request=RejectInputSerializer, responses=OrderSerializer, summary="Reject the current stage",
        description="Sends the order to the reject target and increments rework_count. " + ERROR_SCHEMA_NOTE,
        examples=[OpenApiExample("QA fail", request_only=True,
                                 value={"actor": "qa1", "reason": "Loose stitching on seams"})],
    )
    @action(detail=True, methods=["post"])
    def reject(self, request: Request, pk: str | None = None) -> Response:
        order = self.get_object()
        body = RejectInputSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        order = services.reject(order, **body.validated_data)
        return Response(OrderSerializer(order).data)

    @extend_schema(
        request=ReadyDispatchInputSerializer, responses=OrderSerializer,
        summary="Mark ready for dispatch (PACKAGING only)",
        description="is_ready=false means hold in the finished goods staging area. " + ERROR_SCHEMA_NOTE,
        examples=[OpenApiExample("Ready", request_only=True,
                                 value={"actor": "packer1", "is_ready": True, "cartons_count": 3})],
    )
    @action(detail=True, methods=["post"], url_path="ready-dispatch")
    def ready_dispatch(self, request: Request, pk: str | None = None) -> Response:
        order = self.get_object()
        body = ReadyDispatchInputSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        order = services.set_ready_dispatch(order, **body.validated_data)
        return Response(OrderSerializer(order).data)

    @extend_schema(responses=OrderEventSerializer(many=True), summary="Order timeline", filters=False)
    @action(detail=True, methods=["get"], pagination_class=None, filter_backends=[])
    def events(self, request: Request, pk: str | None = None) -> Response:
        order = self.get_object()
        return Response(OrderEventSerializer(order.events.all(), many=True).data)
