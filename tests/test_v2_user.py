import unittest
import json
from versions import app
from versions.v2.models import User, db, Diary


class TestUser(unittest.TestCase):
    def setUp(self):
        """Creates the app as test client"""
        app.config.from_object('config.Testing')
        self.app = app.test_client()
        self.new_user_info = {
            'username': 'koitoror',
            'fullname': 'daniel jambo',
            'email': 'daniel.kamar@gmail.com',
            'password': 'kamarster@gmail.com'
        }
        self.new_user_login = {
            'username': 'koitoror',
            'password': 'kamarster@gmail.com'
        }

    def test_read_all_users(self):
        """v2 Test Get all users route"""
        self.register()
        response = self.app.get('/api/v2/users')
        self.assertEqual(response.status_code, 200)

        output = json.loads(response.get_data(as_text=True))
        self.assertEqual(output[0]['username'], self.new_user_info['username'])

    def test_read_one_user(self):
        """v2 Test endpoint for one user"""
        new_user = self.register()
        user_id = json.loads(new_user.get_data(as_text=True))['success']['id']
        response = self.app.get('/api/v2/users/{}'.format(user_id))
        self.assertEqual(response.status_code, 200)

    def test_not_found_user(self):
        """v2 Test endpoint if user doesn't exist"""
        response = self.app.get('/api/v2/users/15')
        output = json.loads(response.get_data(as_text=True))['warning']
        self.assertEqual(
            output,
            "user does not exist"
        )

    def test_read_user_diaries(self):
        """v2 Test all diary owned by user"""
        new_user = self.register()
        user_id = json.loads(new_user.get_data(as_text=True))['success']['id']

        self.login()
        self.create_diary()
        response = self.app.get('/api/v2/users/{}/diaries'.format(user_id))
        self.assertEqual(response.status_code, 200)

        output = json.loads(response.get_data(as_text=True))[0]['name']
        self.assertEqual(output, 'Facebook')

    def test_not_found_user_diaries(self):
        """v2 Test all diary owned by user
        If user doesn't exist
        """
        self.register()
        self.login()
        response = self.app.get('/api/v2/users/100/diaries')
        self.assertEqual(response.status_code, 200)

        output = json.loads(response.get_data(as_text=True))['warning']
        self.assertEqual(output, 'user does not own a diary')

    def test_user_does_not_exist(self):
        """v2 test user does not exist
        """
        response = self.app.get('/api/v2/users/112')
        output = json.loads(response.get_data(as_text=True))['warning']
        self.assertEqual(output, 'user does not exist')

    def register(self):
        return self.app.post(
            '/api/v2/auth/register',
            data=json.dumps(self.new_user_info),
            content_type='application/json'
        )

    def login(self):
        return self.app.post(
            '/api/v2/auth/login',
            data=json.dumps(self.new_user_login),
            content_type='application/json'
        )

    def create_diary(self):
        new_diary_info = {
            "name": "Facebook",
            "logo": "url",
            "location": "Silcon valley",
            "category": "Technology",
            "bio": "In publishing and graphic design."
        }
        token = json.loads(self.login().get_data(as_text=True))['token']
        response = self.app.post(
            '/api/v2/diaries/',
            data=json.dumps(new_diary_info),
            headers={
                "content-type": "application/json",
                "x-access-token": token
            }
        )
        return response

    def tearDown(self):
        """Clean-up db"""
        db.session.query(Diary).delete()
        db.session.commit()
        db.session.query(User).delete()
        db.session.commit()


if __name__ == '__main__':
    unittest.main()
