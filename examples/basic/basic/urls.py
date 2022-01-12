"""basic URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django_dramatiq_charts.views import load_chart, timeline_chart, update_cache
from django.conf.urls import include, url

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dramatiq_load_chart/', load_chart, name='load_chart'),
    path('dramatiq_timeline_chart/', timeline_chart, name='timeline_chart'),
    path('update_cache/', update_cache, name='update_cache'),
    url(r'^', include('dashboard.urls')),
]
