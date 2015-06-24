import pymysql

import os

from optparse import make_option
from urllib.parse import urlparse, parse_qs
from django.core.management.base import BaseCommand, CommandError
from django.contrib.sites.models import Site
from django.utils.text import slugify

from hemres.models import *


class Command(BaseCommand):
    #args = 'mysql://user:password@host/database'
    help = 'Import jnews data from the old JD Joomla database'
    option_list = BaseCommand.option_list + (
        make_option('--host',
                    dest='host',
                    default='localhost',
                    help='MySQL host'),
        make_option('--user',
                    dest='user',
                    default='mysql',
                    help='MySQL user'),
        make_option('--password',
                    dest='password',
                    default='password',
                    help='MySQL password'),
        make_option('--database',
                    dest='database',
                    default='database',
                    help='MySQL database'),
        make_option('--tableprefix',
                    dest='tableprefix',
                    default='2gWw',
                    help='Joomla table prefix')
        )

    def handle(self, *args, **options):
        try:
            db = pymysql.connect(host=options.get('host'),
                                 user=options.get('user'),
                                 password=options.get('password'),
                                 database=options.get('database'))
        except pymysql.err.OperationalError as e:
            raise CommandError(e)
        cur = db.cursor()
        
        # Fetch all mailinglists
        cur.execute("SELECT * FROM " + options.get('tableprefix') + "_jnews_lists;")
        mailinglists = cur.fetchall()
        for mailinglist in mailinglists:
            ml = MailingList(name=mailinglist[1])
            ml.label = slugify(mailinglist[1])
            ml.save()
            # Fetch all mailings that belong to this list
            cur.execute("SELECT * FROM " + options.get('tableprefix') + \
                "_jnews_mailings WHERE id IN (SELECT mailing_id from " + options.get('tableprefix') + \
                "_jnews_listmailings WHERE list_id=%d);" % (mailinglist[0],))
            mailings = cur.fetchall()
            for mailing in mailings:
                nl = Newsletter()
                nl.subject = mailing[5]
                nl.content = mailing[9]
                nl.date = mailing[13]
                nl.public = mailing[17]
                nl.save()
        


