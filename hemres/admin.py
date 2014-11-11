from django.contrib import admin
from .models import JaneusSubscriber, EmailSubscriber, MailingList

admin.site.register(JaneusSubscriber)
admin.site.register(EmailSubscriber)
admin.site.register(MailingList)
