import json
import math
import datetime
from hashlib import md5
from collections import Counter

from django import forms
from django.core.cache import cache
from django_dramatiq import models

from .consts import CACHE_KEY_ACTOR_CHOICES, CACHE_KEY_QUEUE_CHOICES
from .config import get_load_chart_qs, get_timeline_chart_qs, get_cache_form_data_sec


def get_actor_choices() -> ((str, str),):
    cache_form_data_sec = get_cache_form_data_sec()
    result = tuple()
    if cache_form_data_sec:
        result = cache.get(CACHE_KEY_ACTOR_CHOICES)
    if not result:
        result = tuple(
            (i, i) for i in models.Task.tasks.values_list('actor_name', flat=True).distinct().order_by('actor_name')
        )
        if cache_form_data_sec:
            cache.set(CACHE_KEY_ACTOR_CHOICES, result, cache_form_data_sec)
    return result


def get_queue_choices() -> ((str, str),):
    cache_form_data_sec = get_cache_form_data_sec()
    result = tuple()
    if cache_form_data_sec:
        result = cache.get(CACHE_KEY_QUEUE_CHOICES)
    if not result:
        result = tuple(
            (i, i) for i in models.Task.tasks.values_list('queue_name', flat=True).distinct().order_by('queue_name')
        )
        if cache_form_data_sec:
            cache.set(CACHE_KEY_QUEUE_CHOICES, result, cache_form_data_sec)
    return result


def get_dt_delta_ms(start: datetime.datetime, end: datetime.datetime) -> int:
    """Duration in milliseconds"""
    return int((end - start).total_seconds() * 1000)


def _now_dt() -> datetime.datetime:
    return datetime.datetime.now()


def _4_hours_ago() -> datetime.datetime:
    return datetime.datetime.now() - datetime.timedelta(hours=4)


def _permanent_hex_color_for_name(name: str) -> str:
    hex_color: str = md5(str(name).encode()).hexdigest()[1:7]
    return '#' + hex_color


class BasicFilterForm(forms.Form):
    date_format = "%Y-%m-%d"
    dt_format_sec = "%Y-%m-%d %H:%M:%S"
    dt_format_ms = "%Y-%m-%d %H:%M:%S.%f"

    start_date = forms.DateTimeField(label='Period start', initial=_4_hours_ago, widget=forms.DateTimeInput(
        attrs={'placeholder': 'Period start', 'style': 'width: 9.5rem;', 'maxlength': '19'}
    ))
    end_date = forms.DateTimeField(label='Period end', initial=_now_dt, widget=forms.DateTimeInput(
        attrs={'placeholder': 'Period end', 'style': 'width: 9.5rem;', 'maxlength': '19'}
    ))
    queue = forms.MultipleChoiceField(choices=get_queue_choices, required=False, label='Queue')
    actor = forms.MultipleChoiceField(choices=get_actor_choices, required=False, label='Actor')

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date', None)
        end_date = cleaned_data.get('end_date', None)
        time_interval = cleaned_data.get('time_interval', None)
        if start_date and end_date:
            if start_date >= end_date:
                raise forms.ValidationError('The period start date is greater than or equal to the period end date')
            if (end_date - start_date) > datetime.timedelta(days=7):
                raise forms.ValidationError('The maximum date range is 7 days')
            if time_interval:
                if (end_date - start_date).total_seconds() < time_interval * 2:
                    raise forms.ValidationError('Time interval is too long')
        return cleaned_data

    def get_title(self) -> str:
        pairs = []
        if self.is_bound and self.is_valid():
            for field_name in self.fields:
                if field_name in self.cleaned_data and self.cleaned_data[field_name]:
                    fields_label = self.fields[field_name].label
                    field_value = self.cleaned_data[field_name]
                    if type(field_value) is datetime.date:
                        pairs.append((fields_label, field_value.strftime(self.date_format)))
                    elif type(field_value) is datetime.datetime:
                        pairs.append((fields_label, field_value.strftime(self.dt_format_sec)))
                    elif hasattr(self.fields[field_name], 'choices'):
                        pairs.append((fields_label, ', '.join(
                            [dict(self.fields[field_name].choices)[value] for value in field_value])))
                    else:
                        pairs.append((fields_label, field_value))
        return ', '.join('{}: <b>{}</b>'.format(k, v) for k, v in pairs if v)


