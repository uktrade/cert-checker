from django.contrib import admin
from django.urls import path
from check.views import PingdomHealthCheckView, PingdomWarningView, PingdomErrorView


urlpatterns = [
    path('', admin.site.urls),
    path('pingdom/healthcheck/', PingdomHealthCheckView.as_view()),
    path('pingdom/warnings/', PingdomWarningView.as_view()),
    path('pingdom/errors/', PingdomErrorView.as_view()),
]
