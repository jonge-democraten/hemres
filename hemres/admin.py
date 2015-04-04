from __future__ import unicode_literals
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.forms import ModelForm
from .models import JaneusSubscriber, EmailSubscriber, MailingList, Newsletter, NewsletterFile, NewsletterTemplate
from .models import NewsletterToList, NewsletterToSubscriber


class TemplateAttachmentInline(admin.TabularInline):
    model = NewsletterTemplate.files.through


class NewsletterTemplateAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'create_newsletter',)
    inlines = [TemplateAttachmentInline, ]

    def create_newsletter(self, obj):
        return '<a href="%s">Create newsletter</a>' % (reverse('create_newsletter', args=[obj.pk]),)
    create_newsletter.allow_tags = True
    create_newsletter.short_description = 'Create newsletter'


class NewsletterFileAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'description')


class NewsletterAttachmentInline(admin.TabularInline):
    model = Newsletter.files.through


class NewsletterAdminForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(NewsletterAdminForm, self).__init__(*args, **kwargs)

        # check if we have mezzanine
        try:
            from mezzanine.core.forms import TinyMceWidget
            self.fields['content'].widget = TinyMceWidget()
            self.fields['content'].widget.attrs['data-mce-conf'] = "{\"convert_urls\": false, \"relative_urls\": false, \"theme\": \"advanced\"}"
        except ImportError:
            from tinymce.widgets import TinyMCE
            self.fields['content'].widget = TinyMCE(attrs={'cols': 80, 'rows': 30}, mce_attrs={'theme': 'advanced', 'convert_urls': False, 'relative_urls': False})


class NewsletterAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'date', 'view_mail', 'test_mail', 'prepare_sending')
    inlines = [NewsletterAttachmentInline, ]
    form = NewsletterAdminForm

    def view_mail(self, obj):
        return '<a href="%s">View in browser</a>' % (reverse('view_newsletter', args=[obj.pk]),)
    view_mail.allow_tags = True
    view_mail.short_description = 'View in browser'

    def test_mail(self, obj):
        return '<a href="%s">Send test mail</a>' % (reverse('test_newsletter', args=[obj.pk]),)
    test_mail.allow_tags = True
    test_mail.short_description = 'Send test mail'

    def prepare_sending(self, obj):
        return '<a href="%s">Send to list</a>' % (reverse('prepare_sending', args=[obj.pk]),)
    prepare_sending.allow_tags = True
    prepare_sending.short_description = 'Send to list'


admin.site.register(JaneusSubscriber)
admin.site.register(EmailSubscriber)
admin.site.register(MailingList)
admin.site.register(NewsletterTemplate, NewsletterTemplateAdmin)
admin.site.register(NewsletterFile, NewsletterFileAdmin)
admin.site.register(Newsletter, NewsletterAdmin)
admin.site.register(NewsletterToList)
admin.site.register(NewsletterToSubscriber)
