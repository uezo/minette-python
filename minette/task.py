""" Task scheduler """
from threading import Thread
import traceback
import schedule
import time


class Task:
    """
    Base class of tasks

    Attributes
    ----------
    helpers : dict
        Helper objects and functions
    logger : Logger
        Logger
    config : Config
        Configuration
    timezone : timezone
        Timezone
    connection_provider : ConnectionProvider
        Connection provider to use database in each tasks
    """
    def __init__(self, helpers, logger, config, timezone, connection_provider):
        """
        Parameters
        ----------
        helpers : dict
            Helper objects and functions
        logger : Logger
            Logger
        config : Config
            Configuration
        timezone : timezone
            Timezone
        connection_provider : ConnectionProvider
            Connection provider to use database in each tasks
        """
        self.helpers = helpers
        self.logger = logger
        self.config = config
        self.timezone = timezone
        self.connection_provider = connection_provider

    def do(self, connection):
        """
        Override this method to do what you want as scheduled task

        Parameters
        ----------
        connection : Connection
            Connection
        """
        pass

    def main(self):
        """
        Main logic called by scheduler
        """
        connection = None
        try:
            connection = self.connection_provider.get_connection() if self.connection_provider else None
            self.do(connection)
        except Exception as ex:
            self.logger.error("error occured in task: " + str(ex) + "\n" + traceback.format_exc())
        finally:
            if connection:
                connection.close()


class Scheduler(Thread):
    """
    Base class of task scheduler

    Attributes
    ----------
    helpers : dict
        Helper objects and functions
    logger : Logger
        Logger
    config : Config
        Configuration
    timezone : timezone
        Timezone
    connection_provider : ConnectionProvider
        Connection provider to use database in each tasks
    schedule : schedule
        schedule module
    """
    def __init__(self, helpers=None, logger=None, config=None, timezone=None, connection_provider=None):
        """
        Parameters
        ----------
        helpers : dict, default None
            Helper objects and functions
        logger : Logger, default None
            Logger
        config : Config, default None
            Configuration
        timezone : timezone, default None
            Timezone
        connection_provider : ConnectionProvider, default None
            Connection provider to use database in each tasks
        """
        super().__init__()
        self.helpers = helpers if helpers else {}
        self.logger = logger
        self.config = config
        self.timezone = timezone
        self.connection_provider = connection_provider
        self.schedule = schedule

    def create_task(self, task_class):
        """
        Create and get callable function of task

        Parameters
        ----------
        task_class : type
            Class of task

        Returns
        -------
        task_main_method : function
            Callable interface of task
        """
        return task_class(self.helpers, self.logger, self.config, self.timezone, self.connection_provider).main

    def register_tasks(self):
        """
        Override this method to register tasks like below;

        `self.schedule.every().minute.do(self.create_task(MyTask))`
        `self.schedule.every().hour.do(self.create_task(YourTask))`
        """
        pass

    def run(self):
        """
        Start scheduler
        """
        while True:
            self.schedule.run_pending()
            time.sleep(1)
