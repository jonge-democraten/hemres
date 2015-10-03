from __future__ import print_function
from django.conf import settings
from django.core.management.base import BaseCommand
from hemres.models import JaneusSubscriber


class Command(BaseCommand):
    help = 'List subscriptions of Janeus users'

    def handle(self, *args, **kwargs):
        if not hasattr(settings, 'JANEUS_SERVER'):
            print("Janeus is not configured!")
            return

        if len(args):
            qs = JaneusSubscriber.objects.filter(member_id=args[0])
        else:
            qs = JaneusSubscriber.objects.select_related('subscriptions').order_by('member_id')
        for s in qs:
            print("Subscriptions of {}".format(s.member_id))
            for sub in s.subscriptions.all():
                print("* {} ({})".format(sub.label, sub.name))
            print()
