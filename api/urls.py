from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register(r'register', RegisterViewSet, basename='register')
router.register(r'balance', BalanceViewSet, basename='balance')
router.register(r'orders', OrdersViewSet, basename='orders')
router.register(r'trade', TradeViewSet, basename='trade')

urlpatterns = [
    path('', include(router.urls)),
    path('login/', LoginViewSet.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

# for url in router.urls:
#     print(url)