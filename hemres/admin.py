from __future__ import unicode_literals
from django.contrib import admin
from .models import JaneusSubscriber, EmailSubscriber, MailingList, Newsletter, NewsletterFile, NewsletterTemplate


class NewsletterFileAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'description')


admin.site.register(JaneusSubscriber)
admin.site.register(EmailSubscriber)
admin.site.register(MailingList)
admin.site.register(NewsletterTemplate)
admin.site.register(NewsletterFile, NewsletterFileAdmin)
admin.site.register(Newsletter)
