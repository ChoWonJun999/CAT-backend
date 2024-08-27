from rest_framework import serializers
from .models import *
from django.contrib.auth import get_user_model

AuthUser = get_user_model()


class AuthUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthUser
        fields = ('id', 'password', 'username', 'email')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = AuthUser.objects.create_user(**validated_data)
        return user


class ProfileSerializer(serializers.ModelSerializer):
    user = AuthUserSerializer()
    class Meta:
        model = Profile
        fields = ('id', 'user', 'phone_number', 'address', 'access_key', 'secret_key')

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = AuthUserSerializer.create(AuthUserSerializer(), validated_data=user_data)
        
        profile = Profile.objects.create(user=user, **validated_data)
        return profile
