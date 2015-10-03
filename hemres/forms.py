from __future__ import unicode_literals
from future.builtins import super
from future.builtins import str
from future.builtins import int
from builtins import object
from django.forms import Form, EmailField, ModelForm, ModelMultipleChoiceField, ModelChoiceField
from django.forms.widgets import CheckboxSelectMultiple, CheckboxFieldRenderer, CheckboxChoiceInput, RadioSelect

from . import models


class SubscriptionEmailForm(Form):
    email = EmailField(max_length=254, label='Emailadres:')


class SubscriptionEmailRecaptchaForm(SubscriptionEmailForm):
    def __init__(self, *args, **kwargs):
        super(SubscriptionEmailRecaptchaForm, self).__init__(*args, **kwargs)
        from captcha.fields import ReCaptchaField
        self.captcha = ReCaptchaField()


class CheckboxChoiceInputDisabled(CheckboxChoiceInput):
    def __init__(self, *args, **kwargs):
        disabledset = kwargs.pop('disabledset', None)
        super(CheckboxChoiceInputDisabled, self).__init__(*args, **kwargs)
        self.disabledset = set([str(x.pk) for x in disabledset])
        if self.choice_value in self.disabledset:
            self.attrs['disabled'] = 'disabled'


class CheckboxFieldDisabledRenderer(CheckboxFieldRenderer):
    def choice_input_class(self, *args, **kwargs):
        kwargs = dict(kwargs, disabledset=self.disabledset)
        return CheckboxChoiceInputDisabled(*args, **kwargs)


class CheckboxSelectMultipleDisabled(CheckboxSelectMultiple):
    def renderer(self, *args, **kwargs):
        instance = CheckboxFieldDisabledRenderer(*args, **kwargs)
        instance.disabledset = self.disabledset
        return instance


class ModelMultipleChoiceFieldDisabled(ModelMultipleChoiceField):
    widget = CheckboxSelectMultipleDisabled

    def __init__(self, disabledset=[], *args, **kwargs):
        super(ModelMultipleChoiceFieldDisabled, self).__init__(*args, **kwargs)
        self.widget.disabledset = disabledset


class JaneusSubscriberForm(ModelForm):
    subscriptions = ModelMultipleChoiceFieldDisabled(
        queryset=models.MailingList.objects.order_by('name'),
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


class CreateNewsletterForm(Form):
    template = ModelChoiceField(
        queryset=models.NewsletterTemplate.objects.filter().order_by('title'),
        required=True,
        widget=RadioSelect,
        empty_label=None,
        label='Templates')


class TestEmailForm(Form):
    email = EmailField(max_length=254, label='Emailadres:')


class PrepareSendingForm(Form):
    lists = ModelChoiceField(
        queryset=models.MailingList.objects.filter().order_by('name'),
        required=True,
        widget=RadioSelect,
        empty_label=None,
        label='Nieuwsbrieven')
