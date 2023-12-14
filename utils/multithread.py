from typing import Callable, Dict, List, Any, Generator
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import perf_counter
from functools import wraps


def time_it(func: Callable) -> Callable:
    @wraps(func)
    def timer_decorator(*args, **kwargs):
        start = perf_counter()
        func_result: Any = func(*args, **kwargs)
        end = perf_counter()
        print(f"function {func.__name__} ran in: {end-start} sec")
        return func_result

    return timer_decorator


def chunks_input(lst, n) -> Generator:
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


@time_it
def multithread_callable(
    func: Callable,
    kwargs_list: List[Dict[str, Any]] = None,
    nb_workers=64,
):
    """ """
    results = []
    with ThreadPoolExecutor(max_workers=nb_workers) as executor:
        futures = [executor.submit(func, **kwargs) for kwargs in kwargs_list]
        print(f"Submitted {executor._max_workers} workers")
        for future in as_completed(futures):
            results.append(future.result())
    return results
