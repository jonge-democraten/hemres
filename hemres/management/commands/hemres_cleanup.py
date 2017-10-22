from __future__ import print_function
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import models
from hemres.models import JaneusSubscriber, EmailSubscriber
from janeus import Janeus


class Command(BaseCommand):
    help = 'Delete the subscriptions of Janeus users that no longer exist and of email subscribers without subscriptions'

    def add_arguments(self, parser):
        parser.add_argument('-n', '--dryrun,', action='store_true', dest='dryrun', default=False, help='Do not actually delete anything')

    def handle(self, *args, **kwargs):
        # if cleanup receives any arguments, interpret as "dry run"
        do_not_delete = kwargs['dryrun']
        if do_not_delete:
            print("Dry run of cleanup, not actually deleting anything.")

        for s in EmailSubscriber.objects.annotate(num=models.Count('subscriptions')).filter(num=0):
            print("Deleting {}.".format(str(s)))
            if not do_not_delete: s.delete()

        if not hasattr(settings, 'JANEUS_SERVER'):
            print("Janeus is not configured!")
            return

        for s in JaneusSubscriber.objects.all():
            if Janeus().by_lidnummer(s.member_id) is None:
                print("Deleting {}".format(s.member_id))
                if not do_not_delete: s.delete()
