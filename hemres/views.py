from __future__ import unicode_literals
from future.builtins import int
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.contrib.contenttypes.models import ContentType
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.generic.edit import UpdateView
from html.parser import HTMLParser
import logging
import hashlib
import os
import html2text

from janeus import Janeus

from . import models
from . import forms


try:
    from mezzanine.utils.sites import current_site_id
except:
    from .siterelated import current_site_id


logger = logging.getLogger(__name__)


def view_home(request):
    if getattr(settings, 'RECAPTCHA', False):
        if request.method == 'POST':
            form = forms.SubscriptionEmailRecaptchaForm(request.POST)
        else:
            form = forms.SubscriptionEmailRecaptchaForm()
    else:
        if request.method == 'POST':
            form = forms.SubscriptionEmailForm(request.POST)
        else:
            form = forms.SubscriptionEmailForm()

    if request.method == 'POST':
        if form.is_valid():
            email = form.cleaned_data['email']
            if getattr(settings, 'HEMRES_DONT_EMAIL', False):
                email_to_send, attachments = compose_mail(email, False, request=request)
                return HttpResponse(email_to_send, content_type='text/html')
            else:
                send_subscriber_mail(email, request=request)
                return render(request, 'hemres/subscriptions_emailsent.html', {'email': email})

    return render(request, 'hemres/home.html', {'form': form})


def subscriptions_done(request):
    return render(request, 'hemres/subscriptions_manage_done.html')


class ManageEmailSubscriptions(UpdateView):
    model = models.EmailSubscriber
    form_class = forms.EmailSubscriberForm
    template_name = 'hemres/subscriptions_manage_email.html'

    def get_success_url(self):
        return reverse(subscriptions_done)

    def get_object(self, *args, **kwargs):
        subscriber = self.kwargs['subscriber']
        token = self.kwargs['token']
        accesstoken = models.EmailSubscriberAccessToken.objects.filter(pk=int(subscriber)).filter(token=token).filter(expiration_date__gt=timezone.now())
        # check expire
        if len(accesstoken) == 0:
            raise Http404()
        return accesstoken[0].subscriber


class ManageJaneusSubscriptions(UpdateView):
    model = models.JaneusSubscriber
    form_class = forms.JaneusSubscriberForm
    template_name = 'hemres/subscriptions_manage_janeus.html'

    def get_success_url(self):
        return reverse(subscriptions_done)

    def get_object(self, *args, **kwargs):
        subscriber = self.kwargs['subscriber']
        token = self.kwargs['token']
        accesstoken = models.JaneusSubscriberAccessToken.objects.filter(pk=int(subscriber)).filter(token=token).filter(expiration_date__gt=timezone.now())
        # check expire
        if len(accesstoken) == 0:
            raise Http404()
        accesstoken[0].subscriber.update_janeus_newsletters()
        return accesstoken[0].subscriber


def make_janeus_subscriber(members):
    member_id, name = members
    s = models.JaneusSubscriber.objects.filter(member_id=int(member_id)).select_related('token')
    if len(s) == 0:
        s = [models.JaneusSubscriber(member_id=int(member_id), janeus_name=name, name=name)]
        s[0].save()
    return s[0]


def create_fresh_janeus_token(subscriber):
    if hasattr(subscriber, 'token'):
        subscriber.token.delete()
    token = hashlib.sha256(os.urandom(64)).hexdigest()
    t = models.JaneusSubscriberAccessToken(subscriber=subscriber, token=token)
    t.save()
    return t


def create_fresh_email_token(subscriber):
    if hasattr(subscriber, 'token'):
        subscriber.token.delete()
    token = hashlib.sha256(os.urandom(64)).hexdigest()
    t = models.EmailSubscriberAccessToken(subscriber=subscriber, token=token)
    t.save()
    return t


def send_subscriber_mail(emailaddress, request):
    # knowledge of 'request' necessary to compose mail
    html_content, attachments = compose_mail(emailaddress, True, request=request)
    h = html2text.HTML2Text()
    h.ignore_images = True
    text_content = h.handle(html_content)

    subject = 'Jonge Democraten Nieuwsbrieven'
    from_email = getattr(settings, 'HEMRES_FROM_ADDRESS', 'noreply@jongedemocraten.nl')
    msg = EmailMultiAlternatives(subject=subject, body=text_content, from_email=from_email, to=[emailaddress])
    msg.attach_alternative(html_content, "text/html")
    msg.mixed_subtype = 'related'
    for a in attachments:
        msg.attach(a)
    msg.send()


