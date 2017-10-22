""" Copyright Mezzanine """

from django.contrib.sites.models import Site
from django.contrib.sites.managers import CurrentSiteManager as DjangoCSM
from django.conf import settings
from django.db import models
import logging
import threading


_thread_local = threading.local()
logger = logging.getLogger(__name__)


def current_request():
    return getattr(_thread_local, "request", None)


class CurrentRequestMiddleware(object):
    def process_request(self, request):
        _thread_local.request = request

        site_id = request.session.get("site_id", None)
        site = None

        if site_id is not None:
            try:
                site = Site.objects.get(id=site_id)
            except Site.DoesNotExist:
                site = None
                site_id = None

        if not site_id:
            domain = request.get_host().lower()

            try:
                site = Site.objects.get(domain__iexact=domain)
                site_id = site.id
            except Site.DoesNotExist:
                site = Site(domain=domain, name=domain)
                site.save()

            site_id = site.id

        _thread_local.site_id = site_id
        _thread_local.site = site

        import django.contrib.sites.shortcuts
        django.contrib.sites.shortcuts.get_current_site = lambda request: site


def set_current_site_id(site_id):
    _thread_local.site_id = site_id
    try:
        _thread_local.site = Site.objects.get(id=site_id)
    except Site.DoesNotExist:
        _thread_local.site = None


def current_site_id():
    if not hasattr(_thread_local, 'site_id'):
        site_id = getattr(settings, 'SITE_ID', None)
        logger.warning('current_site: no site set in thread local, using SITE_ID={}'.format(site_id))
        set_current_site_id(site_id)
    return _thread_local.site_id


def current_site():
    site = getattr(_thread_local, 'site', None)
    if site is None:
        logger.error('current_site: no site set in thread local')
        return None
    return site


class CurrentSiteManager(DjangoCSM):
    def get_queryset(self):
        site_id = current_site_id()
        # if the site is None or invalid, don't use filter
        queryset = super(DjangoCSM, self).get_queryset()
        if Site.objects.filter(id=site_id).exists():
            return queryset.filter(site__id=site_id)
        else:
            return queryset


class SiteRelated(models.Model):
    objects = CurrentSiteManager()

    class Meta:
        abstract = True

    site = models.ForeignKey("sites.Site", editable=False)

    def save(self, update_site=False, *args, **kwargs):
        if update_site or not self.site_id:
            self.site_id = current_site_id()
        super(SiteRelated, self).save(*args, **kwargs)
