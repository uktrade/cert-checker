import datetime as dt

from django.core.management.base import BaseCommand
from check_tls_certs import check_domains, domain_definitions_from_lines, get_cert_from_domain, get_domain_certs


from check.models import Domain


def supress_statuses(status_list):
    return list(filter(
        lambda item: not (item[0] == 'warning' and item[1].startswith('More alternate names than specified')),
        status_list))


class Command(BaseCommand):
    help = 'Scan domains and verify SSL certificates'

    def handle(self, *args, **options):

        domain_objects = Domain.objects.get_domain_check_list()

        if not domain_objects:
            self.stdout.write(self.style.WARNING('Nothing to check.'))
            return

        domains = domain_definitions_from_lines([item.domain_name() for item in domain_objects])

        domain_certs = get_domain_certs(domains)
        results = check_domains(domains, domain_certs, dt.datetime.utcnow())

        for domain_list, status_list, expiry_date in results:

            status_list = supress_statuses(status_list)

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

        self.stdout.write(self.style.SUCCESS('Scanned TLS certs on {} domains'.format(len(results))))
