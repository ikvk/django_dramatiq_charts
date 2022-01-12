from django.conf import settings


def _has_charts_perm_fn_default(request):
    return request.user.is_superuser


def get_perm_fn():
    return getattr(settings, "DJANGO_DRAMATIQ_CHARTS_PERM_FN", _has_charts_perm_fn_default)


def get_plotly_lib():
    return getattr(settings, "DJANGO_DRAMATIQ_CHARTS_PLOTLY_LIB", 'https://cdn.plot.ly/plotly-latest.min.js')


def get_load_chart_qs():
    return getattr(settings, "DJANGO_DRAMATIQ_CHARTS_LOAD_CHART_QS", None)


def get_timeline_chart_qs():
    return getattr(settings, "DJANGO_DRAMATIQ_CHARTS_TIMELINE_CHART_QS", None)


def get_cache_form_data_min():
    return getattr(settings, "DJANGO_DRAMATIQ_CHARTS_CACHE_FORM_DATA_MIN", 12 * 60)
