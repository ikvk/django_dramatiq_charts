from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.core.cache import cache

from .forms import DramatiqLoadChartForm, DramatiqTimelineChartForm
from .settings import get_perm_fn, get_plotly_lib


def load_chart(request):
    if request.method != "GET":
        return HttpResponse('<h3>GET only</h3>')
    if not (get_perm_fn())(request):
        return HttpResponse('<h3>Access denied, <a href="/">go home 🏠</a></h3>')
    response = {}
    if request.GET:
        form = DramatiqLoadChartForm(request.GET)
        if form.is_valid():
            response.update(form.get_chart_data())
    else:
        form = DramatiqLoadChartForm()
    response.update({
        'form': form,
        'plotly_lib': get_plotly_lib()
    })
    return render(request, 'django_dramatiq_charts/load_chart.html', response)


def timeline_chart(request):
    if request.method != "GET":
        return HttpResponse('<h3>GET only</h3>')
    if not (get_perm_fn())(request):
        return HttpResponse('<h3>Access denied, <a href="/">go home 🏠</a></h3>')
    response = {}
    if request.GET:
        form = DramatiqTimelineChartForm(request.GET)
        if form.is_valid():
            response.update(form.get_chart_data())
    else:
        form = DramatiqLoadChartForm()
    response.update({
        'form': form,
        'plotly_lib': get_plotly_lib(),
    })
    return render(request, 'django_dramatiq_charts/timeline_chart.html', response)


def update_cache(request):
    cache.delete_many(['actor_choice_list', 'queue_choice_list'])
    return redirect(request.GET.get('redirect'))
