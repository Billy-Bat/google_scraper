from typing import Callable, Dict, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import perf_counter


def time_it(func: Callable) -> Callable:
    def timer_decorator(*args, **kwargs):
        start = perf_counter()
        func_result: Any = func(*args, **kwargs)
        end = perf_counter()
        print(f"function {func.__name__} ran in: {end-start} sec")
        return func_result

    return timer_decorator


@time_it
def multithread_callable(
    func: Callable,
    kwargs_list: List[Dict[str, Any]] = None,
    workers=64,
):
    results = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(func, **kwargs) for kwargs in kwargs_list]
        print(f"Submitted {executor._max_workers} workers")
        for future in as_completed(futures):
            results.append(future.result())
    return results