class DramatiqLoadChartForm(BasicFilterForm):
    time_interval = forms.IntegerField(
        label='Interval sec', initial=10, min_value=1, max_value=60 * 60 * 24,
        widget=forms.TextInput(attrs={'style': 'width: 2rem;', 'maxlength': '5'})
    )
    status = forms.MultipleChoiceField(label='Status', required=False,
                                       choices=models.Task.STATUSES, initial=models.Task.STATUS_DONE)

    field_order = ['start_date', 'end_date', 'time_interval']

    def get_chart_data(self) -> dict:
        cd = self.cleaned_data
        start_date = cd['start_date'].replace(second=0, microsecond=0)
        end_date = cd['end_date'].replace(second=0, microsecond=0)
        tick_sec = cd['time_interval']
        actors = cd.get('actor')
        queues = cd.get('queue')
        statuses = cd.get('status')
        # get qs
        task_qs = models.Task.tasks.filter(
            updated_at__gte=start_date, created_at__lte=end_date
        ).order_by('updated_at')
        load_chart_qs = get_load_chart_qs()
        if actors:
            task_qs = task_qs.filter(actor_name__in=actors)
        if queues:
            task_qs = task_qs.filter(queue_name__in=queues)
        if statuses:
            task_qs = task_qs.filter(status__in=statuses)
        if load_chart_qs:
            task_qs = task_qs.filter(load_chart_qs)
        if not task_qs.count():
            return {
                'empty_qs': True,
                'chart_title': self.get_title(),
            }
        categories = []
        # dt: a list of actors that worked at this time
        actor_wt_by_ticks = {(start_date + datetime.timedelta(seconds=i)).strftime(self.dt_format_sec): []
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
                    timestamp = (start_time + datetime.timedelta(seconds=tick_sec * sec)).strftime(self.dt_format_sec)
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
        return {
            'categories': json.dumps(categories),
            'working_actors_count': json.dumps(working_actors_count),
            'dates': json.dumps(dates),
            'chart_height': json.dumps(200 + len(categories) * 25),
            'chart_title': self.get_title(),
            'empty_qs': False,
        }


class DramatiqTimelineChartForm(BasicFilterForm):
    status = forms.MultipleChoiceField(label='Status', required=False, choices=models.Task.STATUSES)

    def get_chart_data(self) -> dict:
        cd = self.cleaned_data
        start_date = cd['start_date']
        end_date = cd['end_date']
        actors = cd.get('actor')
        queues = cd.get('queue')
        statuses = cd.get('status')
        task_qs = models.Task.tasks.filter(
            updated_at__gte=start_date, created_at__lte=end_date
        ).order_by('-created_at', '-updated_at')
        timeline_chart_qs = get_timeline_chart_qs()
        if actors:
            task_qs = task_qs.filter(actor_name__in=actors)
        if queues:
            task_qs = task_qs.filter(queue_name__in=queues)
        if statuses:
            task_qs = task_qs.filter(status__in=statuses)
        if timeline_chart_qs:
            task_qs = task_qs.filter(timeline_chart_qs)
        if not task_qs.count():
            return {
                'chart_title': self.get_title(),
                'empty_qs': True,
            }
        filter_data = {
            'start_date': start_date.strftime(self.dt_format_sec),
            'end_date': end_date.strftime(self.dt_format_sec),
            'actor': actors,
            'queue': queues,
            'status': statuses,
        }
        chart_data = []
        for task in task_qs:
            chart_data.append({
                'actor': task.actor_name,
                'queue': task.queue_name,
                'status': task.status,
                'color': _permanent_hex_color_for_name(task.actor_name),
                'duration': get_dt_delta_ms(task.created_at, task.updated_at),
                'start': task.created_at.strftime(self.dt_format_ms),
                'end': task.updated_at.strftime(self.dt_format_ms),
            })
        return {
            'filter_data': json.dumps(filter_data),
            'chart_data': json.dumps(chart_data),
            'chart_title': self.get_title(),
            'empty_qs': False,
        }