@transaction.atomic
def compose_mail(emailaddress, embed, request):
    # find Janeus users
    if hasattr(settings, 'JANEUS_SERVER'):
        janeus_subscribers = [make_janeus_subscriber(s) for s in Janeus().lidnummers(emailaddress)]
    else:
        janeus_subscribers = []

    email_subscribers = models.EmailSubscriber.objects.filter(email=emailaddress).select_related('token')  # case sensitive!

    if len(janeus_subscribers) == 0 and len(email_subscribers) == 0:
        email_subscribers = [models.EmailSubscriber(name='', email=emailaddress)]
        email_subscribers[0].save()

    # create tokens
    janeus_subscribers_tokens = [create_fresh_janeus_token(s) for s in janeus_subscribers]
    email_subscribers_tokens = [create_fresh_email_token(s) for s in email_subscribers]

    if len(janeus_subscribers) == 1 and len(email_subscribers) == 0:
        name = janeus_subscribers[0].name
    else:
        name = None

    absolute_uri = '%s://%s' % (request.scheme, request.get_host())

    context = {'janeus_subscriber_tokens': janeus_subscribers_tokens,
               'email_subscriber_tokens': email_subscribers_tokens,
               'attachments': {},
               'render_mail': embed,
               'absolute_uri': absolute_uri,
               'name': name}
    result = render_to_string('hemres/subscriptions_email.html', context)
    return result, [mime for mime, cid in list(context['attachments'].values())]


@staff_member_required
@permission_required('hemres.add_newsletter')
def create_newsletter(request):
    if request.method == 'POST':
        form = forms.CreateNewsletterForm(request.POST)
    else:
        form = forms.CreateNewsletterForm()

    if request.method == 'POST' and form.is_valid():
        template = form.cleaned_data['template']
        subject = form.cleaned_data['subject']
        newsletter = template.create_newsletter(subject=subject)
        newsletter.content = "<h1>Beste {{naam}},</h1>"
        newsletter.content += "<p>Introductietekst</p>"
        if len(form.cleaned_data['events']):
            newsletter.content += "<h2 id='agenda'>Agenda</h2>"
        current_site = current_site_id()
        for o in form.cleaned_data['events']:
            start = timezone.localtime(o.start_time)
            end = timezone.localtime(o.end_time)
            duration = start.strftime('%A, %d %B %Y %H:%M')

            if (start.day == end.day and start.month == end.month and start.year == end.year):
                duration += ' - {:%H:%M}'.format(end)
            else:
                duration += ' - {:%A, %d %B %Y %H:%M}'.format(end)

            protocol = "http"

            # Set protocol to https if we have mezzanine and mezzanine has SSL_ENABLED set
            try:
                from mezzanine.conf import settings as msettings
                if getattr(msettings, 'SSL_ENABLED', False):
                    protocol = "https"
            except:
                pass

            if o.event.site.id != current_site:
                tag = "<strong>[{}]</strong> ".format(o.event.site.name)
            else:
                tag = ""

            newsletter.content += '<h3 class="agendaitem">{}<a href="{}://{}{}">{}</a></h3>'.format(tag, protocol, o.event.site.domain, o.get_absolute_url(), o.title)
            newsletter.content += "<p>"
            newsletter.content += "<strong>Wanneer</strong>: {}<br/>".format(duration)
            newsletter.content += "<strong>Waar</strong>: {}<br/>".format(o.location)
            newsletter.content += "{}".format(o.event.description)
            newsletter.content += "</p>"
        newsletter.save()
        content_type = ContentType.objects.get_for_model(newsletter.__class__)
        return redirect(reverse('admin:%s_%s_change' % (content_type.app_label, content_type.model), args=(newsletter.id,)))

    return render(request, 'hemres/create_newsletter.html', {'form': form})


def view_newsletter(request, newsletter_pk):
    if request.user.is_active and request.user.is_staff:
        newsletter = get_object_or_404(models.Newsletter, pk=newsletter_pk)
    else:
        # all newsletters SENT TO A LIST at most a year ago
        yearago = datetime.now() - timedelta(days=365)
        newsletter = get_object_or_404(models.Newsletter.objects.filter(public=True).filter(newslettertolist__date__gt=yearago), pk=newsletter_pk)
    subscriptions_url = request.build_absolute_uri(reverse(view_home))
    email, attachments = newsletter.render('Naam', False, subscriptions_url)
    return HttpResponse(email, content_type="text/html")


