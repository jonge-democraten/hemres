from __future__ import unicode_literals
from django.contrib import admin
from django.core.urlresolvers import reverse, reverse_lazy
from django.forms import ModelForm
from django.utils import timezone
from mezzanine.conf import settings as msettings
from mezzanine.utils.sites import current_site_id
from .models import JaneusSubscriber, EmailSubscriber, MailingList, Newsletter, NewsletterTemplate
from .models import NewsletterToList, NewsletterToSubscriber
from .forms import CreateNewsletterForm


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
    form = NewsletterAdminForm
    search_fields = ('subject', 'content')

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            fieldsets = (
                (None, {
                    'fields': ('subject', 'template', 'events'),
                }),
            )
            return fieldsets

        fieldsets = (
            (None, {
                'fields': ('subject', ),
                'description': 'Geef het onderwerp van de nieuwsbrief. Afhankelijk van de mailinglist waarnaar de nieuwsbrief verzonden wordt, komt de naam van de mailinglist er in blockhaken voor: "[Mailinglist] Onderwerp"',
            }),
            (None, {
                'fields': ('content', ),
                'description': 'Heading 1: de eerste regel van de nieuwsbrief (de titel).<br/>Heading 2: de kopjes tussen onderdelen van de nieuwsbrief.<br/>Heading 3: een kopje binnen een onderdeel van de nieuwsbrief.<br/>De tekst {{naam}} wordt vervangen door de naam van de geaddresseerde.'
            }),
            (None, {
                'fields': ['template', 'public'],
            }),
        )
        if not request.user.has_perm('hemres.change_newslettertemplate'):
            fieldsets[2][1]['fields'].remove('template')
        return fieldsets

    def get_fields(self, request, obj=None):
        fields = super(NewsletterAdmin, self).get_fields(request, obj=obj)
        if not request.user.has_perm('hemres.change_newslettertemplate'):
            fields.remove('template')
        return fields

    def get_list_display(self, request):
        if request.user.has_perm('hemres.add_newsletter'):
            return ('__str__', 'date', 'view_mail', 'test_mail', 'prepare_sending')
        else:
            return ('__str__', 'date', 'view_mail', 'test_mail')

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

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            # for adding
            return CreateNewsletterForm
        else:
            return super(NewsletterAdmin, self).get_form(request, obj, **kwargs)

    def save_model(self, request, obj, form, change):
        obj.fix_relative_urls(request)
        obj.save()

    def save_related(self, request, form, formsets, change):
        # we only want to intercept for adding
        if change:
            return super(NewsletterAdmin, self).save_related(request, form, formsets, True)

    def save_form(self, request, form, change):
        # we only want to intercept for adding
        if change:
            return super(NewsletterAdmin, self).save_form(request, form, True)

        # get the information from the form
        template = form.cleaned_data['template']
        subject = form.cleaned_data['subject']
        newsletter = template.create_newsletter(subject=subject)

        # now write the newsletter using some hard-coded (ew) template
        newsletter.content = "<h1>Beste {{naam}},</h1>"
        newsletter.content += "<p>Introductietekst</p>"

        # if we want events, add each event (again, hard-coded)
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

            # for URLs to the site, look if we have SSL_ENABLED and choose https if so
            protocol = "http"
            if msettings.SSL_ENABLED:
                protocol = "https"

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

        # all events added, save and return!
        newsletter.save()
        return newsletter


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
        url = 'https://{}{}'.format(obj.newsletter.site.domain,
                                    reverse('view_newsletter', args=[obj.newsletter.pk]))
        return '<a href="{}">View in browser</a>'.format(url)
    view_mail.allow_tags = True
    view_mail.short_description = 'View in browser'

    def test_mail(self, obj):
        url = 'https://{}{}'.format(obj.newsletter.site.domain,
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


class NewsletterTemplateAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('title', 'template'),
            'description': "Gebruik {{ naam }}, {{ subject }} en {{ content }} voor de naam van de geaddresseerde, het onderwerp van de nieuwsbrief, en de inhoud van de nieuwsbrief.</br>" +
                           "Gebruik {{ subscriptions_url }} voor de absolute URL naar de aan- en afmeldpagina."
        }),
    )


admin.site.register(JaneusSubscriber)
admin.site.register(EmailSubscriber)
admin.site.register(MailingList)
admin.site.register(NewsletterTemplate, NewsletterTemplateAdmin)
admin.site.register(Newsletter, NewsletterAdmin)
admin.site.register(NewsletterToList, NewsletterToListAdmin)
admin.site.register(NewsletterToSubscriber, NewsletterToSubscribersAdmin)
