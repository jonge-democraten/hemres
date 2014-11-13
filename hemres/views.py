from django.conf import settings
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import Http404
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.generic.edit import UpdateView
import hashlib
import os

from janeus import Janeus

from . import models
from . import forms


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
            email_to_send = compose_mail(email)
            if getattr(settings, 'SKIP_EMAIL', False):
                return render(request, 'hemres/subscriptions_fakemail.html', {'email': email_to_send})
            subject = 'Jonge Democraten Nieuwsbrieven'
            from_email = 'noreply@jongedemocraten.nl'
            msg = EmailMessage(subject, email_to_send, from_email=from_email, to=[email])
            msg.send()

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


@transaction.atomic
def compose_mail(emailaddress):
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

    context = {'janeus_subscriber_tokens': janeus_subscribers_tokens,
               'email_subscriber_tokens': email_subscribers_tokens,
               'name': name}
    return render_to_string('hemres/email.html', context)
