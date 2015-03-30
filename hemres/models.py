from __future__ import unicode_literals
from future.builtins import str
from datetime import timedelta
from django.db import models, transaction
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from janeus import Janeus
import re

from .utils import HashFileField


@python_2_unicode_compatible
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

    def __str__(self):
        return self.cast().__str__()


@python_2_unicode_compatible
class JaneusSubscriber(Subscriber):
    member_id = models.IntegerField(unique=True)
    janeus_name = models.CharField(max_length=255, blank=True, default='')

    def __str__(self):
        return "Janeus subscriber '{}' ({})".format(self.janeus_name, str(self.member_id))

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


@python_2_unicode_compatible
class EmailSubscriber(Subscriber):
    email = models.EmailField(max_length=254, unique=True)

    def __str__(self):
        return "Email subscriber '{}'".format(self.email)

    @transaction.atomic
    def remove_secret_newsletters(self):
        for s in self.subscriptions.exclude(janeus_groups_required=''):
            self.subscriptions.remove(s)
        s.save()


def create_expiration_date():
    return timezone.now() + timedelta(days=1)


@python_2_unicode_compatible
class EmailSubscriberAccessToken(models.Model):
    token = models.CharField(max_length=255)
    subscriber = models.OneToOneField(EmailSubscriber, related_name='token')
    expiration_date = models.DateTimeField(default=create_expiration_date)

    def get_absolute_url(self):
        return reverse('subscriptions_email', kwargs={'subscriber': self.pk, 'token': self.token})

    def __str__(self):
        return "Access token for {}".format(str(self.subscriber))


@python_2_unicode_compatible
class JaneusSubscriberAccessToken(models.Model):
    token = models.CharField(max_length=255)
    subscriber = models.OneToOneField(JaneusSubscriber, related_name='token')
    expiration_date = models.DateTimeField(default=create_expiration_date)

    def get_absolute_url(self):
        return reverse('subscriptions_janeus', kwargs={'subscriber': self.pk, 'token': self.token})

    def __str__(self):
        return "Access token for {}".format(str(self.subscriber))


@python_2_unicode_compatible
class MailingList(models.Model):
    label = models.SlugField(unique=True)
    name = models.CharField(max_length=255)
    janeus_groups_auto = models.TextField(blank=True, default='')
    janeus_groups_required = models.TextField(blank=True, default='')

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class NewsletterFile(models.Model):
    # as foreign key in M2M files form NewsletterTemplate, and NewsletterAttachment

    file = HashFileField(upload_to='hemres/files/{}')
    filename = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.filename


@python_2_unicode_compatible
class NewsletterTemplate(models.Model):
    title = models.CharField(max_length=255)
    template = models.TextField()
    files = models.ManyToManyField(NewsletterFile, through='TemplateAttachment')

    # template will be copied to Newsletter
    # each file in files will be a new NewsletterAttachment

    def __str__(self):
        return self.title

    @transaction.atomic
    def create_newsletter(self, subject):
        a = Newsletter(template=self.template, subject=subject)
        a.save()
        for f in self.templateattachment_set.all():
            at = NewsletterAttachment(newsletter=a, file=f.file, attach_to_email=f.attach_to_email, content_id=f.content_id)
            at.save()
        return a


class TemplateAttachment(models.Model):
    template = models.ForeignKey(NewsletterTemplate)
    file = models.ForeignKey(NewsletterFile)
    attach_to_email = models.BooleanField(default=True)
    content_id = models.CharField(max_length=255)


@python_2_unicode_compatible
class Newsletter(models.Model):
    template = models.TextField()  # copied from NewsletterTemplate
    files = models.ManyToManyField(NewsletterFile, through='NewsletterAttachment')  # initial copied from NewsletterTemplate, attach by default
    subject = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    date = models.DateTimeField(auto_now_add=True, blank=True)
    public = models.BooleanField(default=True)

    def __str__(self):
        return self.subject


class NewsletterAttachment(models.Model):
    newsletter = models.ForeignKey(Newsletter)
    file = models.ForeignKey(NewsletterFile)
    attach_to_email = models.BooleanField(default=True)
    content_id = models.CharField(max_length=255)
