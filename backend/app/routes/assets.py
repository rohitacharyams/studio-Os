"""
Asset upload routes for handling file uploads to S3.

This module provides endpoints for uploading images and videos
for both studio media and class media.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.exceptions import RequestEntityTooLarge

from app import db
from app.models import User, Studio, DanceClass
from app.services.s3_service import get_s3_service, S3ServiceError

assets_bp = Blueprint('assets', __name__)


@assets_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_asset():
    """
    Upload a single image or video asset.
    
    Request (multipart/form-data):
    - file: File to upload (required)
    - asset_type: 'image' or 'video' (required)
    - context: 'studio' or 'class' (required)
    - class_id: Class ID (required if context='class')
    
    Response:
    {
        'url': 'https://s3.../file.jpg',
        'key': 'studios/{studio_id}/photos/{uuid}-file.jpg',
        'type': 'image',
        'size': 1024000,
        'content_type': 'image/jpeg',
        'filename': 'original.jpg'
    }
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if not user.studio_id:
        return jsonify({'error': 'No studio found'}), 404
    
    # Check permissions
    if user.role not in ['owner', 'admin']:
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    # Get request data
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    asset_type = request.form.get('asset_type', '').lower()
    context = request.form.get('context', 'studio').lower()
    class_id = request.form.get('class_id')
    
    # Validate asset_type
    if asset_type not in ['image', 'video']:
        return jsonify({'error': "asset_type must be 'image' or 'video'"}), 400
    
    # Validate context
    if context not in ['studio', 'class']:
        return jsonify({'error': "context must be 'studio' or 'class'"}), 400
    
    # Validate class_id if context is 'class'
    if context == 'class':
        if not class_id:
            return jsonify({'error': 'class_id is required when context is "class"'}), 400
        
        # Verify class belongs to user's studio
        dance_class = DanceClass.query.filter_by(
            id=class_id,
            studio_id=user.studio_id
        ).first()
        
        if not dance_class:
            return jsonify({'error': 'Class not found or access denied'}), 404
    
    # Upload file
    try:
        s3_service = get_s3_service()
        result = s3_service.upload_file(
            file=file,
            file_type=asset_type,
            studio_id=user.studio_id,
            context=context,
            class_id=class_id
        )
        
        return jsonify(result), 201
    
    except S3ServiceError as e:
        return jsonify({'error': str(e)}), 400
    except RequestEntityTooLarge:
        return jsonify({'error': 'File too large'}), 413
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@assets_bp.route('/upload-multiple', methods=['POST'])
@jwt_required()
def upload_multiple_assets():
    """
    Upload multiple files at once.
    
    Request (multipart/form-data):
    - files: List of files (required)
    - asset_type: 'image' or 'video' (required)
    - context: 'studio' or 'class' (required)
    - class_id: Class ID (required if context='class')
    
    Response:
    {
        'uploads': [
            {
                'url': 'https://s3.../file1.jpg',
                'key': 'studios/{studio_id}/photos/{uuid}-file1.jpg',
                'type': 'image',
                'size': 1024000,
                'filename': 'file1.jpg'
            },
            ...
        ],
        'errors': [
            {'filename': 'file2.jpg', 'error': 'File too large'},
            ...
        ]
    }
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if not user.studio_id:
        return jsonify({'error': 'No studio found'}), 404
    
    # Check permissions
    if user.role not in ['owner', 'admin']:
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    # Get request data
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files')
    asset_type = request.form.get('asset_type', '').lower()
    context = request.form.get('context', 'studio').lower()
    class_id = request.form.get('class_id')
    
    # Validate asset_type
    if asset_type not in ['image', 'video']:
        return jsonify({'error': "asset_type must be 'image' or 'video'"}), 400
    
    # Validate context
    if context not in ['studio', 'class']:
        return jsonify({'error': "context must be 'studio' or 'class'"}), 400
    
    # Validate class_id if context is 'class'
    if context == 'class':
        if not class_id:
            return jsonify({'error': 'class_id is required when context is "class"'}), 400
        
        # Verify class belongs to user's studio
        dance_class = DanceClass.query.filter_by(
            id=class_id,
            studio_id=user.studio_id
        ).first()
        
        if not dance_class:
            return jsonify({'error': 'Class not found or access denied'}), 404
    
    # Upload files
    uploads = []
    errors = []
    s3_service = get_s3_service()
    
    for file in files:
        if not file or not file.filename:
            continue
        
        try:
            result = s3_service.upload_file(
                file=file,
                file_type=asset_type,
                studio_id=user.studio_id,
                context=context,
                class_id=class_id
            )
            uploads.append(result)
        except S3ServiceError as e:
            errors.append({
                'filename': file.filename,
                'error': str(e)
            })
        except Exception as e:
            errors.append({
                'filename': file.filename,
                'error': f'Upload failed: {str(e)}'
            })
    
    return jsonify({
        'uploads': uploads,
        'errors': errors,
        'success_count': len(uploads),
        'error_count': len(errors)
    }), 201 if uploads else 400


@assets_bp.route('/<path:asset_key>', methods=['DELETE'])
@jwt_required()
def delete_asset(asset_key):
    """
    Delete an asset from S3.
    
    Args:
        asset_key: S3 key (path) of the file to delete
    
    Response:
    {
        'message': 'Asset deleted successfully',
        'key': 'studios/{studio_id}/photos/{uuid}-file.jpg'
    }
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if not user.studio_id:
        return jsonify({'error': 'No studio found'}), 404
    
    # Check permissions
    if user.role not in ['owner', 'admin']:
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    # Verify asset belongs to user's studio
    # S3 key format: studios/{studio_id}/... or classes/{studio_id}/...
    if not asset_key.startswith(f"studios/{user.studio_id}/") and \
       not asset_key.startswith(f"classes/{user.studio_id}/"):
        return jsonify({'error': 'Asset not found or access denied'}), 404
    
    # Delete file
    try:
        s3_service = get_s3_service()
        success = s3_service.delete_file(asset_key)
        
        if success:
            return jsonify({
                'message': 'Asset deleted successfully',
                'key': asset_key
            }), 200
        else:
            return jsonify({'error': 'Failed to delete asset'}), 500
    
    except Exception as e:
        return jsonify({'error': f'Delete failed: {str(e)}'}), 500


@assets_bp.route('/presigned-url/<path:asset_key>', methods=['GET'])
@jwt_required()
def get_presigned_url(asset_key):
    """
    Generate a presigned URL for temporary access to a private asset.
    
    Query params:
    - expiration: Expiration time in seconds (default: 3600)
    
    Response:
    {
        'url': 'https://s3.../file.jpg?signature=...',
        'expiration': 3600
    }
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if not user.studio_id:
        return jsonify({'error': 'No studio found'}), 404
    
    # Verify asset belongs to user's studio
    if not asset_key.startswith(f"studios/{user.studio_id}/") and \
       not asset_key.startswith(f"classes/{user.studio_id}/"):
        return jsonify({'error': 'Asset not found or access denied'}), 404
    
    # Get expiration from query params
    expiration = request.args.get('expiration', 3600, type=int)
    expiration = min(expiration, 604800)  # Max 7 days
    
    # Generate presigned URL
    try:
        s3_service = get_s3_service()
        url = s3_service.generate_presigned_url(asset_key, expiration)
        
        if url:
            return jsonify({
                'url': url,
                'expiration': expiration
            }), 200
        else:
            return jsonify({'error': 'Failed to generate presigned URL'}), 500
    
    except Exception as e:
        return jsonify({'error': f'Failed to generate URL: {str(e)}'}), 500
