.. http://docutils.sourceforge.net/docs/user/rst/quickref.html

django_dramatiq_charts 📊
=========================

Charts for `django_dramatiq <https://github.com/Bogdanp/django_dramatiq>`_ allow to track the completion of tasks using `Plotly.js <https://github.com/plotly/plotly.js/>`_.

There are two types of charts: `load <#load-chart>`_ and `timeline <#timeline-chart>`_.

.. image:: https://img.shields.io/pypi/dm/django_dramatiq_charts.svg?style=social

===============  ===============================================================
Python version   3.6+
License          Apache-2.0
PyPI             https://pypi.python.org/pypi/django_dramatiq_charts/
===============  ===============================================================

.. contents::

Installation
------------
::

    $ pip install django-dramatiq-charts

Guide
-----

Basic
^^^^^

To use the charts you can add the functions *load_chart*, *timeline_chart*, *update_cache* from views to urls. Where the path name for the cache should be equal to *'update_cache'*.

To control additional parameters, set the following variables in your project settings file:

==========================================   ====================================================================================================================   ==========================================
Variable                                     Description                                                                                                            Default
==========================================   ====================================================================================================================   ==========================================
DJANGO_DRAMATIQ_CHARTS_CACHE_FORM_DATA_MIN   the number of seconds of the cache timeout for the queue and actor form fields (0 or *None* to disable data caching)   720
DJANGO_DRAMATIQ_CHARTS_LOAD_CHART_QS         additional queryset for the load chart                                                                                 *None*
DJANGO_DRAMATIQ_CHARTS_PERM_FN               users with access to the charts                                                                                        request.user.is_superuser
DJANGO_DRAMATIQ_CHARTS_PLOTLY_LIB            CDN link for Plotly.js                                                                                                 'https://cdn.plot.ly/plotly-2.8.3.min.js'
DJANGO_DRAMATIQ_CHARTS_TIMELINE_CHART_QS     additional queryset for the timeline chart                                                                             *None*
==========================================   ====================================================================================================================   ==========================================

Load chart
^^^^^^^^^^

It shows the number of tasks for each actor over time using a color bar (the graph area is divided into intervals of a certain duration, displaying the task load).

.. image:: docs/load_chart.png

When hovering over the task interval, the actor's name, date and number of tasks are displayed.

Tasks running more than a day are not counted (assumed to be an error).

The graph filter form contains the following fields:

- Period start
- Period end
- Time interval
- Queue name
- Actor name
- Task status

The maximum date range is 3 days, time interval is an integer number of seconds between 1 and half a period.

To set the form fields to default, press *Reset*. To refresh the queue and actor cache, press *Update cache*.

Timeline chart
^^^^^^^^^^^^^^

It has two display modes:

1. overlay (depict the tasks over each other for every actor on the timeline),

.. figure:: docs/timeline_chart_overlay.png

2. group (uncover tasks within a single chosen actor).

.. figure:: docs/timeline_chart_group.png

To change a mod, you need to click on the task of the actor you are interested in. To return to the overlay you can click on any task.

When hovering over the task, the actor's name, status, duration, start and update time are displayed.

If the task duration is less than a second, this task is depicted on the chart with a duration of 1 second.

The graph filter form contains the following fields:

- Period start
- Period end
- Queue name
- Actor name
- Task status

The maximum date range is 3 days.

To set the form fields to default, press *Reset*. To refresh the queue and actor cache, press *Update cache*.

Release notes
-------------

History of important changes: `release_notes.rst <https://github.com/ikvk/django_dramatiq_charts/blob/master/docs/release_notes.rst>`_

Thanks
------

Big thanks to people who helped develop this library:

your name may be here :)
