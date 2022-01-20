import json
import math
import datetime
from collections import Counter
from operator import itemgetter

from django import forms
from django.core.cache import cache

from django_dramatiq import models
from .settings import get_load_chart_qs, get_timeline_chart_qs, get_cache_form_data_min


def _get_actor_choices() -> ((str, str),):
    key = 'django_dramatiq_charts__actor_choice_list'
    cache_form_data_min = get_cache_form_data_min()
    result = tuple()
    if cache_form_data_min:
        result = cache.get(key)
    if not result:
        result = (('', '<Actor>'),) + tuple(
            (i, i) for i in models.Task.tasks.values_list('actor_name', flat=True).distinct().order_by('actor_name')
        )
        if cache_form_data_min:
            cache.set(key, result, cache_form_data_min)
    return result


def _get_queue_choices() -> ((str, str),):
    key = 'django_dramatiq_charts__queue_choice_list'
    cache_form_data_min = get_cache_form_data_min()
    result = tuple()
    if cache_form_data_min:
        result = cache.get(key)
    if not result:
        result = (('', '<Queue>'),) + tuple(
            (i, i) for i in models.Task.tasks.values_list('queue_name', flat=True).distinct().order_by('queue_name')
        )
        if cache_form_data_min:
            cache.set(key, result, cache_form_data_min)
    return result


