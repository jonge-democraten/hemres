from __future__ import unicode_literals
from django.contrib import admin
from django.core.urlresolvers import reverse, reverse_lazy
from django.forms import ModelForm
from .models import JaneusSubscriber, EmailSubscriber, MailingList, Newsletter, NewsletterFile, NewsletterTemplate
from .models import NewsletterToList, NewsletterToSubscriber


class TemplateAttachmentInline(admin.TabularInline):
    model = NewsletterTemplate.files.through


class NewsletterTemplateAdmin(admin.ModelAdmin):
    inlines = [TemplateAttachmentInline, ]


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
            pass


class NewsletterAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'date', 'view_mail', 'test_mail', 'prepare_sending')
    inlines = [NewsletterAttachmentInline, ]
    form = NewsletterAdminForm

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
        return '<a href="%s">View in browser</a>' % (reverse('view_newsletter', args=[obj.newsletter.pk]),)
    view_mail.allow_tags = True
    view_mail.short_description = 'View in browser'

    def test_mail(self, obj):
        return '<a href="%s">Send test mail</a>' % (reverse('test_newsletter', args=[obj.newsletter.pk]),)
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
admin.site.register(NewsletterTemplate, NewsletterTemplateAdmin)
admin.site.register(NewsletterFile, NewsletterFileAdmin)
admin.site.register(Newsletter, NewsletterAdmin)
admin.site.register(NewsletterToList, NewsletterToListAdmin)
admin.site.register(NewsletterToSubscriber, NewsletterToSubscribersAdmin)
