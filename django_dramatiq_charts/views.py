from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.core.cache import cache

from .consts import CACHE_KEY_ACTOR_CHOICES, CACHE_KEY_QUEUE_CHOICES
from .forms import DramatiqLoadChartForm, DramatiqTimelineChartForm
from .settings import get_perm_fn, get_plotly_lib, get_cache_form_data_min

_err_get_only = '<h3>GET only</h3>'
_err_access_denied = '<h3>Access denied, <a href="/">go home 🏠</a></h3>'


def load_chart(request):
    if request.method != "GET":
        return HttpResponse(_err_get_only)
    if not (get_perm_fn())(request):
        return HttpResponse(_err_access_denied)
    response = {}
    if request.GET:
        form = DramatiqLoadChartForm(request.GET)
        if form.is_valid():
            response.update(form.get_chart_data())
    else:
        form = DramatiqLoadChartForm()
    response.update({
        'form': form,
        'plotly_lib': get_plotly_lib(),
        'cache_enabled': get_cache_form_data_min(),
    })
    return render(request, 'django_dramatiq_charts/load_chart.html', response)


def timeline_chart(request):
    if request.method != "GET":
        return HttpResponse(_err_get_only)
    if not (get_perm_fn())(request):
        return HttpResponse(_err_access_denied)
    response = {}
    if request.GET:
        form = DramatiqTimelineChartForm(request.GET)
        if form.is_valid():
            response.update(form.get_chart_data())
    else:
        form = DramatiqTimelineChartForm()
    response.update({
        'form': form,
        'plotly_lib': get_plotly_lib(),
        'cache_enabled': get_cache_form_data_min(),
    })
    return render(request, 'django_dramatiq_charts/timeline_chart.html', response)


def clean_cache(request):
    cache.delete_many((CACHE_KEY_ACTOR_CHOICES, CACHE_KEY_QUEUE_CHOICES))
    return redirect(request.META.get('HTTP_REFERER'))
