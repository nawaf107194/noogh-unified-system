# coordinator.py

class Component:
    def __init__(self, mediator):
        self.mediator = mediator

class Mediator:
    def __init__(self):
        self.components = []
    
    def register_component(self, component):
        self.components.append(component)
    
    def notify(self, sender, event):
        # Implement central notification logic here
        pass

class ConcreteComponent(Component):
    def do_something(self):
        # Trigger an event through mediator
        self.mediator.notify(self, "SOME_EVENT")

# Usage example:
if __name__ == '__main__':
    mediator = Mediator()
    component = ConcreteComponent(mediator)
    mediator.register_component(component)
    component.do_something()