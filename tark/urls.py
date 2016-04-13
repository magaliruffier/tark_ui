from django.conf.urls import patterns, url
from django.views.generic.base import RedirectView

from tark import views

urlpatterns = patterns('',
                       url(r'^sequence/(?P<seqtype>[\w]+)/(?P<seqid>[\w\.]+)/$', views.getsequence, name='sequence'),
                       url(r'^lookup/(?P<seqtype>[\w]+)/(?P<seqid>[\w\.]+)/$', views.idlookup, name='idlookup'),
                       )
