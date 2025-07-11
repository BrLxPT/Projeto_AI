from apscheduler.schedulers.background import BackgroundScheduler
from main import evaluate_rule

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(evaluate_rule, 'internal', minutes=10)
    scheduler.start()