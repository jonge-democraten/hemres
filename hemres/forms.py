from django.contrib.sites.models import Site
from django.forms import Form, EmailField, ModelForm, ModelMultipleChoiceField, ModelChoiceField, CharField
from django.forms.widgets import CheckboxSelectMultiple, RadioSelect
from django.utils.safestring import mark_safe
import logging
import re

from . import models


logger = logging.getLogger(__name__)


try:
    # Determine if we actually have (Mezzanine) fullcalendar
    from fullcalendar.models import Occurrence
    has_fullcalendar = True
except:
    has_fullcalendar = False


def get_upcoming_events():
    """
    Obtain a QuerySet with upcoming events, or a dummy
    empty QuerySet if (Mezzanine) fullcalendar is not installed.
    """
    try:
        from fullcalendar.models import Occurrence
        return Occurrence.objects.upcoming().order_by('start_time')
    except:
        # use a dummy to get an empty QuerySet
        return models.Subscriber.objects.none()


class SubscriptionEmailForm(Form):
    email = EmailField(max_length=254, label='Emailadres:')


class SubscriptionEmailRecaptchaForm(SubscriptionEmailForm):
    def __init__(self, *args, **kwargs):
        super(SubscriptionEmailRecaptchaForm, self).__init__(*args, **kwargs)
        from captcha.fields import ReCaptchaField
        self.captcha = ReCaptchaField()


class EventField(ModelMultipleChoiceField):
    def __deepcopy__(self, memo):
        result = super(EventField, self).__deepcopy__(memo)
        result.queryset = get_upcoming_events()
        result.populate_choices()
        return result

    def populate_choices(self):
        # this is just a hack in the case we do not have mezzanine
        if not has_fullcalendar:
            return
        # get all sites in occurrences
        occ = tuple(self.queryset.select_related('site'))
        sites = list(Site.objects.filter(occurrence__in=occ).distinct().order_by('name'))
        # fill choices
        choices = []
        for site in sites:
            # get occurrences for this site and convert to (value, label)
            occurrences = (tuple((self.prepare_value(o), self.label_from_instance(o))) for o in occ if o.site==site)
            # add to choices
            choices.append((site.name, tuple(occurrences)))
        self.choices = choices


class JaneusSubscriberForm(ModelForm):
    subscriptions = ModelMultipleChoiceField(
        queryset=models.MailingList.objects.order_by('name'),
        widget=CheckboxSelectMultiple,
        required=False,
        label='Nieuwsbrieven')

    class Meta(object):
        model = models.JaneusSubscriber
        fields = ('name', 'subscriptions')

    def __init__(self, *args, **kwargs):
        super(JaneusSubscriberForm, self).__init__(*args, **kwargs)
        self.fields['name'].label = "Naam"
        allowed = self.instance.get_allowed_newsletters()
        self.fields['subscriptions'].queryset = models.MailingList.objects.filter(pk__in=[int(o.pk) for o in allowed]).order_by('name')

    def save(self, *args, **kwargs):
        result = super(JaneusSubscriberForm, self).save(*args, **kwargs)
        result.update_janeus_newsletters()
        return result


class EmailSubscriberForm(ModelForm):
    subscriptions = ModelMultipleChoiceField(
        queryset=models.MailingList.objects.filter(janeus_groups_required='').order_by('name'),
        required=False,
        widget=CheckboxSelectMultiple,
        label='Nieuwsbrieven')

    class Meta(object):
        model = models.EmailSubscriber
        fields = ('name', 'subscriptions')

    def __init__(self, *args, **kwargs):
        super(EmailSubscriberForm, self).__init__(*args, **kwargs)
        self.fields['name'].label = "Naam"

    def save(self, *args, **kwargs):
        result = super(EmailSubscriberForm, self).save(*args, **kwargs)
        result.remove_restricted_newsletters()
        return result


class CreateNewsletterForm(ModelForm):
    subject = CharField(required=True, label='Onderwerp')

    template = ModelChoiceField(
        queryset=models.NewsletterTemplate.objects.filter().order_by('title'),
        required=True,
        widget=RadioSelect,
        empty_label=None,
        label='Template')

    events = EventField(
        queryset=get_upcoming_events(),
        required=False,
        widget=CheckboxSelectMultiple,
        label='Events')

    class Meta(object):
        model = models.Newsletter
        fields = ['subject','template','events']

    def __init__(self, *args, **kwargs):
        super(CreateNewsletterForm, self).__init__(*args, **kwargs)
        self.fields['events'].widget.attrs['class'] = 'checkboxlist'


class TestEmailForm(Form):
    email = EmailField(max_length=254, label='Emailadres:')


class PrepareSendingForm(Form):
    lists = ModelChoiceField(
        queryset=models.MailingList.objects.filter().order_by('name'),
        required=True,
        widget=RadioSelect,
        empty_label=None,
        label='Nieuwsbrieven')
