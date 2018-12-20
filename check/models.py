import datetime as dt
from django.db import models
from django.db.models import Q

from check_tls_certs import check_domains, domain_definitions_from_lines, get_cert_from_domain, get_domain_certs


def current_time():
    return dt.datetime.now(dt.timezone.utc)


def supress_statuses(status_list):
    return list(filter(
        lambda item: not (item[0] == 'warning' and item[1].startswith('More alternate names than specified')),
        status_list))


class DomainManager(models.Manager):
    def get_domain_check_list(self):
        """Logic: If the domain is OK check it every 24 hours;
        if the domain is in WARNING or ERROR state, check it hourly"""

        return self.filter(
            Q(status=Domain.NOTCHECKED) |
            Q(status__in=[Domain.WARNING, Domain.ERROR], last_checked__lt=current_time()-dt.timedelta(minutes=60)) |
            Q(status=Domain.OK, last_checked__lte=current_time() - dt.timedelta(hours=24))
        )

    def has_errors(self):
        return Domain.objects.filter(status=Domain.ERROR).exists()

    def has_warnings(self):
        return Domain.objects.filter(status=Domain.WARNING).exists()

    def has_check_run_recently(self):
        """Has the checker run in the last hour?"""
        return Domain.objects.exists() and Domain.objects.filter(
            last_checked__gt=current_time() - dt.timedelta(minutes=60)).exists()

    def update_domain_status(self, domain_list, expiry_date, status_list):
        status_list = supress_statuses(status_list)

        if expiry_date:
            if current_time().date() > expiry_date.date():
                status_list.append(['error', 'certificate has expired'])
            elif current_time().date() > expiry_date.date() - dt.timedelta(days=14):
                status_list.append(['warning', 'certificate is due to expire soon'])

        name, port = domain_list[0].split(':')

        domain_obj = Domain.objects.get(name=name, port=int(port))

        formatted_text = '\n'.join(': '.join(row) for row in status_list)

        statuses = [level for level, _ in status_list]

        if 'error' in statuses:
            status = Domain.ERROR
        elif 'warning' in statuses:
            status = Domain.WARNING
        else:
            status = Domain.OK

        domain_obj.status = status
        domain_obj.status_text = formatted_text
        domain_obj.last_checked = dt.datetime.now(dt.timezone.utc)
        domain_obj.save()

        return domain_obj

    def check_certs(self):
        domain_objects = Domain.objects.get_domain_check_list()

        domains = domain_definitions_from_lines([item.domain_name() for item in domain_objects])

        domain_certs = get_domain_certs(domains)
        results = check_domains(domains, domain_certs, dt.datetime.utcnow())

        for domain_list, status_list, expiry_date in results:
            self.update_domain_status(domain_list, expiry_date, status_list)


class Domain(models.Model):
    NOTCHECKED = 'notchecked'
    OK = 'ok'
    WARNING = 'warning'
    ERROR = 'error'

    STATUS_CHOICES = (
        (NOTCHECKED, 'Not Checked'),
        (WARNING, 'Warning'),
        (ERROR, 'Error'),
        (OK, 'OK'),
    )

    last_checked = models.DateTimeField(null=True, blank=True)
    name = models.CharField(max_length=255)
    port = models.IntegerField(default=443)
    status = models.CharField(choices=STATUS_CHOICES, default=NOTCHECKED, max_length=15)
    status_text = models.TextField()

    objects = DomainManager()

    class Meta:
        unique_together = (('name', 'port'),)

    def domain_name(self):
        return '{}:{}'.format(self.name, self.port)
