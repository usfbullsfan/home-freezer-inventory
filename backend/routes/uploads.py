from flask import Blueprint, request, jsonify, send_from_directory, current_app
from flask_jwt_extended import jwt_required
from werkzeug.utils import secure_filename
from PIL import Image
import os
import uuid
import mimetypes
import logging

uploads_bp = Blueprint('uploads', __name__)

# Allowed image extensions and MIME types
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_MIME_TYPES = {
    'image/png',
    'image/jpeg',
    'image/gif',
    'image/webp'
}

# Maximum file size: 5MB
MAX_FILE_SIZE = 5 * 1024 * 1024


def get_upload_folder():
    """Get the upload folder path, creating it if necessary"""
    upload_folder = os.path.join(current_app.root_path, 'uploads', 'category_images')
    os.makedirs(upload_folder, exist_ok=True)
    return upload_folder


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_image(file_path):
    """Validate that the file is actually an image using PIL"""
    try:
        with Image.open(file_path) as img:
            # Verify it's a valid image
            img.verify()
            return True
    except Exception:
        return False


@uploads_bp.route('/category-image', methods=['POST'])
@jwt_required()
def upload_category_image():
    """
    Upload a category image with security validation.

    Security measures:
    - File size limit (5MB)
    - Extension whitelist
    - MIME type validation
    - Image verification using PIL
    - Secure filename generation
    - Protected storage location
    """
    # Check if file is present
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    # Check if filename is empty
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Check file size (Flask's MAX_CONTENT_LENGTH is a backup)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset file pointer

    if file_size > MAX_FILE_SIZE:
        return jsonify({'error': f'File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)}MB'}), 400

    if file_size == 0:
        return jsonify({'error': 'File is empty'}), 400

    # Validate file extension
    if not allowed_file(file.filename):
        return jsonify({'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

    # Validate MIME type
    mime_type = file.content_type
    if mime_type not in ALLOWED_MIME_TYPES:
        return jsonify({'error': 'Invalid file type'}), 400

    # Generate secure filename with UUID to prevent conflicts and directory traversal
    original_extension = file.filename.rsplit('.', 1)[1].lower()

    # SECURITY: Validate extension contains only alphanumeric characters
    # This prevents path traversal attempts via extension (e.g., ".png/../../../etc/passwd")
    if not original_extension.isalnum():
        return jsonify({'error': 'Invalid file extension format'}), 400

    # Generate filename using UUID (secure random) + validated extension
    unique_filename = f"{uuid.uuid4()}.{original_extension}"

    # SECURITY: Use secure_filename to sanitize (defense in depth)
    unique_filename = secure_filename(unique_filename)

    # Get upload folder
    upload_folder = get_upload_folder()

    # Construct file path
    file_path = os.path.join(upload_folder, unique_filename)

    # SECURITY: Verify the resolved path is within the upload folder
    # This prevents path traversal even if validation above is bypassed
    try:
        real_upload_folder = os.path.realpath(upload_folder)
        real_file_path = os.path.realpath(file_path)

        if not real_file_path.startswith(real_upload_folder + os.sep):
            return jsonify({'error': 'Invalid file path'}), 400
    except (ValueError, OSError):
        return jsonify({'error': 'Invalid file path'}), 400

    try:
        # Save file temporarily
        file.save(file_path)

        # Validate it's actually an image
        if not validate_image(file_path):
            os.remove(file_path)
            return jsonify({'error': 'File is not a valid image'}), 400

        # Re-open and re-save to strip any potential malicious data
        with Image.open(file_path) as img:
            # Convert RGBA to RGB if necessary (for JPEG)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background

            # Save the cleaned image
            img.save(file_path, quality=85, optimize=True)

        # Return the URL to access the image
        image_url = f"/api/uploads/category-images/{unique_filename}"

        return jsonify({
            'success': True,
            'image_url': image_url,
            'filename': unique_filename
        }), 201

    except Exception as e:
        # SECURITY: Log detailed error for debugging but return generic message to user
        # This prevents information exposure about internal paths, database details, etc.
        logging.exception("Failed to process uploaded image")

        # Clean up on error
        if os.path.exists(file_path):
            os.remove(file_path)

        return jsonify({'error': 'Failed to process image. Please ensure the file is a valid image.'}), 500


@uploads_bp.route('/category-images/<filename>', methods=['GET'])
def get_category_image(filename):
    """
    Serve uploaded category images.
    No JWT required as images are public resources.
    """
    # Validate filename to prevent directory traversal
    if not filename or '/' in filename or '\\' in filename or '..' in filename:
        return jsonify({'error': 'Invalid filename'}), 400

    # Validate file extension
    if not allowed_file(filename):
        return jsonify({'error': 'Invalid file type'}), 400

    upload_folder = get_upload_folder()

    try:
        return send_from_directory(upload_folder, filename)
    except FileNotFoundError:
        return jsonify({'error': 'Image not found'}), 404


@uploads_bp.route('/category-images/<filename>', methods=['DELETE'])
@jwt_required()
def delete_category_image(filename):
    """
    Delete an uploaded category image.
    Requires authentication.
    """
    # Validate filename to prevent directory traversal
    if not filename or '/' in filename or '\\' in filename or '..' in filename:
        return jsonify({'error': 'Invalid filename'}), 400

    # SECURITY: Validate file extension
    if not allowed_file(filename):
        return jsonify({'error': 'Invalid file type'}), 400

    # SECURITY: Use secure_filename to sanitize
    safe_filename = secure_filename(filename)

    # SECURITY: Use basename to strip any directory components
    safe_filename = os.path.basename(safe_filename)

    upload_folder = get_upload_folder()

    # Construct file path
    file_path = os.path.join(upload_folder, safe_filename)

    # SECURITY: Verify the resolved path is within the upload folder
    # This prevents path traversal even if validation above is bypassed
    try:
        real_upload_folder = os.path.realpath(upload_folder)
        real_file_path = os.path.realpath(file_path)

        if not real_file_path.startswith(real_upload_folder + os.sep):
            return jsonify({'error': 'Path traversal detected'}), 400
    except (ValueError, OSError):
        return jsonify({'error': 'Invalid file path'}), 400

    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({'success': True, 'message': 'Image deleted'}), 200
        else:
            return jsonify({'error': 'Image not found'}), 404
    except Exception as e:
        # SECURITY: Log detailed error for debugging but return generic message to user
        logging.exception("Failed to delete category image")
        return jsonify({'error': 'Failed to delete image'}), 500
