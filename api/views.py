from django.shortcuts import render
from django.http import HttpResponse
import jwt
from rest_framework import viewsets, permissions
from .serializers import *
from rest_framework.response import Response
from .models import *
from rest_framework.views import APIView
from rest_framework import status
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import get_token
import requests
import uuid
from urllib.parse import urlencode, unquote

@ensure_csrf_cookie
def csrf(request):
    return JsonResponse({'csrfToken': get_token(request)})


class LoginView(APIView):
    def post(self, request):
        try:
            username = request.data.get('id')
            password = request.data.get('password')

            if not username or not password:
                return Response(
                    {"error": "ID와 비밀번호를 모두 입력해 주세요."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = authenticate(username=username, password=password)
            
            if user:
                return Response({"message": "로그인 성공"}, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"error": "인증에 실패했습니다. ID와 비밀번호를 확인해 주세요."},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        except Exception as e:
            return Response(
                {"error": "서버에 문제가 발생했습니다. 잠시 후 다시 시도해 주세요.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get(self, request):
        return Response()
    

class RegisterViewset(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer

    def list(self, request):
        queryset = self.queryset
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        print(request.data)
        try:
            payload = {
                'access_key': request.data['access_key'],
                'nonce': str(uuid.uuid4()),
            }

            jwt_token = jwt.encode(payload, request.data['secret_key'])
            authorization = 'Bearer {}'.format(jwt_token)
            headers = {'Authorization': authorization,}

            server_url="https://api.upbit.com"
            res = requests.get(server_url + '/v1/api_keys', headers=headers)
            res.json()
        except Exception as e:
            print(e)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def retrieve(self, request, pk=None):
        profile = self.queryset.get(pk=pk)
        serializer = self.serializer_class(profile)
        return Response(serializer.data)

    def update(self, request, pk=None):
        profile = self.queryset.get(pk=pk)
        serializer = self.serializer_class(profile, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=400)

    def destroy(self, request, pk=None):
        profile = self.queryset.get(pk=pk)
        profile.delete()
        return Response(status=204)
        
