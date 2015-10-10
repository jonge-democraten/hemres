from __future__ import print_function
from django.conf import settings
from django.core.management.base import BaseCommand
from hemres import models
from janeus import Janeus


class Command(BaseCommand):
    help = 'Remove subscription of Janeus user'
    args = 'member_id list_label'

    def handle(self, *args, **kwargs):
        if not hasattr(settings, 'JANEUS_SERVER'):
            print("Janeus is not configured!")
            return

        if len(args) != 2:
            print("Please provide two arguments")
            return

        # get member_id and label from args
        member_id = int(args[0])
        label = str(args[1])

        # retrieve MailingList to add
        qs = models.MailingList.objects.filter(label=label)
        if len(qs):
            ml = qs[0]
        else:
            print("Mailing list not found!")
            return

        # find member from Janeus
        res = Janeus().by_lidnummer(member_id)
        if res is None:
            print("Janeus user not found!")
            return

        # retrieve Janeus subscriber
        s = models.JaneusSubscriber.objects.filter(member_id=int(member_id))
        if len(s):
            s = s[0]
        else:
            print("Janeus subscriber not found!")
            return

        # remove mailing list
        s.subscriptions.remove(ml)

        # update for required attributes
        s.update_janeus_newsletters()

        # save!
        s.save()
