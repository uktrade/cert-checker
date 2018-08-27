import time

from django.http import HttpResponse
from django.views import View

from .models import Domain


class BasePingdomView(View):
    def do_check(self):
        raise NotImplemented

    def get(self, request):
        start_time = time.time()
        success = self.do_check()
        status_text = 'OK' if success else 'DOWN'
        response_time = time.time() - start_time

        return HttpResponse(
            f'<pingdom_http_custom_check>'
            f'<status>{status_text}</status>'
            f'<response_time>{response_time}</response_time>'
            f'</pingdom_http_custom_check>'
        )


class PingdomHealthCheckView(BasePingdomView):
    def do_check(self):
        return Domain.objects.has_check_run_recently()


class PingdomWarningView(BasePingdomView):
    def do_check(self):
        return not Domain.objects.has_warnings()


class PingdomErrorView(BasePingdomView):
    def do_check(self):
        return not Domain.objects.has_errors()

