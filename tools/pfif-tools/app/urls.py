from django.conf.urls import url

import views.controller
import views.forms
import views.index

urlpatterns = [
    url(r'^$', views.index.IndexView.as_view()),
    url(r'^diff/?$', views.forms.DiffFormView.as_view()),
    url(r'^diff/results/?$', views.controller.DiffController.as_view()),
    url(r'^validate/?$', views.forms.ValidatorFormView.as_view()),
    url(r'^validate/results/?$',
        views.controller.ValidatorController.as_view()),
]
