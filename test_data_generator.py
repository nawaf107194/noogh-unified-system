# test_user_service.py

from unittest import TestCase
from tmp_test_data.test_data_generator import get_user_data

class TestUserService(TestCase):

    def test_create_user(self):
        user_data = get_user_data(name="Jane Doe", email="jane.doe@example.com")
        # Assume UserService is a class with a method create_user
        user_service = UserService()
        response = user_service.create_user(user_data)
        self.assertEqual(response.status_code, 201)

    def test_get_user(self):
        user_data = get_user_data(id=1, name="John Doe")
        # Assume UserService is a class with a method get_user
        user_service = UserService()
        response = user_service.get_user(user_data['id'])
        self.assertEqual(response.name, user_data['name'])