# console.py

class ConsoleView:
    def __init__(self, controller):
        self.controller = controller

    def display_message(self, message):
        print(message)

    def get_user_input(self):
        return input("Enter your command: ")

class ConsoleController:
    def __init__(self, model):
        self.model = model
        self.view = ConsoleView(self)

    def process_input(self):
        user_input = self.view.get_user_input()
        result = self.model.process_command(user_input)
        self.view.display_message(result)

class ConsoleModel:
    def process_command(self, command):
        # Example business logic
        if command == 'hello':
            return 'Hello, world!'
        else:
            return 'Unknown command'

def main():
    model = ConsoleModel()
    controller = ConsoleController(model)
    while True:
        controller.process_input()

if __name__ == "__main__":
    main()