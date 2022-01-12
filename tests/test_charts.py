import time
import json
import datetime

import dramatiq

from django_dramatiq.models import Task
from django_dramatiq.test import DramatiqTestCase
from django_dramatiq_charts.forms import DramatiqLoadChartForm, DramatiqTimelineChartForm


class TestDramatiqLoadChart(DramatiqTestCase):

    def setUp(self):
        self.utcnow = datetime.datetime.utcnow()

        # two fast tasks
        @dramatiq.actor(queue_name='queue_fast', max_retries=0)
        def do_work_fast():
            time.sleep(0.01)

        for i in range(2):
            do_work_fast.send()
            self.broker.join(do_work_fast.queue_name)
            self.worker.join()

        # one slow task
        @dramatiq.actor(queue_name='queue_slow', max_retries=0)
        def do_work_slow():
            time.sleep(0.05)

        do_work_slow.send()
        self.broker.join(do_work_slow.queue_name)
        self.worker.join()

        # tasks in the database
        tasks = Task.tasks.all()
        self.assertEqual(3, tasks.count())

    def test_valid_form(self):
        form = DramatiqLoadChartForm(data=dict(
            start_date=self.utcnow - datetime.timedelta(minutes=1),
            end_date=self.utcnow + datetime.timedelta(minutes=1),
            time_interval=10,
            queue='',
            actor='',
            status=Task.STATUS_DONE,
        ))
        # form validation
        self.assertTrue(form.is_valid())
        data = form.get_chart_data()
        # empty qs
        self.assertFalse(data['empty_qs'])
        # chart height
        self.assertEqual('250', data['chart_height'])
        # categories
        self.assertEqual(['do_work_slow', 'do_work_fast'], json.loads(data['categories']))
        # dates
        self.assertEqual(13, len(json.loads(data['dates'])))
        # working actors count
        working_actors_count = json.loads(data['working_actors_count'])
        self.assertEqual(13, len(working_actors_count[0]))
        self.assertEqual(1, sum(i for i in working_actors_count[0] if i))
        self.assertEqual(2, sum(i for i in working_actors_count[1] if i))

    def test_invalid_forms(self):
        # end date is greater than start date
        form = DramatiqLoadChartForm(data=dict(
            start_date=self.utcnow + datetime.timedelta(minutes=1),
            end_date=self.utcnow - datetime.timedelta(minutes=1),
        ))
        self.assertFalse(form.is_valid())
        self.assertEqual(['The period start date is greater than or equal to the period end date'],
                         form.non_field_errors())

        # maximum date range is greater than 3 days
        form = DramatiqLoadChartForm(data=dict(
            start_date=self.utcnow - datetime.timedelta(days=2),
            end_date=self.utcnow + datetime.timedelta(days=2),
        ))
        self.assertFalse(form.is_valid())
        self.assertEqual(['The maximum date range is 3 days'], form.non_field_errors())

        # time interval is too long
        form = DramatiqLoadChartForm(data=dict(
            start_date=self.utcnow - datetime.timedelta(minutes=1),
            end_date=self.utcnow + datetime.timedelta(minutes=1),
            time_interval=100,
        ))
        self.assertFalse(form.is_valid())
        self.assertEqual(['Time interval is too long'], form.non_field_errors())

        # time interval is zero
        form = DramatiqLoadChartForm(data=dict(
            start_date=self.utcnow - datetime.timedelta(minutes=1),
            end_date=self.utcnow + datetime.timedelta(minutes=1),
            time_interval=0,
        ))
        self.assertFalse(form.is_valid())
        self.assertEqual(['Ensure this value is greater than or equal to 1.'], form.errors['time_interval'])

    def test_filters(self):
        # queue
        form = DramatiqLoadChartForm(data=dict(
            start_date=self.utcnow - datetime.timedelta(minutes=1),
            end_date=self.utcnow + datetime.timedelta(minutes=1),
            queue='queue_fast',
            time_interval=10,
        ))
        self.assertTrue(form.is_valid())
        data = form.get_chart_data()
        self.assertFalse(data['empty_qs'])
        self.assertEqual(['do_work_fast'], json.loads(data['categories']))
        working_actors_count = json.loads(data['working_actors_count'])
        self.assertEqual(2, sum(i for i in working_actors_count[0] if i))

        # actor
        form = DramatiqLoadChartForm(data=dict(
            start_date=self.utcnow - datetime.timedelta(minutes=1),
            end_date=self.utcnow + datetime.timedelta(minutes=1),
            actor='do_work_slow',
            time_interval=10,
        ))
        self.assertTrue(form.is_valid())
        data = form.get_chart_data()
        self.assertFalse(data['empty_qs'])
        self.assertEqual(['do_work_slow'], json.loads(data['categories']))
        working_actors_count = json.loads(data['working_actors_count'])
        self.assertEqual(1, sum(i for i in working_actors_count[0] if i))

        # status
        form = DramatiqLoadChartForm(data=dict(
            start_date=self.utcnow - datetime.timedelta(minutes=1),
            end_date=self.utcnow + datetime.timedelta(minutes=1),
            status=Task.STATUS_RUNNING,
            time_interval=10,
        ))
        self.assertTrue(form.is_valid())
        data = form.get_chart_data()
        self.assertTrue(data['empty_qs'])

        # time interval
        form = DramatiqLoadChartForm(data=dict(
            start_date=self.utcnow - datetime.timedelta(minutes=1),
            end_date=self.utcnow + datetime.timedelta(minutes=1),
            time_interval=1,
        ))
        self.assertTrue(form.is_valid())
        data = form.get_chart_data()
        self.assertFalse(data['empty_qs'])
        self.assertEqual(121, len(json.loads(data['dates'])))

        # date period
        form = DramatiqLoadChartForm(data=dict(
            start_date=self.utcnow + datetime.timedelta(minutes=1),
            end_date=self.utcnow + datetime.timedelta(minutes=2),
            time_interval=10,
        ))
        self.assertTrue(form.is_valid())
        data = form.get_chart_data()
        self.assertTrue(data['empty_qs'])


