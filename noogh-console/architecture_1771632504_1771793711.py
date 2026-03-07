# noogh-console/architecture_1771632504.py

class Context:
    def __init__(self, data):
        self.data = data

class ContextFactory:
    @staticmethod
    def create_context(data_type, data):
        if data_type == 'type1':
            return Context({'data': data, 'type': 'type1'})
        elif data_type == 'type2':
            return Context({'data': data, 'type': 'type2'})
        else:
            raise ValueError("Unknown context type")

# Usage example
if __name__ == '__main__':
    context = ContextFactory.create_context('type1', {'key': 'value'})
    print(context.data)