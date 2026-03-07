# Update sandbox_service/main.py to use the factory

from app.core.factory import SandboxFactory

def main():
    sandbox = SandboxFactory.create_sandbox("advanced")
    sandbox.process()

if __name__ == '__main__':
    main()