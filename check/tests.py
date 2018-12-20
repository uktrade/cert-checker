import datetime as dt

from django.test import TestCase, RequestFactory

from .models import Domain
from .views import PingdomErrorView, PingdomWarningView, PingdomHealthCheckView


def current_time():
    return dt.datetime.now(dt.timezone.utc)


def domain_factory(**kwargs):
    default = {
        'last_checked': current_time()-dt.timedelta(days=2),
        'name': 'testing.com',
        'port': '443',
        'status': Domain.OK,
        'status_text': ''
    }

    default.update(kwargs)

    return Domain.objects.create(**default)


class PingdomHealthCheckViewTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_cron_job_has_not_run_recently_error(self):
        request = self.factory.get('/pingdom/healthcheck/')

        response = PingdomHealthCheckView.as_view()(request)

        self.assertContains(response, 'DOWN')

    def test_cron_job_has_run_recently_ok(self):
        domain_factory(last_checked=current_time()-dt.timedelta(minutes=20))

        request = self.factory.get('/pingdom/healthcheck/')

        response = PingdomHealthCheckView.as_view()(request)

        self.assertContains(response, 'OK')


class PingdomWarningViewTestCase(TestCase):
    def test_has_warnings(self):
        domain_factory(status=Domain.WARNING)

        request = RequestFactory().get('/pingdom/warnings/')
        response = PingdomWarningView.as_view()(request)

        self.assertContains(response, 'DOWN')
        self.assertEqual(response.status_code, 200)

    def test_has_warnings_false(self):
        request = RequestFactory().get('/pingdom/warnings/')
        response = PingdomWarningView.as_view()(request)

        self.assertContains(response, 'OK')


class PingdomErrorViewTestCase(TestCase):
    def test_has_errors(self):
        domain_factory(status=Domain.ERROR)

        request = RequestFactory().get('/pingdom/errors/')
        response = PingdomErrorView.as_view()(request)

        self.assertContains(response, 'DOWN')
        self.assertEqual(response.status_code, 200)

    def test_has_errors_false(self):
        request = RequestFactory().get('/pingdom/errors/')
        response = PingdomErrorView.as_view()(request)

        self.assertContains(response, 'OK')
        self.assertEqual(response.status_code, 200)


class DomainModelTestCase(TestCase):
    def test_has_errors_true(self):
        domain_factory(status=Domain.ERROR)

        self.assertTrue(Domain.objects.has_errors())
        self.assertFalse(Domain.objects.has_warnings())

    def test_has_warnings_true(self):
        domain_factory(status=Domain.WARNING)

        self.assertFalse(Domain.objects.has_errors())
        self.assertTrue(Domain.objects.has_warnings())

    def test_has_check_run_recently_true(self):
        domain_factory(last_checked=current_time()-dt.timedelta(minutes=20))
        self.assertTrue(Domain.objects.has_check_run_recently())

    def test_has_check_run_recently_false(self):
        self.assertFalse(Domain.objects.has_check_run_recently())

    def test_get_domain_check_list(self):

        domain_factory(
            name='domain1', last_checked=current_time()-dt.timedelta(minutes=240), status=Domain.ERROR)
        domain_factory(
            name='domain2', last_checked=current_time()-dt.timedelta(minutes=30), status=Domain.ERROR)
        domain_factory(
            name='domain3', last_checked=current_time()-dt.timedelta(hours=25), status=Domain.OK)
        domain_factory(
            name='domain4', last_checked=current_time()-dt.timedelta(hours=20), status=Domain.OK)
        domain_factory(
            name='domain5', last_checked=current_time()-dt.timedelta(minutes=200), status=Domain.WARNING)
        domain_factory(
            name='domain6', last_checked=current_time()-dt.timedelta(minutes=30), status=Domain.WARNING)
        domain_factory(
            name='domain7', last_checked=None, status=Domain.NOTCHECKED
        )

        domains = set(Domain.objects.get_domain_check_list().values_list('name', flat=True))

        self.assertEqual({'domain1', 'domain3', 'domain5', 'domain7'}, domains)

    def test_update_supresses_status(self):

        domain = domain_factory()

        status_text = [
            ('warning', 'More alternate names than specified ...'),
        ]

        domain = Domain.objects.update_domain_status(
            [domain.domain_name()], current_time()+dt.timedelta(days=30), status_text)

        self.assertEqual(domain.status, Domain.OK)

    def test_update_records_last_checked_timestamp(self):

        domain = domain_factory()

        last_checked = domain.last_checked

        domain = Domain.objects.update_domain_status(
            [domain.domain_name()], current_time()-dt.timedelta(days=30), [])

        self.assertNotEqual(last_checked, domain.last_checked)

    def test_expired_cert_recorded_as_error(self):
        domain = domain_factory()

        domain = Domain.objects.update_domain_status(
            [domain.domain_name()], current_time() - dt.timedelta(days=1), [])

        self.assertEqual(domain.status, Domain.ERROR)
        self.assertIn(domain.status_text, 'error: certificate has expired')

    def test_nearly_expiring_cert_recorded_as_warning(self):
        domain = domain_factory()

        domain = Domain.objects.update_domain_status(
            [domain.domain_name()], current_time()+dt.timedelta(days=5), [])

        self.assertEqual(domain.status, Domain.WARNING)
        self.assertEqual(domain.status_text, 'warning: certificate is due to expire soon')
