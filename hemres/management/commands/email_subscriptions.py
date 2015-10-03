from __future__ import print_function
from django.core.management.base import BaseCommand
from hemres.models import EmailSubscriber


class Command(BaseCommand):
    help = 'List subscriptions of email users'

    def handle(self, *args, **kwargs):
        if len(args):
            qs = EmailSubscriber.objects.filter(email=args[0])
        else:
            qs = EmailSubscriber.objects.select_related('subscriptions').order_by('email')
        for s in qs:
            print("Subscriptions of {}".format(s.email))
            for sub in s.subscriptions.all():
                print("* {} ({})".format(sub.label, sub.name))
            print()
