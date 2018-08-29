# DIT TLS certificate checker

## Overview

This app checks the TLS certs on domains. It will raise warnings and error alerts via pingdom endpoints.

A Warning state occurs if a domain is due to expire within 14 days.

An error state occurs if:

- the domain is unreacheable
- the certificate common and alternative names don't match the domain name
- the certificate has expired

Warning/Error states are reported by the following pingdom endpoints:

`/pingdom/warnings/`  
`/pingdom/errors/`

An additional health check endpoint checks if the periodic ssl check task has run within the last hour:

`/pingdom/healthcheck/`

## Implementation

The app uses the django admin app to manage the list of monitored domains.

A django management command needs to be run periodically [suggested: every 30 minutes] to perform the TLS checks: `./manage.py run_ssl_check` 

Domains are checked every 24 hours by default, but if there are errors or warnings, the domain is rechecked every hour.

## Dependencies

1. python 3.6.x+
2. a postgres database OR sqlite3 for local development

## Local dev environment

To run the app locally:

1. Clone this repository and cd into the cloned directory

2. Create a virutalenv and activate it

3. Install requirements `pip install -r requirements`

4. `cp sample_env .env`

5. `./manage.py runserver`

6. Add some domains via the admin (to gain access you'll need to create a superuser: `./manage.py createsuperuser`)

7. Run the management command to check the domains: `./manage.py run_ssl_check`

## Run the tests

`./manage.py test`

## Deployment to gov uk paas

The app is ready for gov uk paas deployment. It requires a postgres database binding to the application. To deploy simply run: `cf push cert-checker`

## Other considerations

### IP filtering

IP filtering is enabled by setting the following env vars:

`RESTRICT_ADMIN=True`  
`ALLOWED_ADMIN_IPS=a comma separated list of IPv4 addresses`

### failed login account lockout

The app uses django-axes, which will lock access after 3 failed attempts.  If this happens, access can be restored using `./manage.py axes_reset`  NOTE: this command will unlock all accounts. See the django-axes documentation for more commands.
