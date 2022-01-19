import dramatiq
import time

from .models import Job


@dramatiq.actor(queue_name='queue', store_results=True)
def process_job(job_id):
    job = Job.objects.get(pk=job_id)
    job.process()

    job.status = Job.STATUS_DONE
    job.save()
