import json
from datetime import datetime

from django_dramatiq.models import Task
from django.test import TransactionTestCase
from django_dramatiq_charts.forms import DramatiqLoadChartForm, DramatiqTimelineChartForm

_fixture_dataset = 'fixtures/dataset.json'


class TestDramatiqLoadChart(TransactionTestCase):
    fixtures = [_fixture_dataset]

    def test_valid_form(self):
        # tasks in the database
        tasks = Task.tasks.all()
        self.assertEqual(29, tasks.count())

        # form validation
        form = DramatiqLoadChartForm(data=dict(
            start_date=datetime(2022, 1, 1, 1, 0, 0),
            end_date=datetime(2022, 1, 1, 1, 1, 0),
            time_interval=10,
            queue=[],
            actor=[],
            status=[Task.STATUS_DONE],
        ))
        self.assertTrue(form.is_valid())

        # empty qs
        data = form.get_chart_data()
        self.assertFalse(data['empty_qs'])

        # chart height
        self.assertEqual('320', data['chart_height'])

        # categories
        self.assertEqual(['specific_tasks', 'sequential_tasks', 'parallel_tasks', 'different_status'],
                         json.loads(data['categories']))

        # dates
        self.assertEqual(7, len(json.loads(data['dates'])))

        # working actors count
        self.assertEqual(
            [
                [None, None, None, None, 1, None, None],
                [1, 1, 1, 1, 2, 1, 1],
                [1, 1, 6, 9, 7, 1, 1],
                [None, 1, None, None, None, None, None]
            ], json.loads(data['working_actors_count'])
        )

    def test_invalid_forms(self):
        # end date is greater than start date
        form = DramatiqLoadChartForm(data=dict(
            start_date=datetime(2022, 1, 1, 1, 1, 0),
            end_date=datetime(2022, 1, 1, 1, 0, 0),
        ))
        self.assertFalse(form.is_valid())
        self.assertEqual(['The period start date is greater than or equal to the period end date'],
                         form.non_field_errors())

        # maximum date range is greater than 7 days
        form = DramatiqLoadChartForm(data=dict(
            start_date=datetime(2022, 1, 1, 1, 0, 0),
            end_date=datetime(2022, 1, 9, 1, 0, 0),
        ))
        self.assertFalse(form.is_valid())
        self.assertEqual(['The maximum date range is 7 days'], form.non_field_errors())

        # time interval is too long
        form = DramatiqLoadChartForm(data=dict(
            start_date=datetime(2022, 1, 1, 1, 0, 0),
            end_date=datetime(2022, 1, 1, 1, 1, 0),
            time_interval=31,
        ))
        self.assertFalse(form.is_valid())
        self.assertEqual(['Time interval is too long'], form.non_field_errors())

        # time interval is zero
        form = DramatiqLoadChartForm(data=dict(
            start_date=datetime(2022, 1, 1, 1, 0, 0),
            end_date=datetime(2022, 1, 1, 1, 1, 0),
            time_interval=0,
        ))
        self.assertFalse(form.is_valid())
        self.assertEqual(['Ensure this value is greater than or equal to 1.'], form.errors['time_interval'])

    def test_filters(self):
        # queue
        form = DramatiqLoadChartForm(data=dict(
            start_date=datetime(2022, 1, 1, 1, 0, 0),
            end_date=datetime(2022, 1, 1, 1, 1, 0),
            queue=['queue_specific'],
            time_interval=10,
        ))
        self.assertTrue(form.is_valid())
        data = form.get_chart_data()
        self.assertFalse(data['empty_qs'])
        self.assertEqual(['specific_tasks'], json.loads(data['categories']))
        self.assertEqual([[None, None, None, None, 1, None, None]], json.loads(data['working_actors_count']))

        # actor
        form = DramatiqLoadChartForm(data=dict(
            start_date=datetime(2022, 1, 1, 1, 0, 0),
            end_date=datetime(2022, 1, 1, 1, 1, 0),
            actor=['different_status'],
            time_interval=10,
        ))
        self.assertTrue(form.is_valid())
        data = form.get_chart_data()
        self.assertFalse(data['empty_qs'])
        self.assertEqual(['different_status'], json.loads(data['categories']))
        self.assertEqual([[None, 4, 1, 1, 1, None, 1]], json.loads(data['working_actors_count']))

        # status
        form = DramatiqLoadChartForm(data=dict(
            start_date=datetime(2022, 1, 1, 1, 0, 0),
            end_date=datetime(2022, 1, 1, 1, 1, 0),
            status=[Task.STATUS_RUNNING],
            time_interval=10,
        ))
        self.assertTrue(form.is_valid())
        data = form.get_chart_data()
        self.assertFalse(data['empty_qs'])
        self.assertEqual(['different_status'], json.loads(data['categories']))
        self.assertEqual([[None, 2, None, None, 1, None, None]], json.loads(data['working_actors_count']))

        # time interval
        form = DramatiqLoadChartForm(data=dict(
            start_date=datetime(2022, 1, 1, 1, 0, 0),
            end_date=datetime(2022, 1, 1, 1, 1, 0),
            time_interval=1,
        ))
        self.assertTrue(form.is_valid())
        data = form.get_chart_data()
        self.assertFalse(data['empty_qs'])
        self.assertEqual(61, len(json.loads(data['dates'])))

        # date period
        form = DramatiqLoadChartForm(data=dict(
            start_date=datetime(2022, 1, 1, 0, 0, 0),
            end_date=datetime(2022, 1, 1, 1, 1, 0),
            time_interval=10,
        ))
        self.assertTrue(form.is_valid())
        data = form.get_chart_data()
        self.assertFalse(data['empty_qs'])
        self.assertEqual(5, len(json.loads(data['categories'])))
        self.assertIn('external_tasks', json.loads(data['categories']))


