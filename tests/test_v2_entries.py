import json
import unittest
from versions import app
from versions.v2.models import User, db, Diary, Entry


class TestEntryV2(unittest.TestCase):
    def setUp(self):
        app.config.from_object('config.Testing')
        self.app = app.test_client()
        self.new_entry = {
            "title": "Friday 13th",
            "desc": "Lorem ipsum dolor sit amet consectetur adip elit."
        }
        self.new_user_info = {
            "username": "oliver",
            "fullname": "oliver kamar",
            "email": "oliver.kamar@maseno.com",
            "password": "kamarster@gmail.com"
        }
        self.user_login_info = {
            "username": "oliver",
            "password": "kamarster@gmail.com"
        }
        self.new_diary_info = {
            "name": "Crown paints",
            "logo": "url",
            "category": "Construction",
            "location": "NBO",
            "bio": "if you like it crown it"
        }

    def test_create_entry(self):
        """Create new entry for a diary
        """
        response = self.register_entry()
        self.assertEqual(response.status_code, 201)
        self.assertIn('successfully created entry', str(response.data))
        _entry = json.loads(response.get_data(as_text=True))
        exists = db.session.query(
            db.exists().where(Entry.title == _entry['entry']['title']))
        self.assertTrue(exists)

    def test_read_entries(self):
        """Get entries for diary
        """
        new_diary = self.register_diary()
        diary_id = json.loads(
            new_diary.get_data(as_text=True))['diary']['id']

        new_entry = self.app.post(
            '/api/v2/diaries/{}/entries'.format(diary_id),
            data=json.dumps(self.new_entry),
            headers={
                "content-type": "application/json",
                "x-access-token": self.token()})

        entry_id = json.loads(
            new_entry.get_data(as_text=True))['entry']['id']

        resp = self.app.get(
            '/api/v2/diaries/{}/entries'.format(diary_id))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            entry_id,
            json.loads(resp.get_data(as_text=True))['entries'][0]['id'])

        response = self.app.get(
            '/api/v2/diaries/entries',
            headers={
                "content-type": "application/json",
                "x-access-token": self.token()
            }
        )
        self.assertEqual(response.status_code, 200)

        output = json.loads(response.get_data(as_text=True))['Entries']
        self.assertEqual(output[0]['title'], self.new_entry['title'])

    def test_delete_entry(self):
        """Test deleting diary twice
        """
        new_diary = self.register_diary()
        diary_id = json.loads(
            new_diary.get_data(as_text=True))['diary']['id']

        new_entry = self.app.post(
            '/api/v2/diaries/{}/entries'.format(diary_id),
            data=json.dumps(self.new_entry),
            headers={
                "content-type": "application/json",
                "x-access-token": self.token()})

        entry_id = json.loads(
            new_entry.get_data(as_text=True))['entry']['id']
        self.app.delete(
            '/api/v2/diaries/{}/entries/{}'.format(diary_id, entry_id),
            data=json.dumps(self.new_entry),
            headers={
                "content-type": "application/json",
                "x-access-token": self.token()})
        exists = db.session.query(
            db.exists().where(Entry.title == self.new_entry['title']))
        self.assertTrue(exists)

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
                "x-access-token": self.token()
            }
        )

    def register_entry(self):
        new_diary = self.register_diary()
        diary_id = json.loads(
            new_diary.get_data(as_text=True))['diary']['id']

        return self.app.post(
            '/api/v2/diaries/{}/entries'.format(diary_id),
            data=json.dumps(self.new_entry),
            headers={
                "content-type": "application/json",
                "x-access-token": self.token()})

    def tearDown(self):
        """Clean-up db"""
        db.session.query(Entry).delete()
        db.session.query(Diary).delete()
        db.session.query(User).delete()
        db.session.commit()


if __name__ == '__main__':
    unittest.main()
