import cProfile
import pstats
import io
from functools import wraps

class PerformanceProfiler:
    def __init__(self, filename=None):
        self.filename = filename
        self.pr = None

    def start(self):
        self.pr = cProfile.Profile()
        self.pr.enable()

    def stop(self):
        if self.pr:
            self.pr.disable()
            s = io.StringIO()
            sortby = 'cumulative'
            ps = pstats.Stats(self.pr, stream=s).sort_stats(sortby)
            ps.print_stats()
            print(s.getvalue())
            if self.filename:
                with open(self.filename, 'w') as f:
                    ps.dump_stats(f.name)

    def profile(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            self.start()
            result = func(*args, **kwargs)
            self.stop()
            return result
        return wrapper

if __name__ == "__main__":
    profiler = PerformanceProfiler(filename='performance_profile.log')

    @profiler.profile
    def some_expensive_function():
        sum([i * i for i in range(10000)])

    some_expensive_function()