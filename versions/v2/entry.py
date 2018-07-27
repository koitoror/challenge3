"""Defines routes for CRUD functions in entry
Calls methods from Diary model
POST: Create Entry given a diary ID
    uses diaryID and current_user to create the relationship
GET: Reads all Entry for a diaryID
PUT: Updates a entry
    expects diaryID, current_user and entryID as arguments
DELETE: Deletes a Entry
    expects diaryID, current_user and entryID as arguments
"""
from flask import Blueprint, jsonify, request
from versions.v2.models import Diary, db, User, Entry, Notification
from versions import login_required
from functools import wraps

mod = Blueprint('entry_v2', __name__)


def precheck(f):
    """Checks if diaryID is available
    Check if diary belongs to current user
    """
    @wraps(f)
    def wrap(*args, **kwargs):
        diary = Diary.query.get(kwargs['diaryId'])
        entry = Entry.query.get(kwargs['entryId'])

        if not diary:
            return jsonify({'warning': 'Diary Not Found'}), 404

        if not entry:
            return jsonify({'warning': 'Entry Not Found'}), 404

        if args[0] != entry.entryer.id:
            return jsonify({'warning': 'Not Allowed, you are not owner'}), 401

        return f(*args, **kwargs)
    return wrap


@mod.route('/<diaryId>/entries', methods=['POST'])
@login_required
def create_entry(current_user, diaryId):
    """Create Entry given a diary ID
    Takes current user ID and diary ID then attachs it to response data
    """
    data = request.get_json()
    _entryer = User.query.get(current_user)
    _diary = Diary.query.get(diaryId)

    if not _diary:
        return jsonify({'warning': 'Diary Not Found'}), 404

    # create new entry instances
    new_entry = Entry(
        title=data['title'],
        desc=data['desc'],
        diary=_diary,
        entryer=_entryer
    )

    # Commit changes to db
    new_entry.save()

    # Send response if diary was saved
    if new_entry.id:
        # create a notification if entry is created
        if current_user != _diary.owner.id:
            new_notification = Notification(
                recipient=_diary.owner,
                actor=_entryer.username,
                diary_id=diaryId,
                entry_id=new_entry.id
            )
            new_notification.save()

        return jsonify({
            'success': 'successfully created entry',
            'entry': {
                'id': new_entry.id,
                'title': new_entry.title,
                'entryer': new_entry.entryer.username,
                'desc': new_entry.desc
            }
        }), 201

    return jsonify({'warning': 'Could not create new entries'}), 401


@mod.route('/<diaryId>/entries', methods=['GET'])
def read_entry(diaryId):
    """Reads all Entry given a diary ID"""
    diary = Diary.query.get(diaryId)
    if not diary:
        return jsonify({'warning': 'Diary Not Found'}), 404

    if diary.entries:
        return jsonify({'entries': [
            {
                'id': entry.id,
                'title': entry.title,
                'desc': entry.desc,
                'entryer': entry.entryer.username,
                'diary': entry.diary.name,
                'created_at': entry.created_at,
                'updated_at': entry.updated_at,
            } for entry in diary.entries
        ]}), 200

    return jsonify({'warning': 'Diary has no entries'}), 200


@mod.route('/<diaryId>/entries/<entryId>', methods=['DELETE'])
@login_required
@precheck
def delete_entry(current_user, diaryId, entryId):
    """Delete a Entry given a entry ID and diary ID
    confirms if current_user is owner of entry
    """
    title = ''
    entry = Entry.query.get(entryId)
    if entry:
        title = entry.title
        entry.delete()

    if not db.session.query(
        db.exists().where(Entry.title == title)
    ).scalar():
        return jsonify({'success': 'Entry Deleted'}), 200

    return jsonify({'warning': 'Entry Not Deleted'}), 400


@mod.route('/entries', methods=['GET'])
@login_required
def read_all_entries(current_user):
    """Reads all Entries"""
    entries = Entry.query.all()
    if entries:
        return jsonify({'Entries': [
            {
                'id': entry.id,
                'title': entry.title,
                'desc': entry.desc,
                'entryer': entry.entryer.username,
                'diary': entry.diary.name,
                'created_at': entry.created_at,
                'updated_at': entry.updated_at
            } for entry in entries
        ]}), 200

    return jsonify({'warning': 'No Entry, create one first'}), 200


@mod.route('/<diaryId>/entries/<entryId>', methods=['PUT'])
@login_required
@precheck
def update_diary(current_user, diaryId, entryId):
    """Updates a entry given a diary ID
    confirms if current user is owner of diary
    """
    data = request.get_json()
    entry = Entry.query.get(entryId)

    entry.title = data['title']
    entry.desc = data['desc']

    entry.save()

    if entry.title == data['title']:
        return jsonify({
            'success': 'successfully updated',
            'entry': {
                'id': entry.id,
                'title': entry.title,
                'desc': entry.desc,
                'entryer': entry.entryer.username,
                'diary': entry.diary.name,
                'created_at': entry.created_at,
                'updated_at': entry.updated_at
            }
        }), 201

    return jsonify({'warning': 'Entry Not Updated'}), 400
