# dashboard/app_1771891133.py

class AppFactory:
    @staticmethod
    def create_app(config):
        if config.get('app_type') == 'type_a':
            return AppTypeA(config)
        elif config.get('app_type') == 'type_b':
            return AppTypeB(config)
        else:
            raise ValueError("Unknown app type")

class AppTypeA:
    def __init__(self, config):
        self.config = config

    def run(self):
        # Logic for AppTypeA
        pass

class AppTypeB:
    def __init__(self, config):
        self.config = config

    def run(self):
        # Logic for AppTypeB
        pass

# Usage in app.py or other entry points
if __name__ == '__main__':
    import json
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    app = AppFactory.create_app(config)
    app.run()