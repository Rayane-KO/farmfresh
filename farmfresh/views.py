from django.views.generic import TemplateView
from view_breadcrumbs import BaseBreadcrumbMixin

class HomePage(TemplateView):
    template_name = "index.html"

class TestPage(TemplateView):
    template_name = "test.html"

class ThanksPage(TemplateView):
    template_name = "thanks.html"

class AboutPage(BaseBreadcrumbMixin, TemplateView):
    template_name = "about.html"
    crumbs = [("About", "")]