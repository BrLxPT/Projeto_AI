import schedule
import time
from threading import Thread

class TaskScheduler:
    """Agendador de tarefas recorrentes"""
    
    def __init__(self):
        self.jobs = {}
    
    def add_job(self, job_id, interval, task, *args, **kwargs):
        """
        Adiciona uma nova tarefa agendada
        :param job_id: Identificador único da tarefa
        :param interval: Intervalo no formato '10 minutes' ou '1 hour'
        :param task: Função a ser executada
        :param args: Argumentos posicionais para a função
        :param kwargs: Argumentos nomeados para a função
        """
        # Remove job existente se houver
        self.remove_job(job_id)
        
        # Adiciona novo job
        job = schedule.every(interval).do(task, *args, **kwargs)
        self.jobs[job_id] = job
    
    def remove_job(self, job_id):
        """Remove uma tarefa agendada"""
        if job_id in self.jobs:
            schedule.cancel_job(self.jobs[job_id])
            del self.jobs[job_id]
    
    def run_pending(self):
        """Executa tarefas pendentes em loop"""
        while True:
            schedule.run_pending()
            time.sleep(1)
    
    def start(self):
        """Inicia o scheduler em uma thread separada"""
        thread = Thread(target=self.run_pending, daemon=True)
        thread.start()