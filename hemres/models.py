from datetime import timedelta
from django.db import models, transaction
from django.core.urlresolvers import reverse
from django.utils import timezone
from janeus import Janeus
import re


class Subscriber(models.Model):
    name = models.CharField(max_length=255, blank=True, default='')
    subscriptions = models.ManyToManyField('MailingList', related_name='subscribers', blank=True)

    def cast(self):
        try:
            return self.janeussubscriber
        except JaneusSubscriber.DoesNotExist:
            pass
        try:
            return self.emailsubscriber
        except EmailSubscriber.DoesNotExist:
            pass

    def __unicode__(self):
        return self.cast().__unicode__()


class JaneusSubscriber(Subscriber):
    member_id = models.IntegerField(unique=True)
    janeus_name = models.CharField(max_length=255, blank=True, default='')

    def __unicode__(self):
        return r"Janeus subscriber '{}' ({})".format(self.janeus_name, str(self.member_id))

    @transaction.atomic
    def update_janeus_newsletters(self):
        res = Janeus().by_lidnummer(self.member_id)
        if res is None:
            self.groups = []  # whoops...
        dn, attrs = res
        self.groups = set(Janeus().groups_of_dn(dn))
        auto_membership = []
        for s in MailingList.objects.exclude(janeus_groups_auto=''):
            auto = set([x.strip() for x in re.split(',|\n', s.janeus_groups_auto)])
            if len(auto.intersection(self.groups)):
                auto_membership.append(s)
        self.subscriptions.add(*list(auto_membership))
        for s in self.subscriptions.exclude(janeus_groups_required=''):
            req = set([x.strip() for x in re.split(',|\n', s.janeus_groups_required) if len(x.strip())])
            if len(req.intersection(self.groups)) == 0 and s not in auto_membership:
                self.subscriptions.remove(s)
        self.subscriptions.add(*auto_membership)
        self.save()

    def get_auto_newsletters(self):
        res = Janeus().by_lidnummer(self.member_id)
        if res is None:
            self.groups = []  # whoops...
        dn, attrs = res
        self.groups = set(Janeus().groups_of_dn(dn))
        auto_membership = []
        for s in MailingList.objects.exclude(janeus_groups_auto=''):
            auto = set([x.strip() for x in re.split(',|\n', s.janeus_groups_auto) if len(x.strip())])
            if len(auto.intersection(self.groups)):
                auto_membership.append(s)
        return auto_membership

    def get_allowed_newsletters(self):
        res = Janeus().by_lidnummer(self.member_id)
        if res is None:
            self.groups = []  # whoops...
        dn, attrs = res
        self.groups = set(Janeus().groups_of_dn(dn))
        allowed = []
        for s in MailingList.objects.order_by('name'):
            auto = set([x.strip() for x in re.split(',|\n', s.janeus_groups_auto) if len(x.strip())])
            req = set([x.strip() for x in re.split(',|\n', s.janeus_groups_required) if len(x.strip())])
            if len(auto.intersection(self.groups)):
                allowed.append(s)
            elif len(req) == 0:
                allowed.append(s)
            elif len(req.intersection(self.groups)):
                allowed.append(s)
        return allowed


class EmailSubscriber(Subscriber):
    email = models.EmailField(max_length=254, unique=True)

    def __unicode__(self):
        return r"Email subscriber '{}'".format(self.email)

    @transaction.atomic
    def remove_secret_newsletters(self):
        for s in self.subscriptions.exclude(janeus_groups_required=''):
            self.subscriptions.remove(s)
        s.save()


def create_expiration_date():
    return timezone.now() + timedelta(days=1)


class EmailSubscriberAccessToken(models.Model):
    token = models.CharField(max_length=255)
    subscriber = models.OneToOneField(EmailSubscriber, related_name='token')
    expiration_date = models.DateTimeField(default=create_expiration_date)

    def get_url(self):
        return reverse('subscriptions_email', kwargs={'subscriber': self.pk, 'token': self.token})

    def __unicode__(self):
        return r"Access token for {}".format(str(self.subscriber))


class JaneusSubscriberAccessToken(models.Model):
    token = models.CharField(max_length=255)
    subscriber = models.OneToOneField(JaneusSubscriber, related_name='token')
    expiration_date = models.DateTimeField(default=create_expiration_date)

    def get_url(self):
        return reverse('subscriptions_janeus', kwargs={'subscriber': self.pk, 'token': self.token})

    def __unicode__(self):
        return r"Access token for {}".format(str(self.subscriber))


class MailingList(models.Model):
    label = models.SlugField(unique=True)
    name = models.CharField(max_length=255)
    janeus_groups_auto = models.TextField(blank=True, default='')
    janeus_groups_required = models.TextField(blank=True, default='')

    def __unicode__(self):
        return r"{}".format(self.name)
