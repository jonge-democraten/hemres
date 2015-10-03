from __future__ import print_function
from django.conf import settings
from django.core.management.base import BaseCommand
from hemres.models import JaneusSubscriber


class Command(BaseCommand):
    help = 'Delete Janeus users that no longer exist'

    def handle(self, *args, **kwargs):
        if not hasattr(settings, 'JANEUS_SERVER'):
            print("Janeus is not configured!")
            return

        for s in JaneusSubscriber.objects.all():
            if Janeus().by_lidnummer(s.member_id) is None:
                print("Deleted {}".format(s.member_id))
                s.delete()
