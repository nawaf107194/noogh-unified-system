import os
import ast
import networkx as nx
import matplotlib.pyplot as plt

class DependencyGraphGenerator:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.graph = nx.DiGraph()

    def parse_module(self, module_path):
        with open(module_path, 'r') as file:
            tree = ast.parse(file.read())
        return [node.id for node in ast.walk(tree) if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom)]

    def build_graph(self):
        for root, dirs, files in os.walk(self.root_dir):
            for file in files:
                if file.endswith('.py'):
                    full_path = os.path.join(root, file)
                    dependencies = self.parse_module(full_path)
                    for dependency in dependencies:
                        self.graph.add_edge(full_path, dependency)
    
    def visualize(self, output_path='dependency_graph.png'):
        pos = nx.spring_layout(self.graph)
        nx.draw(self.graph, pos, with_labels=True, arrows=True, node_size=3000, font_size=8, node_color="skyblue", edge_color="black")
        plt.savefig(output_path)
        plt.show()

# Example usage
if __name__ == "__main__":
    generator = DependencyGraphGenerator('path/to/project_root')
    generator.build_graph()
    generator.visualize()