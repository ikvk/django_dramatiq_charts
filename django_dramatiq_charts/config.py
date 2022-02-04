from django.conf import settings


def _has_charts_perm_fn_default(request):
    return request.user.is_superuser


def get_perm_fn():
    return getattr(settings, "DJANGO_DRAMATIQ_CHARTS_PERM_FN", _has_charts_perm_fn_default)


def get_load_chart_qs():
    return getattr(settings, "DJANGO_DRAMATIQ_CHARTS_LOAD_QS_FILTER", None)


def get_timeline_chart_qs():
    return getattr(settings, "DJANGO_DRAMATIQ_CHARTS_TIMELINE_QS_FILTER", None)


def get_cache_form_data_sec():
    return getattr(settings, "DJANGO_DRAMATIQ_CHARTS_CACHE_FORM_DATA_SEC", 60 * 60 * 4)
