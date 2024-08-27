from django.urls import path
from .views import *
from rest_framework.routers import DefaultRouter


urlpatterns = [
    path('api/csrf/', csrf, name='csrf'),

    path('login', LoginView.as_view(), name='login'),
]


router = DefaultRouter()
router.register('register', RegisterViewset, basename='register')
urlpatterns += router.urls

# for urls in urlpatterns:
#     print(urls)