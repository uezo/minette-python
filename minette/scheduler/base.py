""" Scheduler for periodic tasks """
import traceback
from logging import getLogger
import schedule
import time
from concurrent.futures import ThreadPoolExecutor


class Task:
    """
    Base class of tasks

    Attributes
    ----------
    config : minette.Config
        Configuration
    timezone : pytz.timezone
        Timezone
    logger : logging.Logger
        Logger
    connection_provider : minette.ConnectionProvider
        Connection provider to use database in each tasks
    """
    def __init__(self, config=None, timezone=None, logger=None,
                 connection_provider=None, **kwargs):
        """
        Parameters
        ----------
        config : minette.Config, default None
            Configuration
        timezone : pytz.timezone, default None
            Timezone
        logger : logging.Logger, default None
            Logger
        connection_provider : minette.ConnectionProvider
            Connection provider to use database in each tasks
        """
        self.config = config
        self.timezone = timezone
        self.logger = logger or getLogger(__name__)
        self.connection_provider = connection_provider

    def do(self, **kwargs):
        """
        Implement your periodic task

        """
        self.logger.error("Task is not implemented")


class Scheduler:
    """
    Task scheduler for periodic tasks

    Examples
    --------
    To start doing scheduled tasks, just create `Scheduler` instance
    and register task(s), then call `start()`

    >>> my_scheduler = MyScheduler()
    >>> my_scheduler.every_minutes(MyTask)
    >>> my_scheduler.start()

    To register tasks, this class provides shortcut methods.
    Each tasks run at worker threads.

    >>> my_scheduler.every_minutes(MyTask)
    >>> my_scheduler.every_seconds(MyTask, seconds=5)
    >>> my_scheduler.every_seconds(MyTask, seconds=5, arg1="val1", arg2="val2")

    You can also use internal `schedule` to register tasks
    then the tasks run at main thread.

    >>> my_scheduler.schedule.every().minute.do(self.create_task(MyTask))
    >>> my_scheduler.schedule.every().hour.do(self.create_task(YourTask))

    Notes
    -----
    How to execute jobs in parallel?
    https://schedule.readthedocs.io/en/stable/faq.html#how-to-execute-jobs-in-parallel

    Attributes
    ----------
    config : minette.Config
        Configuration
    timezone : pytz.timezone
        Timezone
    logger : logging.Logger
        Logger
    threads : int
        Number of worker threads to process tasks
    connection_provider : minette.ConnectionProvider
        Connection provider to use database in each tasks
    schedule : schedule
        schedule module
    executor : concurrent.futures.ThreadPoolExecutor
        Executor to run tasks at worker threads
    """

    def __init__(self, config=None, timezone=None, logger=None, threads=None,
                 connection_provider=None, **kwargs):
        """
        Parameters
        ----------
        config : minette.Config, default None
            Configuration
        timezone : pytz.timezone, default None
            Timezone
        logger : logging.Logger, default None
            Logger
        threads : int, default None
            Number of worker threads to process tasks
        connection_provider : ConnectionProvider, default None
            Connection provider to use database in each tasks
        """
        self.config = config
        self.timezone = timezone
        self.logger = logger or getLogger(__name__)
        self.threads = threads
        self.connection_provider = connection_provider
        self.schedule = schedule
        self.executor = ThreadPoolExecutor(
            max_workers=self.threads, thread_name_prefix="SchedulerThread")
        self._is_running = False

    @property
    def is_running(self):
        return self._is_running

    def create_task(self, task_class, **kwargs):
        """
        Create and return callable function of task

        Parameters
        ----------
        task_class : type
            Class of task

        Returns
        -------
        task_method : callable
            Callable interface of task
        """
        if isinstance(task_class, type):
            if issubclass(task_class, Task):
                return task_class(
                    config=self.config,
                    timezone=self.timezone,
                    logger=self.logger,
                    connection_provider=self.connection_provider,
                    **kwargs).do
            else:
                raise TypeError(
                    "task_class should be a subclass of minette.Task " +
                    "or callable, not {}".format(task_class.__name__))

        elif callable(task_class):
            return task_class

        else:
            raise TypeError(
                "task_class should be a subclass of minette.Task " +
                "or callable, not the instance of {}".format(
                    task_class.__class__.__name__))

    def every_seconds(self, task, seconds=1, *args, **kwargs):
        self.schedule.every(seconds).seconds.do(
            self.executor.submit, self.create_task(task), *args, **kwargs)

    def every_minutes(self, task, minutes=1, *args, **kwargs):
        self.schedule.every(minutes).minutes.do(
            self.executor.submit, self.create_task(task), *args, **kwargs)

    def every_hours(self, task, hours=1, *args, **kwargs):
        self.schedule.every(hours).hours.do(
            self.executor.submit, self.create_task(task), *args, **kwargs)

    def every_days(self, task, days=1, *args, **kwargs):
        self.schedule.every(days).days.do(
            self.executor.submit, self.create_task(task), *args, **kwargs)

    def start(self):
        """
        Start scheduler
        """
        self.logger.info("Task scheduler started")
        self._is_running = True
        while self._is_running:
            self.schedule.run_pending()
            time.sleep(1)
        self.logger.info("Task scheduler stopped")

    def stop(self):
        """
        Stop scheduler
        """
        self._is_running = False