class TestDramatiqTimelineChart(DramatiqTestCase):

    def setUp(self):
        self.utcnow = datetime.datetime.utcnow()

        # two fast tasks
        @dramatiq.actor(queue_name='queue_fast', max_retries=0)
        def do_work_fast():
            time.sleep(0.01)

        for i in range(2):
            do_work_fast.send()
            self.broker.join(do_work_fast.queue_name)
            self.worker.join()

        # one slow task
        @dramatiq.actor(queue_name='queue_slow', max_retries=0)
        def do_work_slow():
            time.sleep(0.05)

        do_work_slow.send()
        self.broker.join(do_work_slow.queue_name)
        self.worker.join()

        # tasks in the database
        tasks = Task.tasks.all()
        self.assertEqual(3, tasks.count())

    def test_valid_form(self):
        form = DramatiqTimelineChartForm(data=dict(
            start_date=self.utcnow - datetime.timedelta(minutes=1),
            end_date=self.utcnow + datetime.timedelta(minutes=1),
            queue='',
            actor='',
            status=Task.STATUS_DONE,
        ))
        # form validation
        self.assertTrue(form.is_valid())
        data = form.get_chart_data()
        # empty qs
        self.assertFalse(data['empty_qs'])
        # chart data
        chart_data = json.loads(data['chart_data'])
        self.assertEqual(3, len(chart_data))
        self.assertEqual('do_work_slow', chart_data[0]['actor'])
        self.assertEqual('do_work_fast', chart_data[1]['actor'])
        self.assertEqual('do_work_fast', chart_data[2]['actor'])
        # filter data
        filter_data = json.loads(data['filter_data'])
        self.assertEqual(5, len(filter_data))
        self.assertEqual('done', filter_data['status'])


    def test_invalid_forms(self):
        # end date is greater than start date
        form = DramatiqTimelineChartForm(data=dict(
            start_date=self.utcnow,
            end_date=self.utcnow,
        ))
        self.assertFalse(form.is_valid())
        self.assertEqual(['The period start date is greater than or equal to the period end date'],
                         form.non_field_errors())

        # maximum date range is greater than 3 days
        form = DramatiqTimelineChartForm(data=dict(
            start_date=self.utcnow - datetime.timedelta(days=2),
            end_date=self.utcnow + datetime.timedelta(days=2),
        ))
        self.assertFalse(form.is_valid())
        self.assertEqual(['The maximum date range is 3 days'], form.non_field_errors())

    def test_filters(self):
        # queue
        form = DramatiqTimelineChartForm(data=dict(
            start_date=self.utcnow - datetime.timedelta(minutes=1),
            end_date=self.utcnow + datetime.timedelta(minutes=1),
            queue='queue_fast',
        ))
        self.assertTrue(form.is_valid())
        data = form.get_chart_data()
        self.assertFalse(data['empty_qs'])
        chart_data = json.loads(data['chart_data'])
        self.assertEqual(2, len(chart_data))
        self.assertEqual('do_work_fast', chart_data[0]['actor'])
        self.assertEqual('do_work_fast', chart_data[0]['actor'])

        # actor
        form = DramatiqTimelineChartForm(data=dict(
            start_date=self.utcnow - datetime.timedelta(minutes=1),
            end_date=self.utcnow + datetime.timedelta(minutes=1),
            actor='do_work_slow',
        ))
        self.assertTrue(form.is_valid())
        data = form.get_chart_data()
        self.assertFalse(data['empty_qs'])
        chart_data = json.loads(data['chart_data'])
        self.assertEqual(1, len(chart_data))
        self.assertEqual('do_work_slow', chart_data[0]['actor'])

        # status
        form = DramatiqTimelineChartForm(data=dict(
            start_date=self.utcnow - datetime.timedelta(minutes=1),
            end_date=self.utcnow + datetime.timedelta(minutes=1),
            status=Task.STATUS_RUNNING,
        ))
        self.assertTrue(form.is_valid())
        data = form.get_chart_data()
        self.assertTrue(data['empty_qs'])

        # date period
        task_slow = Task.tasks.filter(actor_name='do_work_slow').values('updated_at', 'created_at')[0]
        form = DramatiqTimelineChartForm(data=dict(
            start_date=task_slow['created_at'] + datetime.timedelta(seconds=0.01),
            end_date=task_slow['updated_at'] - datetime.timedelta(seconds=0.01),
        ))
        self.assertTrue(form.is_valid())
        data = form.get_chart_data()
        self.assertFalse(data['empty_qs'])
        dt_format = "%Y-%m-%d %H:%M:%S.%f"
        chart_data = json.loads(data['chart_data'])
        self.assertEqual(1, len(chart_data))
        self.assertEqual('do_work_slow', chart_data[0]['actor'])
        self.assertEqual(task_slow['created_at'].strftime(dt_format), chart_data[0]['start'])
        self.assertEqual(task_slow['updated_at'].strftime(dt_format), chart_data[0]['end'])
