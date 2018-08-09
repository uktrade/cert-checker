import datetime as dt
from django.db import models
from django.db.models import Q


def current_time():
    return dt.datetime.now(dt.timezone.utc)


class DomainManager(models.Manager):
    def get_domain_check_list(self):
        """Logic: If the domain is OK check it every 24 hours;
        if the domain is in WARNING or ERROR state, check it hourly"""

        return self.filter(
            Q(status=Domain.NOTCHECKED) |
            Q(status__in=[Domain.WARNING, Domain.ERROR], last_checked__gte=current_time - dt.timedelta(60)) |
            Q(status=Domain.OK, last_checked__gte=current_time - dt.timedelta(24*60))
        )

    def has_errors(self):
        return Domain.objects.filter(status=Domain.ERROR).exists()

    def has_warnings(self):
        return Domain.objects.filter(status=Domain.WARNING).exists()

    def has_check_run_recently(self):
        """Has the checker run in the last hour?"""
        return Domain.objects.filter(
            status_in=[Domain.OK, Domain.ERROR, Domain.WARNING],
            last_checked__lt=current_time() - dt.timedelta(hours=1)).exists()


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


class DomainManager(models.Manager):
    def get_domains_due_for_checking(self):
        """Logic: If the domain is OK check it every 24 hours;
        if the domain is in WARNING or ERROR state, check it hourly"""

        return self.filter(
            Q(status=Domain.NOTCHECKED) |
            Q(status__in=[Domain.WARNING, Domain.ERROR], last_checked__gte=current_time - dt.timedelta(60)) |
            Q(status=Domain.OK, last_checked__gte=current_time - dt.timedelta(24*60))
        )

    def has_errors(self):
        return Domain.objects.filter(status=Domain.ERROR).exists()

    def has_warnings(self):
        return Domain.objects.filter(status=Domain.WARNING).exists()

    def has_check_run_recently(self):
        """Has the checker run in the last hour?"""
        return Domain.objects.filter(
            status_in=[Domain.OK, Domain.ERROR, Domain.WARNING],
            last_checked__lt=current_time - dt.timedelta(60)).exists()
