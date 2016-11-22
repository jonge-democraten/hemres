from django.core.management.base import BaseCommand
from hemres import models
import logging
import time


logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(fmt='%(asctime)s %(message)s', datefmt='%H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class Command(BaseCommand):
    help = 'Start the Hemres worker'

    def send_mails(self):
        try:
            # Get all "tasks" from the database
            for ns in models.NewsletterToSubscriber.objects.all():
                # Check if the email address is not empty
                if ns.target_email == "":
                    logger.info("Skipping {} due to no email address".format(ns.pk))
                    ns.delete()
                elif ns.pk in self.failing_pks:
                    # Do not try sending if we had an exception last time we tried...
                    pass
                else:
                    logger.info("Sending {}...".format(ns.pk))
                    try:
                        # Try sending the email, and report exception if it didn't work
                        # Note that send_mail also deletes the object from the database...
                        # Note that Django turns "autocommit" on for database transactions,
                        # this is important as otherwise our DELETE queries are never committed.
                        ns.send_mail()
                    except Exception as e:
                        logger.exception(e)
                        self.failing_pks.append(ns.pk)
        except Exception as e:
            logger.exception(e)

    def handle(self, *args, **kwargs):
        logger.info("Starting Hemres worker!")

        self.failing_pks = []

        # In a forever loop, send all mails and then sleep for 60 seconds
        while True:
            self.send_mails()
            time.sleep(60)
