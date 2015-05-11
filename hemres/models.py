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
from email import encoders
from email.mime.base import MIMEBase
from janeus import Janeus
import re
import bleach
import html2text


from .utils import HashFileField


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
        if not hasattr(settings, 'JANEUS_SERVER'):
            return []
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
        if not hasattr(settings, 'JANEUS_SERVER'):
            return MailingList.objects.all()
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
    def create_newsletter(self, subject, owner=None):
        a = Newsletter(template=self.template, subject=subject, owner=owner)
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
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        permissions = (
            ("change_all_newsletters", "Can change all newsletters"),
        )

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

        context['files'] = {}
        attached = []
        for f in self.newsletterattachment_set.all():
            context['files'][f.content_id] = f
            if f.attach_to_email:
                attached.append(f.file)

        if not embed and len(attached):
            # we are for browser!
            filelist_template = "<ul>{% for f in files %}<li><a href=\"{{f.file.url}}\">{{f.filename}}</a></li>{% endfor %}</ul>"
            filelist = Template(filelist_template).render(Context({'files': attached}))
            context['filelist'] = mark_safe(bleach.clean(filelist, tags=allowed_tags, attributes=allowed_attrs))
        else:
            context['filelist'] = ''

        context['subject'] = mark_safe(bleach.clean(self.subject, tags=allowed_tags, attributes=allowed_attrs))
        context['name'] = mark_safe(bleach.clean(name))
        context['naam'] = mark_safe(bleach.clean(name))

        # first render content
        # only allow tags "emailimage" and "emailfile"
        # replace src="{{blabla}}" by src="{% emailimage 'blabla' %}"
        # replace href="{{blabla}}" by href="{% emailfile 'blabla' %}"
        # then use bleach to restrict HTML

        # in the template, the following context variables are defined:
        # - render_mail: Boolean, True if rendering for mail, False if for browser
        # - subscriptions_url: URL for managing subscriptions
        # - subject: subject as set in Newsletter object
        # - name: name of the recipient (as set in EmailSubscriber or in LDAP)
        # - content: content after rendering
        # - filelist: unordered list of attached files (all files with attach_to_email set), only for in browser

        header = "{% load hemres_email %}{% limit_filters %}{% limit_tags emailimage_media emailimage_static emailimage emailfile %}"
        template = header + self.content
        template = re.sub('src="\\{\\{\s*(\S+)\s*\\}\\}"', 'src="{% emailimage \'\\1\' %}"', template)
        template = re.sub('href="\\{\\{\s*(\S+)\s*\\}\\}"', 'href="{% emailfile \'\\1\' %}"', template)
        context['content'] = Template(template).render(Context(context))
        context['content'] = mark_safe(bleach.clean(context['content'], tags=allowed_tags, attributes=allowed_attrs))

        # then render whole mail
        header = "{% load hemres_email %}{% limit_filters %}{% limit_tags emailimage_media emailimage_static emailimage emailfile if endif %}"
        result = Template(header + self.template).render(Context(context))

        from inlinestyler.utils import inline_css
        result = inline_css(result)

        # and add any unreferenced attachments
        attachments = [mime for mime, cid in list(context['attachments'].values())]
        for f in self.newsletterattachment_set.all():
            if f.attach_to_email and f.content_id not in context['attachments']:
                path = f.file.file.path
                with open(path, 'rb') as fh:
                    mime = MIMEBase('application', 'octet-stream')
                    mime.set_payload(fh.read())
                    encoders.encode_base64(mime)
                    mime.add_header('Content-Disposition', 'attachment', filename=f.file.filename)
                    attachments.append(mime)

        return result, attachments

    @transaction.atomic
    def prepare_sending(self, target_list, subscriptions_url):
        a = NewsletterToList(newsletter=self, target_list=target_list, subscriptions_url=subscriptions_url)
        a.save()
        return a


class NewsletterAttachment(models.Model):
    newsletter = models.ForeignKey(Newsletter)
    file = models.ForeignKey(NewsletterFile)
    attach_to_email = models.BooleanField(default=True)
    content_id = models.CharField(max_length=255)


@python_2_unicode_compatible
class NewsletterToList(models.Model):
    # To send newsletter to mailing list. After sending, the field
    # sent will be set to True and the date to the moment that the
    # NewsletterToSubscriber instances were created.
    newsletter = models.ForeignKey(Newsletter, null=False)
    target_list = models.ForeignKey(MailingList, null=False)
    subscriptions_url = models.CharField(max_length=255, blank=True)
    sent = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True, blank=True)

    def __str__(self):
        return "'{}' to '{}'".format(self.newsletter, self.target_list)

    @transaction.atomic
    def process(self):
        if self.sent:
            return  # only send once

        # get auto and required Janeus groups
        auto = set([x.strip() for x in re.split(',|\n', self.target_list.janeus_groups_auto) if len(x.strip())])
        req = set([x.strip() for x in re.split(',|\n', self.target_list.janeus_groups_required) if len(x.strip())])

        # First send it to all automatic subscribers
        autosubs = {}
        for group in auto:
            if hasattr(settings, 'JANEUS_SERVER'):
                for dn, attrs in Janeus().members_of_group(group):
                    autosubs[attrs['cn'][0]] = (attrs['sn'][0], attrs['mail'][0])
        for sub in autosubs.values():
            a = NewsletterToSubscriber(newsletter=self.newsletter,
                                       subscriptions_url=self.subscriptions_url,
                                       target_list=self.target_list,
                                       target_name=sub[0],
                                       target_email=sub[1])
            a.save()

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
                    if str(sub.member_id) in autosubs:
                        send_it = False  # already sent
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
