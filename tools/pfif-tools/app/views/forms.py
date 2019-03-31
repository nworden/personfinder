from django.views.generic.base import TemplateView


class ValidatorFormView(TemplateView):

    template_name = 'validator.html'


class DiffFormView(TemplateView):

    template_name = 'diff.html'
