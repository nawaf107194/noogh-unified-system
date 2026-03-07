import os
import inspect

class CodeGenerator:
    def __init__(self, output_directory='.'):
        self.output_directory = output_directory
        if not os.path.exists(self.output_directory):
            os.makedirs(self.output_directory)

    def generate_class(self, class_name, methods=None):
        """
        Generate a class with the given name and optional methods.
        """
        class_template = f"class {class_name}:\n"
        if methods:
            for method in methods:
                class_template += f"    def {method}(self):\n        pass\n"
        self._write_to_file(f"{class_name}.py", class_template)
        return class_template

    def generate_method(self, method_name):
        """
        Generate a method stub.
        """
        method_template = f"def {method_name}():\n    pass\n"
        return method_template

    def generate_file_structure(self, file_name, content):
        """
        Generate a file with the given content.
        """
        self._write_to_file(file_name, content)
        return content

    def _write_to_file(self, file_name, content):
        """
        Write content to a file in the specified directory.
        """
        full_path = os.path.join(self.output_directory, file_name)
        with open(full_path, 'w') as file:
            file.write(content)

# Example usage
if __name__ == "__main__":
    generator = CodeGenerator(output_directory='generated_code')
    class_content = generator.generate_class('ExampleClass', methods=['initialize', 'process'])
    print(class_content)
    method_content = generator.generate_method('example_method')
    print(method_content)
    file_content = generator.generate_file_structure('example_file.py', method_content)
    print(file_content)