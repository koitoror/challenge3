"""Defines routes for CRUD functions in diary
Calls methods from Diary model
GET: Reads all Diaries
    Fetch all diary from db
POST: Creates a diary
    Takes current_user ID and update data
GET: Read single diary info
PUT: Updates single diary
DELETE: Delete single diary
"""
from flask import Blueprint, jsonify, request
from versions.v2.models import Diary
from versions import login_required
from functools import wraps
from versions.utils import existing_module, get_in_module


mod = Blueprint('diary_v2', __name__)


def precheck(f):
    """Checks if diaryID is available
    Check if diary belongs to current user
    """
    @wraps(f)
    def wrap(*args, **kwargs):
        diary = get_in_module('diary', kwargs['diaryId'])

        if not diary:
            return jsonify({'warning': 'Diary Not Found'}), 404

        if args[0] != diary.owner.id:
            return jsonify({'warning': 'Not Allowed, you are not owner'}), 401

        return f(*args, **kwargs)
    return wrap


@mod.route('/', methods=['GET'])
def read_all_diaries():
    """Reads all Diaries
    user can search for diary via diary name
    response is paginated per limit
    """
    params = {
        'page': request.args.get('page', default=1, type=int),
        'limit': request.args.get('limit', default=5, type=int),
        'location': request.args.get('location', default=None, type=str),
        'category': request.args.get('category', default=None, type=str),
        '_query': request.args.get('q', default=None, type=str)
    }

    diaries = Diary().Search(params)

    if diaries:
        return jsonify({
            'diaries': [
                {   'id': diary.id,
                    'name': diary.name,
                    'logo': diary.logo,
                    'location': diary.location,
                    'category': diary.category,
                    'bio': diary.bio,
                    'owner': diary.owner.username,
                    'created_at': diary.created_at,
                    'updated_at': diary.updated_at
                } for diary in diaries
            ]
        }), 200
    return jsonify({'warning': 'No Diaries, create one first'}), 200


@mod.route('/', methods=['POST'])
@login_required
def create_diary(current_user):
    """Creates a diary
    Takes current_user ID and update data
    test if actually saved
    """
    data = request.get_json()

    # Check if there is an existing diary with same name
    if existing_module('diary', data['name']):
        return jsonify({
            'warning': 'Diary name {} already taken'.format(data['name'])
        }), 409

    diary_owner = get_in_module('user', current_user)

    # create new diary instances
    new_diary = Diary(
        name=data['name'],
        logo=data['logo'],
        location=data['location'],
        category=data['category'],
        bio=data['bio'],
        owner=diary_owner
    )

    # Commit changes to db
    new_diary.save()

    # Send response if diary was saved
    if new_diary.id:
        return jsonify({
            'success': 'successfully created diary',
            'diary': {
                'id': new_diary.id,
                'name': new_diary.name,
                'location': new_diary.location,
                'category': new_diary.category,
                'bio': new_diary.bio,
                'owner': new_diary.owner.username
            }
        }), 201

    return jsonify({'warning': 'Could not create new diary'}), 401


@mod.route('/<diaryId>', methods=['GET'])
def read_diary(diaryId):
    """Reads Diary given a diary id"""
    diary = get_in_module('diary', diaryId)

    if diary:
        return jsonify({
            'diary': {
                'id': diary.id,
                'name': diary.name,
                'logo': diary.logo,
                'location': diary.location,
                'category': diary.category,
                'bio': diary.bio,
                'owner': diary.owner.username,
                'created_at': diary.created_at,
                'updated_at': diary.updated_at
            }
        }), 200
    return jsonify({'warning': 'Diary Not Found'}), 404


@mod.route('/<diaryId>', methods=['PUT'])
@login_required
@precheck
def update_diary(current_user, diaryId):
    """Updates a diary given a diary ID
    confirms if current user is owner of diary
    """
    data = request.get_json()
    diary = get_in_module('diary', diaryId)

    diary.name = data['name']
    diary.logo = data['logo']
    diary.location = data['location']
    diary.category = data['category']
    diary.bio = data['bio']

    diary.save()

    if diary.name == data['name']:
        return jsonify({
            'success': 'successfully updated',
            'diary': {
                'id': diary.id,
                'name': diary.name,
                'logo': diary.logo,
                'location': diary.location,
                'category': diary.category,
                'bio': diary.bio,
                'owner': diary.owner.username,
                'created_at': diary.created_at,
                'updated_at': diary.updated_at
            }
        }), 201

    return jsonify({'warning': 'Diary Not Updated'}), 400


@mod.route('/<diaryId>', methods=['DELETE'])
@login_required
@precheck
def delete_diary(current_user, diaryId):
    """Deletes a diary
    confirms if current user is owner of diary
    """
    diary = get_in_module('diary', diaryId)
    name = diary.name
    diary.delete()

    if not existing_module('diary', name):
        return jsonify({'success': 'Diary Deleted'}), 200

    return jsonify({'warning': 'Diary Not Deleted'}), 400
