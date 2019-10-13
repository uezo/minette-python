import pytest
from pytz import timezone
from concurrent.futures import ThreadPoolExecutor

from minette import Task, Scheduler


class MyTask(Task):
    def do(self, arg1, arg2):
        print(arg1, arg2)


class StopTask(Task):
    def do(self, sc):
        sc.stop()


class MyClass:
    def do(self, arg1):
        print(arg1)


def print_something():
    print("something")


def test_init_task():
    task = Task(timezone=timezone("Asia/Tokyo"))
    assert task.timezone == timezone("Asia/Tokyo")


def test_do_task():
    task = Task()
    task.do()


def test_init_scheduler():
    sc = Scheduler(timezone=timezone("Asia/Tokyo"), threads=2)
    assert sc.timezone == timezone("Asia/Tokyo")
    assert sc.threads == 2
    assert isinstance(sc.executor, ThreadPoolExecutor)
    assert sc.is_running is False


def test_scheduler_create_task():
    # subclass of task
    sc = Scheduler(timezone=timezone("Asia/Tokyo"))
    task = sc.create_task(MyTask)
    assert callable(task)
    assert not isinstance(task, MyTask)
    assert task is not MyTask

    # other class
    with pytest.raises(TypeError):
        task = sc.create_task(MyClass)

    # callable
    task = sc.create_task(print_something)
    assert task is print_something

    # callable (instance method)
    mc = MyClass()
    task = sc.create_task(mc.do)
    assert task == mc.do

    # other
    with pytest.raises(TypeError):
        task = sc.create_task(MyClass())


def test_scheduler_register_task():
    sc = Scheduler()
    sc.every_seconds(print_something)
    sc.every_minutes(print_something, 2)
    sc.every_hours(MyTask, arg1="val1", arg2="val2")
    sc.every_days(MyTask, 4, "val1", "val2")


def test_scheduler_start_stop():
    sc = Scheduler()
    sc.every_seconds(MyTask, arg1="val1", arg2="val2")
    sc.every_seconds(StopTask, 3, sc=sc)
    sc.start()
    assert sc.is_running is False
