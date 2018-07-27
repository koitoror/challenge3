import unittest
import json
from versions import app
from versions.v2.models import User, db, Diary


class TestDiaryV2(unittest.TestCase):
    def setUp(self):
        app.config.from_object('config.Testing')
        self.app = app.test_client()
        self.new_diary_info = {
            "name": "Crown",
            "logo": "url",
            "category": "Construction",
            "location": "NBO",
            "bio": "if you like it crown it"
        }
        self.update_diary_info = {
            "name": "Crown paints",
            "logo": "url",
            "category": "Construction",
            "location": "NBO",
            "bio": "if you like it crown it"
        }
        self.new_user_info = {
            "username": "robert",
            "fullname": "robert jambo",
            "email": "daniel.kamar@jkuat.comm",
            "password": "kamarster@gmail.com"
        }
        self.user_login_info = {
            "username": "robert",
            "password": "kamarster@gmail.com"
        }

    def test_read_all_diaries(self):
        """Test if can access endpoint for all diaries
        """
        self.register_diary()
        response = self.app.get('/api/v2/diaries/')
        self.assertEqual(response.status_code, 200)
        output = json.loads(response.get_data(as_text=True))['diaries']
        self.assertEqual(output[0]['name'], self.new_diary_info['name'])

    def test_read_if_no_diaries(self):
        """Test what happens when no diaries
        """
        response = self.app.get('/api/v2/diaries/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('No Diaries, create one first', str(response.data))

    def test_create_diary(self):
        """Test if can register new diary
        """
        response = self.register_diary()
        self.assertEqual(response.status_code, 201)
        output = json.loads(response.get_data(as_text=True))
        self.assertEqual(output['success'], 'successfully created diary')
        exists = db.session.query(
            db.exists().where(Diary.name == output['diary']['name'])
        ).scalar()
        self.assertTrue(exists)

    def test_create_diary_if_name_taken(self):
        """Test create diary if name is taken
        """
        self.register_diary()
        response = self.register_diary()
        output = json.loads(response.get_data(as_text=True))['warning']
        self.assertEqual(
            output,
            'Diary name {} already taken'.format(
                self.new_diary_info['name']))

    def test_can_read_one_diary(self):
        """Test route for single diary
        """
        new_diary = self.register_diary()
        diary_id = json.loads(
            new_diary.get_data(as_text=True))['diary']['id']

        response = self.app.get('/api/v2/diaries/{}'.format(diary_id))
        self.assertEqual(response.status_code, 200)
        output = json.loads(response.get_data(as_text=True))['diary']
        self.assertEqual(output['id'], diary_id)

    def test_read_no_diary(self):
        """Test 404 not found on diary not existing
        """
        response = self.app.get('/api/v2/diaries/6000')
        self.assertEqual(response.status_code, 404)

        output = json.loads(response.get_data(as_text=True))['warning']
        self.assertEqual(output, 'Diary Not Found')

    def test_update_diary(self):
        """Test if user can update diary
        """
        new_diary = self.register_diary()
        diary_id = json.loads(
            new_diary.get_data(as_text=True))['diary']['id']

        response = self.app.put(
            '/api/v2/diaries/{}'.format(diary_id),
            data=json.dumps(self.update_diary_info),
            headers={
                "content-type": "application/json",
                "x-access-token": self.token()
            }
        )
        self.assertIn('successfully updated', str(response.data))
        _diary = json.loads(response.get_data(as_text=True))
        exists = db.session.query(
            db.exists().where(Diary.name == _diary['diary']['name']))
        self.assertTrue(exists)

    def test_unsuccesful_update(self):
        """Test update if diary doesn't exist"""
        self.register_user()
        response = self.app.put(
            '/api/v2/diaries/6000',
            data=json.dumps(self.update_diary_info),
            headers={
                "content-type": "application/json",
                "x-access-token": self.token()
            }
        )
        self.assertIn('Diary Not Found', str(response.data))
        self.assertEqual(response.status_code, 404)

    def test_delete_diary_not_owner(self):
        """Test delete not your diary
        """
        new_user = {
            "username": "hotpoint",
            "fullname": "robert hotpoint",
            "email": "daniel.kamar@nbo.samadc.org",
            "password": "kamarster@gmail.com"
        }
        new_user_login = {
            "username": "hotpoint",
            "password": "kamarster@gmail.com"
        }
        self.app.post(
            '/api/v2/auth/register',
            data=json.dumps(new_user),
            content_type='application/json'
        )
        response_login = self.app.post(
            '/api/v2/auth/login',
            data=json.dumps(new_user_login),
            content_type='application/json'
        )
        token = json.loads(response_login.get_data(as_text=True))['token']
        new_diary = self.register_diary()
        diary_id = json.loads(
            new_diary.get_data(as_text=True))['diary']['id']

        response = self.app.delete(
            '/api/v2/diaries/{}'.format(diary_id),
            headers={
                "content-type": "application/json",
                "x-access-token": token
            }
        )
        self.assertEqual(response.status_code, 401)

        self.assertIn('Not Allowed, you are not owner', str(response.data))

    def test_delete_diary(self):
        """Test if actually deleted diary
        """
        new_diary = self.register_diary()
        diary_id = json.loads(
            new_diary.get_data(as_text=True))['diary']['id']

        response = self.app.delete(
            '/api/v2/diaries/{}'.format(diary_id),
            headers={
                "content-type": "application/json",
                "x-access-token": self.token()
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('Diary Deleted', str(response.data))

    def test_delete_empty_diary(self):
        """Test delete already deleted diary
        """
        self.register_user()
        response = self.app.delete(
            '/api/v2/diaries/1',
            headers={
                "content-type": "application/json",
                "x-access-token": self.token()
            }
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn('Diary Not Found', str(response.data))

    def register_user(self):
        return self.app.post(
            '/api/v2/auth/register',
            data=json.dumps(self.new_user_info),
            content_type='application/json'
        )

    def login(self):
        return self.app.post(
            '/api/v2/auth/login',
            data=json.dumps(self.user_login_info),
            content_type='application/json'
        )

    def token(self):
        response = self.app.post(
            '/api/v2/auth/login',
            data=json.dumps(self.user_login_info),
            content_type='application/json')
        return json.loads(response.get_data(as_text=True))['token']

    def register_diary(self):
        self.register_user()
        return self.app.post(
            '/api/v2/diaries/',
            data=json.dumps(self.new_diary_info),
            headers={
                "content-type": "application/json",
                "x-access-token": self.token()})

    def tearDown(self):
        """Clean-up db"""
        db.session.query(Diary).delete()
        db.session.query(User).delete()
        db.session.commit()


if __name__ == '__main__':
    unittest.main()
