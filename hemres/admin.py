from __future__ import unicode_literals
from django.contrib import admin
from django.core.urlresolvers import reverse
from .models import JaneusSubscriber, EmailSubscriber, MailingList, Newsletter, NewsletterFile, NewsletterTemplate


class NewsletterTemplateAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'create_newsletter',)

    def create_newsletter(self, obj):
        return '<a href="%s">Create newsletter</a>' % (reverse('create_newsletter', args=[obj.pk]),)
    create_newsletter.allow_tags = True
    create_newsletter.short_description = 'Create newsletter'


class NewsletterFileAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'description')


admin.site.register(JaneusSubscriber)
admin.site.register(EmailSubscriber)
admin.site.register(MailingList)
admin.site.register(NewsletterTemplate, NewsletterTemplateAdmin)
admin.site.register(NewsletterFile, NewsletterFileAdmin)
admin.site.register(Newsletter)
