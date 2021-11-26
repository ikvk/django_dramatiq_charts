import time
import json
import datetime

import dramatiq

from django_dramatiq.models import Task
from django_dramatiq_charts.forms import DramatiqLoadChartForm


class TestDramatiqLoadChart():

    def test_form(self):
        # todo create tasks

        # And form context for chart built for 3 items
        utcnow = datetime.datetime.utcnow()
        form = DramatiqLoadChartForm(data=dict(
            start_date=utcnow - datetime.timedelta(minutes=1),
            end_date=utcnow + datetime.timedelta(minutes=1),
            time_interval=10,
            queue='',
            actor='',
            status=Task.STATUS_DONE
        ))
        self.assertTrue(form.is_valid())
        chart_data = form.get_chart_data()
        self.assertIs(str, type(chart_data['chart_title']))
        self.assertEqual('225', chart_data['chart_height'])
        self.assertEqual(False, chart_data['empty_qs'])
        self.assertEqual(["do_work"], json.loads(chart_data['categories']))
        self.assertEqual(13, len(json.loads(chart_data['dates'])))
        working_actors_count = json.loads(chart_data['working_actors_count'])
        self.assertEqual(13, len(working_actors_count[0]))
        self.assertEqual(3, sum(i for i in working_actors_count[0] if i))
