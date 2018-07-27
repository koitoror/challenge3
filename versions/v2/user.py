"""defines user routes
get all users
get all diaries that belongs to a user
get all entries that belongs to a user
get one user information
"""
from flask import Blueprint, jsonify
from versions.v2.models import User


mod = Blueprint('users_v2', __name__)


@mod.route('', methods=['GET'])
def get_all_users():
    """Read all users"""
    users = User.query.all()
    if users:
        return jsonify(
            [
                {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'diaries': [
                        {
                            'id': b.id,
                            'name': b.name
                        } for b in user.diaries] if user.diaries else None
                } for user in users
            ]
        ), 200
    return jsonify({'warning': 'No Users'}), 200


@mod.route('/<user_id>', methods=['GET'])
def read_user(user_id):
    """Reads user given an ID"""
    user = User.query.get(user_id)
    if user:
        return jsonify({'user': {
            'username': user.username,
            'fullname': user.fullname,
            'id': user.id,
            'activate': user.activate,
            'email': user.email
        }}), 200

    return jsonify({'warning': 'user does not exist'}), 404


@mod.route('/<user_id>/diaries', methods=['GET'])
def read_user_diaries(user_id):
    """Read all diaries owned by this user"""
    user = User.query.get(user_id)
    if user:
        return jsonify(
            [
                {
                    'id': diary.id,
                    'name': diary.name,
                    'logo': diary.logo,
                    'location': diary.location,
                    'category': diary.category,
                    'bio': diary.bio,
                    'created_at': diary.created_at,
                    'updated_at': diary.updated_at
                } for diary in user.diaries
            ] if user.diaries else None
        ), 200

    return jsonify({'warning': 'user does not own a diary'}), 200
