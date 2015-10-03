from __future__ import print_function
from django.core.management.base import BaseCommand
from hemres import models


class Command(BaseCommand):
    help = 'Remove subscription of email user'
    args = 'email list_label'

    def handle(self, *args, **kwargs):
        if len(args) != 2:
            print("Please provide two arguments")
            return

        # get member_id and label from args
        email = str(args[0])
        label = str(args[1])

        # retrieve MailingList to add
        qs = models.MailingList.objects.filter(label=label)
        if len(qs):
            ml = qs[0]
        else:
            print("Mailing list not found!")
            return

        # retrieve email subscriber
        s = models.EmailSubscriber.objects.filter(email=email)
        if len(s):
            s = s[0]
        else:
            print("Subscriber not found!")
            return

        # remove mailing list
        s.subscriptions.remove(ml)

        # save!
        s.save()
