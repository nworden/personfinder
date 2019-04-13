from django import urls

import pfiftools.views.controller as controller
import pfiftools.views.forms as forms
import pfiftools.views.index as index

urlpatterns = [
    urls.re_path(r'^$', index.IndexView.as_view()),
    urls.re_path(r'^diff/?$', forms.DiffFormView.as_view()),
    urls.re_path(r'^diff/results/?$', controller.DiffController.as_view()),
    urls.re_path(r'^validate/?$', forms.ValidatorFormView.as_view()),
    urls.re_path(r'^validate/results/?$',
                 controller.ValidatorController.as_view()),
]
