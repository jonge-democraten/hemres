from django_cron import CronJobBase, Schedule
from hemres.models import NewsletterToSubscriber


class SendNewslettersCronJob(CronJobBase):
    """Cronjob to send newsletters to subscribers
    Add this class to CRON_CLASSES (in settings.py)
    """
    RUN_EVERY_MINS = 1  # every minute

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'hemres.send_newsletters'  # a unique code

    def do(self):
        try:
            msgs = []

            # Get all "tasks" from the database
            for ns in NewsletterToSubscriber.objects.all():
                # Check if the email address is not empty
                if ns.target_email == "":
                    msgs.append("Skipping {} (to {}) due to no email address".format(ns.pk, ns.target_name))
                    # Just delete it...
                    ns.delete()
                else:
                    msgs.append("Sending a newsletter to {}...".format(ns.pk, ns.target_name))
                    try:
                        # Try sending the email, and report exception if it didn't work
                        # Note that send_mail also deletes the object from the database...
                        # Note that Django turns "autocommit" on for database transactions,
                        # this is important as otherwise our DELETE queries are never committed.
                        ns.send_mail()
                    except Exception as e:
                        msgs.append("Exception: {}".format(e))
        except Exception as e:
            msgs.append("Exception: {}".format(e))

        return "\n".join(msgs)
