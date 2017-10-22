from django.core.management.base import BaseCommand
from hemres import models
from filelock import FileLock, Timeout
from smtplib import SMTPRecipientsRefused
import logging


logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(fmt='%(asctime)s %(message)s', datefmt='%H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class Command(BaseCommand):
    help = 'Start the Hemres worker'

    def add_arguments(self, parser):
        parser.add_argument('lock_filename', help="filename of lockfile used to ensure only one send is running")

    def send_mails(self):
        try:
            # Get all "tasks" from the database
            for ns in models.NewsletterToSubscriber.objects.all():
                # Check if the email address is not empty
                if ns.target_email == "":
                    logger.info("Skipping and deleting {} due to no email address".format(ns.pk))
                    ns.delete()
                else:
                    logger.info("Sending {}...".format(ns.pk))
                    try:
                        # Try sending the email, and report exception if it didn't work
                        # Note that send_mail also deletes the object from the database...
                        # Note that Django turns "autocommit" on for database transactions,
                        # this is important as otherwise our DELETE queries are never committed.
                        ns.send_mail()
                    except SMTPRecipientsRefused as e:
                        logger.exception(e)
                        ns.delete()
                    except Exception as e:
                        logger.exception(e)
        except Exception as e:
            logger.exception(e)

    def handle(self, *args, **kwargs):
        # We require 1 additional argument, which is the filename for locking
        try:
            with FileLock(kwargs['lock_filename'], timeout=0):
                logger.info("Going to send mails")
                self.send_mails()
                logger.info("Done, bye!")
        except Timeout:
            logger.info("Not sending mails, lockfile locked")
