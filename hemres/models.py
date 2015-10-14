from __future__ import unicode_literals
from future.builtins import str
from datetime import timedelta
from django.db import models, transaction
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.template import Context, Template
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.safestring import mark_safe
from janeus import Janeus
from mezzanine.core.models import SiteRelated
import re
import bleach
import html2text


# bleach is annoying with CSS handling. Just break it.
bleach.BleachSanitizer.sanitize_css = lambda self, style: style


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
        if not hasattr(settings, 'JANEUS_SERVER'):
            return
        res = Janeus().by_lidnummer(self.member_id)
        if res is None:
            self.groups = []  # whoops...
        dn, attrs = res
        self.groups = set(Janeus().groups_of_dn(dn))
        for s in self.subscriptions.exclude(janeus_groups_required=''):
            req = set([x.strip() for x in re.split(',|\n', s.janeus_groups_required) if len(x.strip())])
            if len(req.intersection(self.groups)) == 0:
                self.subscriptions.remove(s)
        self.save()

    def get_allowed_newsletters(self):
        if not hasattr(settings, 'JANEUS_SERVER'):
            return MailingList.objects.all()
        res = Janeus().by_lidnummer(self.member_id)
        if res is None:
            self.groups = []  # whoops...
        dn, attrs = res
        self.groups = set(Janeus().groups_of_dn(dn))
        allowed = []
        for s in MailingList.objects.order_by('name'):
            req = set([x.strip() for x in re.split(',|\n', s.janeus_groups_required) if len(x.strip())])
            if len(req) == 0 or len(req.intersection(self.groups)):
                allowed.append(s)
        return allowed


@python_2_unicode_compatible
class EmailSubscriber(Subscriber):
    email = models.EmailField(max_length=254, unique=True)

    def __str__(self):
        return "Email subscriber '{}'".format(self.email)

    @transaction.atomic
    def remove_restricted_newsletters(self):
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
    janeus_groups_required = models.TextField(blank=True, default='')

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class NewsletterTemplate(models.Model):
    title = models.CharField(max_length=255)
    template = models.TextField()

    # template will be copied to Newsletter

    def __str__(self):
        return self.title

    @transaction.atomic
    def create_newsletter(self, subject):
        a = Newsletter(template=self.template, subject=subject)
        a.save()
        return a


@python_2_unicode_compatible
class Newsletter(SiteRelated):
    template = models.TextField()  # copied from NewsletterTemplate
    subject = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    date = models.DateTimeField(default=timezone.now, blank=True)
    public = models.BooleanField(default=True)

    def __str__(self):
        return self.subject

    def render(self, name, embed, subscriptions_url):
        # Render email, set embed=True for sending mail, or embed=False for viewing in browser

        # Notes:
        # absolute_uri = '%s://%s' % (request.scheme, request.get_host())
        # subscriptions_url = request.build_absolute_uri(reverse('hemres.views.view_home'))

        context = {}
        context['render_mail'] = embed
        context['subscriptions_url'] = subscriptions_url
        context['attachments'] = {}  # receives MIME attachments

        allowed_tags = ['a', 'b', 'blockquote', 'caption', 'code', 'em', 'h1', 'h2', 'h3', 'i', 'img', 'strong', 'ul', 'ol', 'li', 'p', 'br', 'span', 'table', 'tbody', 'tr', 'td', 'thead', 'div', 'span']
        allowed_attrs = {
            '*': ['class', 'style'],
            'a': ['href', 'target'],
            'img': ['src', 'alt', 'width', 'height'],
            'table': ['border', 'align', 'cellpadding', 'cellspacing'],
        }

        # hack to allow cid as protocol for images
        if 'cid' not in bleach.BleachSanitizer.allowed_protocols:
            bleach.BleachSanitizer.allowed_protocols += ["cid"]

        context['subject'] = mark_safe(bleach.clean(self.subject, tags=allowed_tags, attributes=allowed_attrs))
        context['name'] = mark_safe(bleach.clean(name))
        context['naam'] = mark_safe(bleach.clean(name))

        # first render content then use bleach to restrict HTML

        # in the template, the following context variables are defined:
        # - render_mail: Boolean, True if rendering for mail, False if for browser
        # - subscriptions_url: URL for managing subscriptions
        # - subject: subject as set in Newsletter object
        # - name: name of the recipient (as set in EmailSubscriber or in LDAP)
        # - content: content after rendering

        header = "{% load hemres_email %}{% limit_filters %}{% limit_tags emailimage_media emailimage_static %}"
        template = header + self.content
        template = re.sub('src="{}([^"]*)"'.format(settings.MEDIA_URL), 'src="{% emailimage_media \'\\1\' %}"', template)
        template = re.sub('src="{}([^"]*)"'.format(settings.STATIC_URL), 'src="{% emailimage_static \'\\1\' %}"', template)
        context['content'] = Template(template).render(Context(context))
        context['content'] = mark_safe(bleach.clean(context['content'], tags=allowed_tags, attributes=allowed_attrs))

        # then render whole mail
        header = "{% load hemres_email %}{% limit_filters %}{% limit_tags emailimage_media emailimage_static if endif %}"
        template = header + self.template
        template = re.sub('src="{}([^"]*)"'.format(settings.MEDIA_URL), 'src="{% emailimage_media \'\\1\' %}"', template)
        template = re.sub('src="{}([^"]*)"'.format(settings.STATIC_URL), 'src="{% emailimage_static \'\\1\' %}"', template)
        result = Template(template).render(Context(context))

        from inlinestyler.utils import inline_css
        from lxml.etree import XMLSyntaxError
        try:
            result = inline_css(result)
        except XMLSyntaxError:
            pass  # bad luck

        # and return the result and all attachments (images)
        attachments = [mime for mime, cid in list(context['attachments'].values())]
        return result, attachments

    @transaction.atomic
    def prepare_sending(self, target_list, subscriptions_url):
        a = NewsletterToList(newsletter=self, target_list=target_list, subscriptions_url=subscriptions_url)
        a.save()
        return a


