from abc import ABC, abstractmethod
import json

class Command(ABC):
    @abstractmethod
    def execute(self):
        pass

class SetMemoryCommand(Command):
    def __init__(self, memory_storage, key, value):
        self.memory_storage = memory_storage
        self.key = key
        self.value = value

    def execute(self):
        return self.memory_storage.set(self.key, self.value)

class GetMemoryCommand(Command):
    def __init__(self, memory_storage, key):
        self.memory_storage = memory_storage
        self.key = key

    def execute(self):
        return self.memory_storage.get(self.key)

class DeleteMemoryCommand(Command):
    def __init__(self, memory_storage, key):
        self.memory_storage = memory_storage
        self.key = key

    def execute(self):
        return self.memory_storage.delete(self.key)

class MemoryStorage:
    def set(self, key, value):
        # Logic to store the data in memory
        print(f"Setting {key} to {value}")
        return True

    def get(self, key):
        # Logic to retrieve the data from memory
        print(f"Getting {key}")
        return "some_value"

    def delete(self, key):
        # Logic to delete the data from memory
        print(f"Deleting {key}")
        return True

class MemoryCommandInvoker:
    def __init__(self, memory_storage):
        self.memory_storage = memory_storage
        self.commands = []

    def add_command(self, command):
        self.commands.append(command)

    def execute_all_commands(self):
        results = []
        for command in self.commands:
            result = command.execute()
            results.append(result)
        return results

# Example usage
if __name__ == '__main__':
    memory_storage = MemoryStorage()
    invoker = MemoryCommandInvoker(memory_storage)

    set_command = SetMemoryCommand(memory_storage, 'key1', 'value1')
    get_command = GetMemoryCommand(memory_storage, 'key1')
    delete_command = DeleteMemoryCommand(memory_storage, 'key1')

    invoker.add_command(set_command)
    invoker.add_command(get_command)
    invoker.add_command(delete_command)

    results = invoker.execute_all_commands()
    print(results)