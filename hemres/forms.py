from django.forms import Form, EmailField, ModelForm, ModelMultipleChoiceField
from django.forms.widgets import CheckboxSelectMultiple
from captcha.fields import ReCaptchaField

from . import models


class SubscriptionEmailForm(Form):
    email = EmailField(max_length=254, label='Emailadres:')


class SubscriptionEmailRecaptchaForm(SubscriptionEmailForm):
    captcha = ReCaptchaField()


class JaneusSubscriberForm(ModelForm):
    subscriptions = ModelMultipleChoiceField(
        queryset=models.MailingList.objects.order_by('name'),
        required=False,
        widget=CheckboxSelectMultiple,
        label='Nieuwsbrieven')

    class Meta:
        model = models.JaneusSubscriber
        fields = ('name', 'subscriptions')

    def __init__(self, *args, **kwargs):
        super(JaneusSubscriberForm, self).__init__(*args, **kwargs)
        self.fields['name'].label = "Naam"


class EmailSubscriberForm(ModelForm):
    subscriptions = ModelMultipleChoiceField(
        queryset=models.MailingList.objects.filter(janeus_groups_required='').order_by('name'),
        required=False,
        widget=CheckboxSelectMultiple,
        label='Nieuwsbrieven')

    class Meta:
        model = models.EmailSubscriber
        fields = ('name', 'subscriptions')

    def __init__(self, *args, **kwargs):
        super(EmailSubscriberForm, self).__init__(*args, **kwargs)
        self.fields['name'].label = "Naam"