@staff_member_required
def test_newsletter(request, pk):
    newsletter = get_object_or_404(models.Newsletter, pk=pk)
    if request.method == 'POST':
        form = forms.TestEmailForm(request.POST)
    else:
        form = forms.TestEmailForm()

    if request.method == 'POST':
        if form.is_valid():
            address = form.cleaned_data['email']
            subscriptions_url = request.build_absolute_uri(reverse(view_home))
            subject = "[Test] {}".format(newsletter.subject)
            html_content, attachments = newsletter.render('', True, subscriptions_url)

            h = html2text.HTML2Text()
            h.ignore_images = True
            text_content = h.handle(html_content)
            from_email = getattr(settings, 'HEMRES_FROM_ADDRESS', 'noreply@jongedemocraten.nl')

            msg = EmailMultiAlternatives(subject=subject, body=text_content, from_email=from_email, to=[address])
            msg.attach_alternative(html_content, "text/html")
            msg.mixed_subtype = 'related'
            for a in attachments:
                msg.attach(a)

            if getattr(settings, 'HEMRES_DONT_EMAIL', False):
                return HttpResponse(msg.message().as_string(), content_type="message")
            else:
                msg.send()
                content_type = ContentType.objects.get_for_model(newsletter.__class__)
                return redirect(reverse('admin:%s_%s_changelist' % (content_type.app_label, content_type.model)))

    return render(request, 'hemres/test_newsletter.html', {'form': form, 'nieuwsbrief': str(newsletter)})


@staff_member_required
@permission_required('hemres.add_newsletter')
def prepare_sending(request, pk):
    newsletter = get_object_or_404(models.Newsletter, pk=pk)
    if request.method == 'POST':
        form = forms.PrepareSendingForm(request.POST)
    else:
        form = forms.PrepareSendingForm()

    if request.method == 'POST':
        if form.is_valid():
            subscriptions_url = request.build_absolute_uri(reverse(view_home))
            newsletter.prepare_sending(form.cleaned_data['lists'], subscriptions_url)
            content_type = ContentType.objects.get_for_model(newsletter.__class__)
            return redirect(reverse('admin:%s_%s_changelist' % (content_type.app_label, content_type.model)))

    return render(request, 'hemres/prepare_sending.html', {'form': form, 'nieuwsbrief': str(newsletter)})


@staff_member_required
@permission_required('hemres.add_newslettertosubscriber')
def process_sending(request, pk):
    newsletter_to_list = get_object_or_404(models.NewsletterToList, pk=pk)
    newsletter_to_list.process()
    content_type = ContentType.objects.get_for_model(models.NewsletterToList)
    return redirect(reverse('admin:%s_%s_changelist' % (content_type.app_label, content_type.model)))


def list_all(request):
    # Find all Newsletters of the current site
    site_id = current_site_id()
    if request.user.is_active and request.user.is_staff:
        letters = models.Newsletter.objects.filter(site__id__exact=site_id)
        letters = models.NewsletterToList.objects.order_by('-date').values('target_list__name', 'newsletter_id','newsletter__subject','date').filter(newsletter__in=letters)
    else:
        yearago = datetime.now() - timedelta(days=365)
        letters = models.Newsletter.objects.filter(site__id__exact=site_id)
        letters = models.NewsletterToList.objects.filter(target_list__janeus_groups_required='', newsletter__public=True,date__gt=yearago).order_by('-date').values('target_list__name', 'newsletter_id','newsletter__subject','date').filter(newsletter__in=letters)
    letters = [{'id': s['newsletter_id'], 'subject': '[{}] {}'.format(s['target_list__name'], s['newsletter__subject']), 'date': s['date']} for s in letters]
    return render(request, 'hemres/list.html', {'letters': letters})


class CSSExtract(HTMLParser):
    style = False
    data = ""

    def handle_starttag(self, tag, attrs):
        self.style = tag == "style"

    def handle_endtag(self, tag):
        self.style = False

    def handle_data(self, data):
        if self.style:
            self.data += data


@staff_member_required
def get_css(request, pk):
    newsletter = get_object_or_404(models.Newsletter, pk=pk)
    parser = CSSExtract()
    parser.feed(newsletter.template)
    return HttpResponse(parser.data, content_type="text/css")