def _now_dt() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _four_hours_ago() -> str:
    return (datetime.datetime.now() - datetime.timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S")


def _task_duration_ms(start: datetime.datetime, end: datetime.datetime) -> int:
    """Duration in milliseconds"""
    return int((end - start).total_seconds() * 1000)


class DramatiqBasicChartForm(forms.Form):
    start_date = forms.DateTimeField(label='Period start', initial=_four_hours_ago, widget=forms.DateTimeInput(
        attrs={'placeholder': 'Period start', 'style': 'width: 9.5rem;', 'maxlength': '19'}
    ))
    end_date = forms.DateTimeField(label='Period end', initial=_now_dt, widget=forms.DateTimeInput(
        attrs={'placeholder': 'Period end', 'style': 'width: 9.5rem;', 'maxlength': '19'}
    ))
    queue = forms.ChoiceField(choices=_get_queue_choices, required=False, label='Queue')
    actor = forms.ChoiceField(choices=_get_actor_choices, required=False, label='Actor')
    status = forms.ChoiceField(choices=[('', '<All statuses>')] + models.Task.STATUSES, required=False,
                               initial=models.Task.STATUS_DONE, label='Status')

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date', None)
        end_date = cleaned_data.get('end_date', None)
        time_interval = cleaned_data.get('time_interval', None)
        if start_date and end_date:
            if start_date >= end_date:
                raise forms.ValidationError('The period start date is greater than or equal to the period end date')
            if (end_date - start_date) > datetime.timedelta(days=3):
                raise forms.ValidationError('The maximum date range is 3 days')
        if time_interval:
            if (end_date - start_date).total_seconds() < time_interval * 2:
                raise forms.ValidationError('Time interval is too long')
        return cleaned_data


class DramatiqLoadChartForm(DramatiqBasicChartForm):
    time_interval = forms.IntegerField(
        label='Interval sec', initial=10, min_value=1, max_value=60 * 60 * 24,
        widget=forms.TextInput(attrs={'style': 'width: 2rem;', 'maxlength': '5'})
    )

    field_order = ['start_date', 'end_date', 'time_interval']

    def get_chart_data(self) -> dict:
        cd = self.cleaned_data
        start_date = cd['start_date'].replace(second=0, microsecond=0)
        end_date = cd['end_date'].replace(second=0, microsecond=0)
        tick_sec = cd['time_interval']
        actor = cd.get('actor')
        queue = cd.get('queue')
        status = cd.get('status')
        # get qs
        task_qs = models.Task.tasks.filter(
            updated_at__gte=start_date, created_at__lte=end_date
        ).order_by('updated_at')
        load_chart_qs = get_load_chart_qs()
        if actor:
            task_qs = task_qs.filter(actor_name=actor)
        if queue:
            task_qs = task_qs.filter(queue_name=queue)
        if status:
            task_qs = task_qs.filter(status=status)
        if load_chart_qs:
            task_qs = task_qs.filter(load_chart_qs)
        if not task_qs.count():
            return {"empty_qs": True}
        categories = []
        # dt: a list of actors that worked at this time
        dt_format = "%Y-%m-%d %H:%M:%S"
        actor_wt_by_ticks = {(start_date + datetime.timedelta(seconds=i)).strftime(dt_format): []
                             for i in range(0, int((end_date - start_date).total_seconds() + tick_sec), tick_sec)}
        for task in task_qs:
            # correcting the time range for external tasks
            updated_at = min(task.updated_at, end_date)
            created_at = max(task.created_at, start_date)
            if (task.updated_at - task.created_at).days >= 1:
                # miss tasks that "work" for more than a day (most likely an error)
                continue
            if task.actor_name not in categories:
                categories.append(task.actor_name)
            actor_work_secs = (updated_at - created_at).total_seconds()
            # seconds passed before the next tick interval
            next_tick = math.ceil((created_at - start_date).total_seconds() / tick_sec) * tick_sec
            start_time = start_date + datetime.timedelta(seconds=next_tick)
            # what ticks should this actor be assigned to
            for sec in range(0, int(actor_work_secs / tick_sec) + 1):
                calculating_dt = start_time + datetime.timedelta(seconds=tick_sec * sec)
                if calculating_dt > end_date:
                    # actor can run longer than the final dt of the chart
                    continue
                else:
                    timestamp = (start_time + datetime.timedelta(seconds=tick_sec * sec)).strftime(dt_format)
                    actor_wt_by_ticks[timestamp].append(task.actor_name)
        categories = sorted(categories, reverse=True)
        working_actors_count = [[] for _ in categories]
        dates = []
        for date, actors in actor_wt_by_ticks.items():
            actors_count = Counter(actors)
            dates.append(date)
            if actors_count:
                for i, items in enumerate(categories):
                    if items in set(actors):
                        working_actors_count[i].append(actors_count[items])
                    else:
                        working_actors_count[i].append(None)
            else:
                for i, _ in enumerate(categories):
                    working_actors_count[i].append(None)
        chart_title = ', '.join(
            '{}: {}'.format(self.fields[key].label, value) for key, value in cd.items() if value != '')
        return {
            "categories": json.dumps(categories),
            "working_actors_count": json.dumps(working_actors_count),
            "dates": json.dumps(dates),
            'chart_height': json.dumps(200 + len(categories) * 25),
            'chart_title': json.dumps(chart_title),
            "empty_qs": False,
        }


class DramatiqTimelineChartForm(DramatiqBasicChartForm):
    def get_chart_data(self) -> dict:
        cd = self.cleaned_data
        start_date = cd['start_date']
        end_date = cd['end_date']
        actor = cd.get('actor')
        queue = cd.get('queue')
        status = cd.get('status')
        dt_format = "%Y-%m-%d %H:%M:%S"
        task_qs = models.Task.tasks.filter(
            updated_at__gte=start_date, created_at__lte=end_date
        ).order_by('updated_at')
        timeline_chart_qs = get_timeline_chart_qs()
        if actor:
            task_qs = task_qs.filter(actor_name=actor)
        if queue:
            task_qs = task_qs.filter(queue_name=queue)
        if status:
            task_qs = task_qs.filter(status=status)
        if timeline_chart_qs:
            task_qs = task_qs.filter(timeline_chart_qs)
        if not task_qs.count():
            return {"empty_qs": True}
        filter_data = {
            'start_date': start_date.strftime(dt_format),
            'end_date': end_date.strftime(dt_format),
            'actor': actor,
            'queue': queue,
            'status': status,
        }
        chart_data = []
        for task in task_qs:
            chart_data.append({
                'actor': task.actor_name,
                'status': task.status,
                'duration': _task_duration_ms(task.created_at, task.updated_at),
                'start': task.created_at.strftime(dt_format + ".%f"),
                'end': task.updated_at.strftime(dt_format + ".%f"),
            })
        chart_data.sort(key=itemgetter('end'), reverse=True)
        chart_data.sort(key=itemgetter('actor'), reverse=True)
        chart_title = ', '.join(
            '{}: {}'.format(self.fields[key].label, value) for key, value in cd.items() if value != '')
        return {
            "filter_data": json.dumps(filter_data),
            "chart_data": json.dumps(chart_data),
            'chart_title': json.dumps(chart_title),
            "empty_qs": False,
        }
