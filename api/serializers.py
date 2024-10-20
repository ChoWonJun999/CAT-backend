from rest_framework import serializers
from .models import *
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

AuthUser = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        return token
    
class RegisterSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(source='profile.phone_number')
    address = serializers.CharField(source='profile.address')
    access_key = serializers.CharField(source='profile.access_key')
    secret_key = serializers.CharField(source='profile.secret_key')
    state = serializers.CharField(source='profile.state')

    class Meta:
        model = AuthUser
        fields = ('id', 'username', 'password', 'phone_number', 'address', 'access_key', 'secret_key', 'state')
        extra_kwargs = {
            'password': {'write_only': True}
            , 'access_key': {'write_only': True}
            , 'secret_key': {'write_only': True}
            }

    def create(self, validated_data):
        profile_data = {
            'phone_number': validated_data['profile']['phone_number'],
            'address': validated_data['profile']['address'],
            'access_key': validated_data['profile']['access_key'],
            'secret_key': validated_data['profile']['secret_key'],
            'state': validated_data['profile']['state'],
        }

        user = AuthUser.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )

        Profile.objects.create(
            user=user,
            **profile_data
        )

        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})
        instance.username = validated_data.get('username', instance.username)
        
        if 'password' in validated_data:
            instance.set_password(validated_data['password'])

        instance.save()

        profile = instance.profile
        profile.phone_number = profile_data.get('phone_number', profile.phone_number)
        profile.address = profile_data.get('address', profile.address)
        profile.access_key = profile_data.get('access_key', profile.access_key)
        profile.secret_key = profile_data.get('secret_key', profile.secret_key)
        profile.state = profile_data.get('state', profile.state)
        profile.save()

        return instance
    
class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'
    
class TradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('id', 'state', 'user')
    
    def update(self, instance, validated_data):
        instance.state = validated_data['state']
        instance.save()
        return instance
