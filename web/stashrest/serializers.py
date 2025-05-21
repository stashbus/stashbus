from django.contrib.auth.models import Group, User
from rest_framework import serializers
from stashrest.models import DataProducer, Secret


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ["url", "username", "email", "groups"]


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ["url", "name"]


class DataProducerSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataProducer
        fields = ["url", "name", "command"]


class SecretSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Secret
        fields = ["url", "name", "value"]