class TestDramatiqTimelineChart(TransactionTestCase):
    fixtures = [_fixture_dataset]

    def test_valid_form(self):
        # tasks in the database
        tasks = Task.tasks.all()
        self.assertEqual(29, tasks.count())

        # form validation
        form = DramatiqTimelineChartForm(data=dict(
            start_date=datetime(2022, 1, 1, 1, 0, 0),
            end_date=datetime(2022, 1, 1, 1, 1, 0),
            queue=[],
            actor=[],
            status=[],
        ))
        self.assertTrue(form.is_valid())

        # empty qs
        data = form.get_chart_data()
        self.assertFalse(data['empty_qs'])

        # chart data
        dt_format = "%Y-%m-%d %H:%M:%S.%f"
        chart_data = json.loads(data['chart_data'])
        self.assertEqual(27, len(chart_data))
        self.assertEqual('sequential_tasks', chart_data[-1]['actor'])
        self.assertEqual('done', chart_data[-1]['status'])
        self.assertEqual(17000, chart_data[-1]['duration'])
        self.assertEqual(datetime(2022, 1, 1, 0, 59, 50), datetime.strptime(chart_data[-1]['start'], dt_format))
        self.assertEqual(datetime(2022, 1, 1, 1, 0, 7), datetime.strptime(chart_data[-1]['end'], dt_format))

        # filter data
        dt_format = "%Y-%m-%d %H:%M:%S"
        filter_data = json.loads(data['filter_data'])
        self.assertEqual(5, len(filter_data))
        self.assertEqual(datetime(2022, 1, 1, 1, 0, 0), datetime.strptime(filter_data['start_date'], dt_format))
        self.assertEqual(datetime(2022, 1, 1, 1, 1, 0), datetime.strptime(filter_data['end_date'], dt_format))
        self.assertFalse(filter_data['actor'])
        self.assertFalse(filter_data['queue'])
        self.assertFalse(filter_data['status'])

    def test_invalid_forms(self):
        # end date is greater than start date
        form = DramatiqTimelineChartForm(data=dict(
            start_date=datetime(2022, 1, 1, 1, 1, 0),
            end_date=datetime(2022, 1, 1, 1, 0, 0),
        ))
        self.assertFalse(form.is_valid())
        self.assertEqual(['The period start date is greater than or equal to the period end date'],
                         form.non_field_errors())

        # maximum date range is greater than 7 days
        form = DramatiqTimelineChartForm(data=dict(
            start_date=datetime(2022, 1, 1, 0, 0, 0),
            end_date=datetime(2022, 1, 9, 0, 0, 0),
        ))
        self.assertFalse(form.is_valid())
        self.assertEqual(['The maximum date range is 7 days'], form.non_field_errors())

    def test_filters(self):
        # queue
        form = DramatiqTimelineChartForm(data=dict(
            start_date=datetime(2022, 1, 1, 1, 0, 0),
            end_date=datetime(2022, 1, 1, 1, 1, 0),
            queue=['queue_specific'],
        ))
        self.assertTrue(form.is_valid())
        data = form.get_chart_data()
        self.assertFalse(data['empty_qs'])
        chart_data = json.loads(data['chart_data'])
        self.assertEqual(3, len(chart_data))
        self.assertEqual({'specific_tasks'}, {task['actor'] for task in chart_data})

        # actor
        form = DramatiqTimelineChartForm(data=dict(
            start_date=datetime(2022, 1, 1, 1, 0, 0),
            end_date=datetime(2022, 1, 1, 1, 1, 0),
            actor=['different_status'],
        ))
        self.assertTrue(form.is_valid())
        data = form.get_chart_data()
        self.assertFalse(data['empty_qs'])
        chart_data = json.loads(data['chart_data'])
        self.assertEqual(8, len(chart_data))
        self.assertEqual({'different_status'}, {task['actor'] for task in chart_data})

        # status
        form = DramatiqTimelineChartForm(data=dict(
            start_date=datetime(2022, 1, 1, 1, 0, 0),
            end_date=datetime(2022, 1, 1, 1, 1, 0),
            status=[Task.STATUS_RUNNING],
        ))
        self.assertTrue(form.is_valid())
        data = form.get_chart_data()
        self.assertFalse(data['empty_qs'])
        chart_data = json.loads(data['chart_data'])
        self.assertEqual(3, len(chart_data))
        self.assertEqual({'running'}, {task['status'] for task in chart_data})

        # date period
        form = DramatiqTimelineChartForm(data=dict(
            start_date=datetime(2022, 1, 1, 0, 0, 0),
            end_date=datetime(2022, 1, 1, 1, 1, 0),
        ))
        self.assertTrue(form.is_valid())
        data = form.get_chart_data()
        self.assertFalse(data['empty_qs'])
        chart_data = json.loads(data['chart_data'])
        self.assertEqual(28, len(chart_data))
        self.assertIn('external_tasks', {task['actor'] for task in chart_data})
