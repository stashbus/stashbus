from django.shortcuts import render

from django.contrib.auth.models import Group, User
from stashrest.models import DataProducer, Secret

from rest_framework import permissions, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request

from stashrest.serializers import (
    DataProducerSerializer,
    SecretSerializer,
    GroupSerializer,
    UserSerializer,
)
from stashrest.mongo import brno_weather, btc_prices
from stashrest.models import OWMPayload, Message

from typing import Dict, List, Any


class DataProducerViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    queryset = DataProducer.objects.all()
    serializer_class = DataProducerSerializer
    # permission_classes = [permissions.IsAuthenticated]


class SecretViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    queryset = Secret.objects.all()
    serializer_class = SecretSerializer
    # permission_classes = [permissions.IsAuthenticated]


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """

    queryset = Group.objects.all().order_by("name")
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]


class BrnoWeatherListView(APIView):
    def get(self, request: Request) -> Response:
        cursor = brno_weather.find().sort("timestamp", -1).limit(100)
        results: List[Dict[str, Any]] = []

        for doc in cursor:
            doc["_id"] = str(doc["_id"])  # Convert ObjectId
            entry = OWMPayload(**doc)
            results.append(entry.model_dump())

        return Response(results)


class BTCPriceListView(APIView):
    def get(self, request: Request) -> Response:
        cursor = btc_prices.find().sort("timestamp", -1).limit(100)
        results: List[Dict[str, Any]] = []

        for doc in cursor:
            doc["_id"] = str(doc["_id"])  # Convert ObjectId
            entry = Message(**doc)
            results.append(entry.model_dump())

        return Response(results)
