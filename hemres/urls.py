from __future__ import unicode_literals
from django.conf.urls import patterns, url
from . import views

urlpatterns = patterns(
    '',
    url(r'^$', views.view_home, name='home'),
    url(r'^subscriptions/e/(?P<subscriber>\d+)/(?P<token>.+)/$', views.ManageEmailSubscriptions.as_view(), name='subscriptions_email'),
    url(r'^subscriptions/j/(?P<subscriber>\d+)/(?P<token>.+)/$', views.ManageJaneusSubscriptions.as_view(), name='subscriptions_janeus'),
    url(r'^subscriptions/done/$', views.subscriptions_done),
)