@python_2_unicode_compatible
class NewsletterToList(models.Model):
    # To send newsletter to mailing list. After sending, the field
    # sent will be set to True and the date to the moment that the
    # NewsletterToSubscriber instances were created.
    newsletter = models.ForeignKey(Newsletter, null=False)
    target_list = models.ForeignKey(MailingList, null=False)
    subscriptions_url = models.CharField(max_length=255, blank=True)
    sent = models.BooleanField(default=False)
    date = models.DateTimeField(default=timezone.now, blank=True)

    def __str__(self):
        return "'{}' to '{}'".format(self.newsletter, self.target_list)

    @transaction.atomic
    def process(self):
        if self.sent:
            return  # only send once

        # get required Janeus groups
        req = set([x.strip() for x in re.split(',|\n', self.target_list.janeus_groups_required) if len(x.strip())])

        # Then send to all subscribers from database
        for sub in self.target_list.subscribers.all():
            sub = sub.cast()
            if type(sub) is EmailSubscriber and not len(req):
                a = NewsletterToSubscriber(newsletter=self.newsletter,
                                           subscriptions_url=self.subscriptions_url,
                                           target_list=self.target_list,
                                           target_name=sub.name,
                                           target_email=sub.email)
                a.save()
            elif type(sub) is JaneusSubscriber:
                if hasattr(settings, 'JANEUS_SERVER'):
                    res = Janeus().by_lidnummer(sub.member_id)
                else:
                    res = None
                if res is not None:
                    dn, attrs = res
                    mail, name = attrs['mail'][0], attrs['sn'][0]
                    send_it = True
                    if len(req):
                        groups = set(Janeus().groups_of_dn(dn))
                        send_it = len(req.intersection(groups)) > 0
                    if send_it:
                        a = NewsletterToSubscriber(newsletter=self.newsletter,
                                                   subscriptions_url=self.subscriptions_url,
                                                   target_list=self.target_list,
                                                   target_name=name,
                                                   target_email=mail)
                        a.save()
        self.sent = True
        self.date = timezone.now()
        self.save()


@python_2_unicode_compatible
class NewsletterToSubscriber(models.Model):
    # After sending, instance is deleted.
    newsletter = models.ForeignKey(Newsletter, null=False)
    subscriptions_url = models.CharField(max_length=255, blank=True)
    target_list = models.ForeignKey(MailingList, null=False)
    target_name = models.CharField(max_length=255, blank=True)
    target_email = models.EmailField(max_length=254)

    def __str__(self):
        return "'[{}] {}' to '{}'".format(self.target_list, self.newsletter, self.target_email)

    def send_mail(self):
        subject = "[{}] {}".format(self.target_list.name, self.newsletter.subject)
        html_content, attachments = self.newsletter.render(self.target_name, True, self.subscriptions_url)
        h = html2text.HTML2Text()
        h.ignore_images = True
        text_content = h.handle(html_content)
        from_email = getattr(settings, 'HEMRES_FROM_ADDRESS', 'noreply@jongedemocraten.nl')

        msg = EmailMultiAlternatives(subject=subject, body=text_content, from_email=from_email, to=[self.target_email])
        msg.attach_alternative(html_content, "text/html")
        msg.mixed_subtype = 'related'
        for a in attachments:
            msg.attach(a)

        if not getattr(settings, 'HEMRES_DONT_EMAIL', False):
            msg.send()
        self.delete()
