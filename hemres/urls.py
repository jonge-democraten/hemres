from __future__ import unicode_literals
from django.conf.urls import patterns, url
from . import views

urlpatterns = patterns(
    '',
    url(r'^$', views.view_home, name='home'),
    url(r'^subscriptions/e/(?P<subscriber>\d+)/(?P<token>.+)/$', views.ManageEmailSubscriptions.as_view(), name='subscriptions_email'),
    url(r'^subscriptions/j/(?P<subscriber>\d+)/(?P<token>.+)/$', views.ManageJaneusSubscriptions.as_view(), name='subscriptions_janeus'),
    url(r'^subscriptions/done/$', views.subscriptions_done),
    url(r'^create_newsletter/(?P<template_pk>\d+)/$', views.create_newsletter, name='create_newsletter'),
    url(r'^view/(?P<newsletter_pk>\d+)/$', views.view_newsletter, name='view_newsletter'),
    url(r'^test/(?P<pk>\d+)$', views.test_newsletter, name='test_newsletter'),
    url(r'^prepare/(?P<pk>\d+)$', views.prepare_sending, name='prepare_sending'),
    url(r'^process/(?P<pk>\d+)$', views.process_sending, name='process_sending'),
)
