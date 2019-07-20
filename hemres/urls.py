from django.conf.urls import url
from .views import *

urlpatterns = [
    url(r'^$', view_home, name='home'),
    url(r'^subscriptions/e/(?P<subscriber>\d+)/(?P<token>.+)/$', ManageEmailSubscriptions.as_view(), name='subscriptions_email'),
    url(r'^subscriptions/j/(?P<subscriber>\d+)/(?P<token>.+)/$', ManageJaneusSubscriptions.as_view(), name='subscriptions_janeus'),
    url(r'^subscriptions/done/$', subscriptions_done),
    url(r'^subscriptions/u/(?P<token>.+)/$', unsubscribe_landing),
    url(r'^subscriptions/a/(?P<token>.+)/$', unsubscribe_sendmail),
    url(r'^subscriptions/U/(?P<token>.+)/$', unsubscribe_unsub),
    url(r'^view/(?P<newsletter_pk>\d+)/$', view_newsletter, name='view_newsletter'),
    url(r'^test/(?P<pk>\d+)$', test_newsletter, name='test_newsletter'),
    url(r'^prepare/(?P<pk>\d+)$', prepare_sending, name='prepare_sending'),
    url(r'^process/(?P<pk>\d+)$', process_sending, name='process_sending'),
    url(r'^list/$', list_all, name='list_all'),
    url(r'^css/(?P<pk>\d+)$', get_css, name='get_css'),
]
