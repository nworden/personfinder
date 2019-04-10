from django.conf.urls import url

import pfiftools.views.controller as controller
import pfiftools.views.forms as forms
import pfiftools.views.index as index

urlpatterns = [
    url(r'^$', index.IndexView.as_view()),
    url(r'^diff/?$', forms.DiffFormView.as_view()),
    url(r'^diff/results/?$', controller.DiffController.as_view()),
    url(r'^validate/?$', forms.ValidatorFormView.as_view()),
    url(r'^validate/results/?$', controller.ValidatorController.as_view()),
]
