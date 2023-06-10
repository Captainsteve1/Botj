import logging
import queue
import threading
import traceback
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Tuple, Union

log = logging.getLogger(__name__)

class task_complete(NamedTuple):
    ret: Any = None
    exc: str = False

def asyncthread(
    func: Callable,
    daemon: Optional[bool] = True,
    auto_start: Optional[bool] = False
) -> threading.Thread:
    def wrapped_func(Queue: queue.Queue, *args, **kwargs) -> None:
        try:
            return Queue.put(task_complete(ret=func(*args, **kwargs), exc=False))
        except Exception:
            return Queue.put(task_complete(ret=None, exc=traceback.format_exc()))

    def wrap(*args, **kwargs) -> threading.Thread:
        Queue = queue.Queue()
        thread_task = threading.Thread(target=wrapped_func, args=(Queue,) + args, kwargs=kwargs)
        thread_task.daemon = daemon
        if auto_start: thread_task.start()
        thread_task.result_queue = Queue
        return thread_task

    return wrap

def processor_asynced(
    items: Union[Any, List[Any]],
    max_threads: Optional[bool] = 0
) -> None:
    items = [items] if not isinstance(items, list) else items
    chunks = [items[x:x + max_threads] for x in range(0, len(items), max_threads)] if max_threads else [items]
    for chunk in chunks:
        for item in chunk:
            item.start()
        for item in chunk:
            yield item.result_queue.get()
