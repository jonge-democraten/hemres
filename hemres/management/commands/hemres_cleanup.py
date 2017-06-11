from __future__ import print_function
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import models
from hemres.models import JaneusSubscriber, EmailSubscriber
from janeus import Janeus


class Command(BaseCommand):
    help = 'Delete the subscriptions of Janeus users that no longer exist and of email subscribers without subscriptions'

    def handle(self, *args, **kwargs):
        for s in EmailSubscriber.objects.annotate(num=models.Count('subscriptions')).filter(num=0):
            s.delete()

        if not hasattr(settings, 'JANEUS_SERVER'):
            print("Janeus is not configured!")
            return

        for s in JaneusSubscriber.objects.all():
            if Janeus().by_lidnummer(s.member_id) is None:
                print("Deleted {}".format(s.member_id))
                s.delete()
