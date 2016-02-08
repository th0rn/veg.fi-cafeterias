#!/bin/bash

# Used in production by cron, as per something like this in crontab:
# 5 0 * * * ./update.sh >&2
# In order to have cron send emails, add the following to crontab:
# MAILTO=<your@email>
# Then install a sendmail program, such as:
# msmtp-mta
# Sample ~/.msmtprc configuration:
# # Set default values for all following accounts.
# defaults
# auth           on
# tls            on
# tls_trust_file /etc/ssl/certs/ca-certificates.crt
# logfile        ~/.msmtp.log

# # yahoo
# account yahoo
# host smtp.mail.yahoo.com
# user <yahoo_user>
# from <yahoo_user>@yahoo.com
# password <password>

# # Set a default account
# account default : yahoo

flock -n /tmp/vegfi.lock "$HOME"/env/bin/python -m vegfi.veg --output-dir /data/www/
