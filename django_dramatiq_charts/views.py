from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.core.cache import cache
from django.core.handlers.wsgi import WSGIRequest
from django.conf import settings
from django.utils.http import url_has_allowed_host_and_scheme

from .consts import CACHE_KEY_ACTOR_CHOICES, CACHE_KEY_QUEUE_CHOICES
from .forms import DramatiqLoadChartForm, DramatiqTimelineChartForm
from .config import get_perm_fn, get_cache_form_data_sec, get_clean_cache_redirect_url

_err_get_only = '<h3>GET only</h3>'
_err_access_denied = '<h3>Access denied, <a href="/">go home 🏠</a></h3>'


def _safe_redirect_to_http_referer(request: WSGIRequest, fallback_url: str = '/') -> HttpResponseRedirect:
    http_referer = request.META.get('HTTP_REFERER')
    if http_referer and url_has_allowed_host_and_scheme(
            http_referer,
            allowed_hosts={request.get_host()},
            require_https=False if settings.DEBUG else request.is_secure()
    ):
        return redirect(http_referer)
    else:
        return redirect(fallback_url)


def load_chart(request):
    if request.method != "GET":
        return HttpResponse(_err_get_only)
    if not (get_perm_fn())(request):
        return HttpResponse(_err_access_denied)
    response = {}
    form = DramatiqLoadChartForm(request.GET or None)
    if form.is_valid():
        response.update(form.get_chart_data())
    response.update({
        'form': form,
        'cache_enabled': get_cache_form_data_sec(),
    })
    return render(request, 'django_dramatiq_charts/load_chart.html', response)


def timeline_chart(request):
    if request.method != "GET":
        return HttpResponse(_err_get_only)
    if not (get_perm_fn())(request):
        return HttpResponse(_err_access_denied)
    response = {}
    form = DramatiqTimelineChartForm(request.GET or None)
    if form.is_valid():
        response.update(form.get_chart_data())
    response.update({
        'form': form,
        'cache_enabled': get_cache_form_data_sec(),
    })
    return render(request, 'django_dramatiq_charts/timeline_chart.html', response)


def clean_cache(request):
    cache.delete_many((CACHE_KEY_ACTOR_CHOICES, CACHE_KEY_QUEUE_CHOICES))
    clean_cache_redirect_url = get_clean_cache_redirect_url()
    if clean_cache_redirect_url:
        return redirect(clean_cache_redirect_url)
    else:
        return _safe_redirect_to_http_referer(request)
