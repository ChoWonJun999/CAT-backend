from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
from .models import Profile
from .serializers import *
import logging
import requests
import pyupbit
import pandas as pd
from functools import wraps
from django.contrib.auth import get_user_model
import auto_trade_thread as att
from threading import Lock


logger = logging.getLogger(__name__)

auto_trade_thread = None
auto_trade_thread_lock = Lock()

def api_key_required(view_func):
    @wraps(view_func)
    def _wrapped_view(view, request, *args, **kwargs):
        user = request.user

        try:
            profile = get_object_or_404(Profile.objects, user=user)
            _access_key = profile.access_key
            _secret_key = profile.secret_key
        except Profile.DoesNotExist:
            return Response(
                {'detail': '프로필 정보가 없습니다. 먼저 API 키를 등록해주세요.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not _access_key or not _secret_key:
            return Response(
                {'detail': 'API 키가 등록되어 있지 않습니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        request.upbit = pyupbit.Upbit(_access_key, _secret_key)
        try:
            return view_func(view, request, *args, **kwargs)
        except requests.exceptions.RequestException as e:
            logger.exception("Upbit API 요청 중 예외 발생")
            return Response(
                {'detail': 'Upbit API 요청 중 오류가 발생했습니다.', 'error': str(e)},
                status=status.HTTP_502_BAD_GATEWAY
            )
        except Exception as e:
            logger.exception("잔액 조회 중 서버 내부 오류 발생")
            return Response(
                {'detail': '서버 내부 오류', 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    return _wrapped_view

class LoginViewSet(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class RegisterViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]
    AuthUser = get_user_model()
    queryset = AuthUser.objects.all()
    serializer_class = RegisterSerializer

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        try:
            required_keys = ['access_key', 'secret_key']
            missing_keys = [key for key in required_keys if key not in request.data]
            if missing_keys:
                return Response(
                    {'detail': f'필수 키가 누락되었습니다: {", ".join(missing_keys)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            _access_key = request.data['access_key']
            _secret_key = request.data['secret_key']

            try:
                _upbit_check = pyupbit.Upbit(_access_key, _secret_key)
                _upbit_check.get_api_key_list()
            except ValueError as e:
                return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response(
                    {'detail': 'Upbit API 오류', 'error': str(e)},
                    status=status.HTTP_502_BAD_GATEWAY
                )

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.exception("회원가입 중 예외 발생")
            return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def update(self, request, pk=None):
        user = get_object_or_404(self.queryset, pk=pk)
        serializer = self.serializer_class(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BalanceViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @api_key_required
    def list(self, request):
        _upbit = request.upbit

        my_tickers = _upbit.get_balances()
        
        tickers = []
        for ticker in my_tickers :
            if not ticker['avg_buy_price_modified'] and ticker['avg_buy_price'] != '0' :
                tickers.append("KRW-"+ticker['currency'])

        df_tickers = pd.DataFrame(my_tickers)
        df_tickers = df_tickers.reset_index()
        df_tickers.rename(columns = {'currency' : 'market'}, inplace = True)
        contents = pyupbit.get_current_price(ticker=tickers, verbose=True)
        df = pd.DataFrame(contents)
        df = df.reset_index()
        df['market'] = [temp[4:] for temp in df['market']]
        final_df = pd.merge(df_tickers, df, on='market')
        final_df['balance'] = final_df['balance'].astype(float)
        final_df['buy_price'] = final_df['balance'] * final_df['avg_buy_price'].astype(float)
        final_df['current_price'] = final_df['balance'] * final_df['trade_price']
        final_df['eva_price'] = (final_df['balance'] * final_df['trade_price']) - (final_df['balance'] * final_df['avg_buy_price'].astype(float))
        final_df['eva_percent'] = ((final_df['balance'] * final_df['trade_price']) - (final_df['balance'] * final_df['avg_buy_price'].astype(float)))/(final_df['balance'] * final_df['avg_buy_price'].astype(float))*100
        final_df = final_df.sort_values('current_price', ascending=False)

        return Response(final_df.to_dict(orient='records'), status=status.HTTP_200_OK)

class OrdersViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    @api_key_required
    def list(self, request):
        queryset = self.queryset.filter(user=request.user)
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def create(self, request):
        serializers = self.serializer_class(data=request.data)
        if serializers.is_valid():
            serializers.save()
            return Response(serializers.data, status=status.HTTP_200_OK)
        else:
            return Response(serializers.errors, status=status.HTTP_400_BAD_REQUEST)

class TradeViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    queryset = Profile.objects.all()
    serializer_class = TradeSerializer

    def retrieve(self, request, pk=None):
        user = get_object_or_404(self.queryset, user=request.user)
        serializer = self.serializer_class(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    @api_key_required
    def update(self, request, pk=None):
        user = get_object_or_404(self.queryset, user=request.user)
        serializer = self.serializer_class(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            global auto_trade_thread
            with auto_trade_thread_lock:
                if request.data.get('state'):
                    _upbit = request.upbit
                    auto_trade_thread = att.Worker(_upbit, request.data.get('method'))
                    auto_trade_thread.daemon = True
                    auto_trade_thread.start()
                else:
                    if auto_trade_thread:
                        auto_trade_thread.kill()
                        auto_trade_thread = None
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
