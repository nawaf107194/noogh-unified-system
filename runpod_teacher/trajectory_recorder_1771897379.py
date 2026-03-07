from abc import ABC, abstractmethod

# Subject class
class TrajectorySubject(ABC):
    _observers = []

    def attach(self, observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer):
        try:
            self._observers.remove(observer)
        except ValueError:
            pass

    def notify(self):
        for observer in self._observers:
            observer.update(self)

# Observer class
class TrajectoryObserver(ABC):
    @abstractmethod
    def update(self, subject):
        pass

# Concrete implementation of subject and observers
class TrajectoryRecorder(TrajectorySubject):
    def __init__(self):
        super().__init__()
        self._trajectory_data = []

    def record_trajectory(self, data):
        self._trajectory_data.append(data)
        self.notify()

class DataAnalyzer(TrajectoryObserver):
    def update(self, subject):
        print("DataAnalyzer received trajectory update:", subject._trajectory_data)

if __name__ == '__main__':
    recorder = TrajectoryRecorder()
    analyzer = DataAnalyzer()

    recorder.attach(analyzer)

    recorder.record_trajectory({"step": 1, "action": "start"})
    recorder.record_trajectory({"step": 2, "action": "move"})