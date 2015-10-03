from __future__ import unicode_literals
from django.contrib import admin
from django.core.urlresolvers import reverse, reverse_lazy
from django.forms import ModelForm
from .models import JaneusSubscriber, EmailSubscriber, MailingList, Newsletter, NewsletterTemplate
from .models import NewsletterToList, NewsletterToSubscriber


class NewsletterAdminForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(NewsletterAdminForm, self).__init__(*args, **kwargs)

        # check if we have mezzanine
        try:
            from mezzanine.core.forms import TinyMceWidget
            self.fields['content'].widget = TinyMceWidget()
            self.fields['content'].widget.attrs['data-mce-conf'] = "{\"convert_urls\": false, \"relative_urls\": false, \"theme\": \"advanced\"}"
        except ImportError:
            try:
                from tinymce.widgets import TinyMCE
                self.fields['content'].widget = TinyMCE(attrs={'cols': 80, 'rows': 30}, mce_attrs={'theme': 'advanced', 'toolbar': 'undo redo bold italic', 'convert_urls': False, 'relative_urls': False})
            except ImportError:
                pass


class NewsletterAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'date', 'view_mail', 'test_mail', 'prepare_sending')
    form = NewsletterAdminForm

    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            (None, {
                'fields': ('subject', ),
                'description': 'Geef het onderwerp van de nieuwsbrief. Afhankelijk van de mailinglist waarnaar de nieuwsbrief verzonden wordt, komt de naam van de mailinglist er in blockhaken voor: "[Mailinglist] Onderwerp"',
            }),
            (None, {
                'fields': ('content', ),
                'description': 'Voor de inhoud van de nieuwsbrief kun je gebruik maken van <b>vet</b> en <i>cursief</i>, van genummerde en van ongenummerde lijsten, van hyperlinks en van Heading 1, Heading 2 en Heading 3.<br/>Gebruik Heading 1 voor de eerste regel van de nieuwsbrief (de titel), gebruik Heading 2 voor de kopjes tussen onderdelen van de nieuwsbrief, en gebruik Heading 3 voor een kopje binnen een onderdeel van de nieuwsbrief.<br/>Verder wordt de tekst {{naam}} vervangen door de naam van de geaddresseerde.'
            }),
            (None, {
                'fields': ['template', 'owner', 'public'],
            }),
        )
        if not request.user.has_perm('hemres.change_newslettertemplate'):
            fieldsets[2][1]['fields'].remove('template')
        if not request.user.has_perm('hemres.change_all_newsletters'):
            fieldsets[2][1]['fields'].remove('owner')
        return fieldsets

    def get_fields(self, request, obj=None):
        fields = super(NewsletterAdmin, self).get_fields(request, obj=obj)
        if not request.user.has_perm('hemres.change_newslettertemplate'):
            fields.remove('template')
        if not request.user.has_perm('hemres.change_all_newsletters'):
            fields.remove('owner')
        return fields

    def get_queryset(self, request):
        query = super(NewsletterAdmin, self).get_queryset(request)
        if request.user.is_superuser or request.user.has_perm('hemres.change_all_newsletters'):
            return query
        return query.filter(owner=request.user)

    def has_change_permission(self, request, obj=None):
        test = super(NewsletterAdmin, self).has_change_permission(request)
        if not test or obj is None or request.user.is_superuser or request.user.has_perm('hemres.change_all_newsletters'):
            return test
        return obj.owner == request.user

    def view_mail(self, obj):
        url = reverse('view_newsletter', args=[obj.pk])
        return '<a href="{}">View in browser</a>'.format(url)
    view_mail.allow_tags = True
    view_mail.short_description = 'View in browser'

    def test_mail(self, obj):
        url = reverse('test_newsletter', args=[obj.pk])
        return '<a href="{}">Send test mail</a>'.format(url)
    test_mail.allow_tags = True
    test_mail.short_description = 'Send test mail'

    def prepare_sending(self, obj):
        url = reverse('prepare_sending', args=[obj.pk])
        return '<a href="{}">Send to list</a>'.format(url)
    prepare_sending.allow_tags = True
    prepare_sending.short_description = 'Send to list'

    def get_urls(self):
        from django.conf.urls import url
        from django.views.generic import RedirectView
        info = self.model._meta.app_label, self.model._meta.model_name
        urlpatterns = [url(r'^create_newsletter$', RedirectView.as_view(url=reverse_lazy('create_newsletter')), name='%s_%s_add' % info)]
        return super(NewsletterAdmin, self).get_urls() + urlpatterns


class NewsletterToListAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'view_mail', 'test_mail', 'process_sending', 'date')

    def process_sending(self, obj):
        if obj.sent:
            return 'Already sent'
        else:
            return '<a href="%s">Send to emails</a>' % (reverse('process_sending', args=[obj.pk]),)
    process_sending.allow_tags = True
    process_sending.short_description = 'Send to emails'

    def view_mail(self, obj):
        url = 'http://{}{}'.format(obj.newsletter.site.domain,
                                   reverse('view_newsletter', args=[obj.newsletter.pk]))
        return '<a href="{}">View in browser</a>'.format(url)
    view_mail.allow_tags = True
    view_mail.short_description = 'View in browser'

    def test_mail(self, obj):
        url = 'http://{}{}'.format(obj.newsletter.site.domain,
                                   reverse('test_newsletter', args=[obj.newsletter.pk]))
        return '<a href="{}">Send test mail</a>'.format(url)
    test_mail.allow_tags = True
    test_mail.short_description = 'Send test mail'


def send_newsletters(modeladmin, request, queryset):
    for n in queryset:
        n.send_mail()
send_newsletters.short_description = "Send the newsletters"


class NewsletterToSubscribersAdmin(admin.ModelAdmin):
    actions = [send_newsletters]


admin.site.register(JaneusSubscriber)
admin.site.register(EmailSubscriber)
admin.site.register(MailingList)
admin.site.register(NewsletterTemplate)
admin.site.register(Newsletter, NewsletterAdmin)
admin.site.register(NewsletterToList, NewsletterToListAdmin)
admin.site.register(NewsletterToSubscriber, NewsletterToSubscribersAdmin)
