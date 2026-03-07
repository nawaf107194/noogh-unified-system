import pytest

from unified_core.core.spatial_specialist import SpatialSpecialist

class TestSpatialSpecialist:

    def setup_method(self):
        self.spatial_specialist = SpatialSpecialist()

    def test_get_spatial_belief_propositions_happy_path(self):
        self.spatial_specialist.spatial_map = {
            'root': (0, 0),
            'nodes': [
                {'name': 'node1', 'description': 'Description 1'},
                {'name': 'node2', 'description': 'Description 2'}
            ]
        }
        
        expected_propositions = [
            "My physical root is located at (0, 0)",
            "I have awareness of 2 top-level components",
            "Directory 'node1' serves as: Description 1",
            "Directory 'node2' serves as: Description 2"
        ]
        
        assert self.spatial_specialist.get_spatial_belief_propositions() == expected_propositions

    def test_get_spatial_belief_propositions_empty_nodes(self):
        self.spatial_specialist.spatial_map = {
            'root': (0, 0),
            'nodes': []
        }
        
        expected_propositions = [
            "My physical root is located at (0, 0)",
            "I have awareness of 0 top-level components"
        ]
        
        assert self.spatial_specialist.get_spatial_belief_propositions() == expected_propositions

    def test_get_spatial_belief_propositions_no_nodes(self):
        self.spatial_specialist.spatial_map = {
            'root': (0, 0),
            'nodes': None
        }
        
        expected_propositions = [
            "My physical root is located at (0, 0)",
            "I have awareness of 0 top-level components"
        ]
        
        assert self.spatial_specialist.get_spatial_belief_propositions() == expected_propositions

    def test_get_spatial_belief_propositions_no_root(self):
        self.spatial_specialist.spatial_map = {
            'root': None,
            'nodes': [
                {'name': 'node1', 'description': 'Description 1'}
            ]
        }
        
        expected_propositions = [
            "My physical root is located at None",
            "I have awareness of 1 top-level components",
            "Directory 'node1' serves as: Description 1"
        ]
        
        assert self.spatial_specialist.get_spatial_belief_propositions() == expected_propositions

    def test_get_spatial_belief_propositions_no_root_and_nodes(self):
        self.spatial_specialist.spatial_map = {
            'root': None,
            'nodes': None
        }
        
        expected_propositions = [
            "My physical root is located at None",
            "I have awareness of 0 top-level components"
        ]
        
        assert self.spatial_specialist.get_spatial_belief_propositions() == expected_propositions

    def test_get_spatial_belief_propositions_no_spatial_map(self):
        self.spatial_specialist.spatial_map = {}
        
        expected_propositions = []
        
        assert self.spatial_specialist.get_spatial_belief_propositions() == expected_propositions