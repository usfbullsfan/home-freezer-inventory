from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import subprocess
import os

feedback_bp = Blueprint('feedback', __name__)


def get_db_connection():
    """Get database connection"""
    import sqlite3
    from flask import current_app

    # Get database path from Flask app config
    db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
    if db_uri.startswith('sqlite:///'):
        db_path = db_uri.replace('sqlite:///', '')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    else:
        raise ValueError('Feedback routes only support SQLite databases')


@feedback_bp.route('/submit', methods=['POST'])
@jwt_required()
def submit_feedback():
    """Submit new feedback (bug or enhancement request)"""
    user_id = int(get_jwt_identity())
    data = request.get_json()

    feedback_type = data.get('type')
    description = data.get('description', '').strip()

    # Validation
    if not feedback_type or feedback_type not in ['bug', 'enhancement']:
        return jsonify({'error': 'Invalid feedback type'}), 400

    if not description:
        return jsonify({'error': 'Description is required'}), 400

    if len(description) > 5000:
        return jsonify({'error': 'Description must be less than 5000 characters'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            '''INSERT INTO feedback_submissions (user_id, type, description)
               VALUES (?, ?, ?)''',
            (user_id, feedback_type, description)
        )
        conn.commit()
        feedback_id = cursor.lastrowid
        conn.close()

        return jsonify({
            'success': True,
            'id': feedback_id,
            'message': 'Feedback submitted successfully. It will be processed shortly.'
        }), 201

    except Exception as e:
        print(f'Error submitting feedback: {e}')
        return jsonify({'error': 'Failed to submit feedback'}), 500


@feedback_bp.route('/list', methods=['GET'])
@jwt_required()
def list_feedback():
    """List all feedback submissions (admin only)"""
    user_id = int(get_jwt_identity())

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if user is admin
    cursor.execute('SELECT role FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()

    if not user or user['role'] != 'admin':
        conn.close()
        return jsonify({'error': 'Admin access required'}), 403

    # Get feedback with user information
    cursor.execute(
        '''SELECT
               f.id,
               f.user_id,
               u.username,
               f.type,
               f.description,
               f.submitted_at,
               f.github_issue_number,
               f.github_issue_url,
               f.processed_at,
               f.status,
               f.error_message
           FROM feedback_submissions f
           JOIN users u ON f.user_id = u.id
           ORDER BY f.submitted_at DESC
           LIMIT 100'''
    )

    feedback_list = []
    for row in cursor.fetchall():
        feedback_list.append({
            'id': row['id'],
            'user_id': row['user_id'],
            'username': row['username'],
            'type': row['type'],
            'description': row['description'],
            'submitted_at': row['submitted_at'],
            'github_issue_number': row['github_issue_number'],
            'github_issue_url': row['github_issue_url'],
            'processed_at': row['processed_at'],
            'status': row['status'],
            'error_message': row['error_message']
        })

    conn.close()
    return jsonify({'feedback': feedback_list})


@feedback_bp.route('/process', methods=['POST'])
@jwt_required()
def process_feedback():
    """Manually trigger GitHub issue processing (admin only)"""
    user_id = int(get_jwt_identity())

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if user is admin
    cursor.execute('SELECT role FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()

    if not user or user['role'] != 'admin':
        conn.close()
        return jsonify({'error': 'Admin access required'}), 403

    conn.close()

    # Run the GitHub issue processor script
    try:
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'process_github_issues.py'
        )

        result = subprocess.run(
            ['python3', script_path],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': 'GitHub issues processed successfully',
                'output': result.stdout
            })
        else:
            # Script failed - return both stdout and stderr as they contain error messages
            error_output = result.stderr or result.stdout or 'Unknown error'
            return jsonify({
                'success': False,
                'error': 'Processing failed',
                'details': error_output.strip()
            }), 500

    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Processing timeout'}), 500
    except Exception as e:
        print(f'Error processing feedback: {e}')
        return jsonify({'error': 'Internal server error while processing feedback'}), 500


@feedback_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """Get feedback statistics (admin only)"""
    user_id = int(get_jwt_identity())

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if user is admin
    cursor.execute('SELECT role FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()

    if not user or user['role'] != 'admin':
        conn.close()
        return jsonify({'error': 'Admin access required'}), 403

    # Get statistics
    cursor.execute(
        '''SELECT
               COUNT(*) as total,
               SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
               SUM(CASE WHEN status = 'processed' THEN 1 ELSE 0 END) as processed,
               SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
               SUM(CASE WHEN type = 'bug' THEN 1 ELSE 0 END) as bugs,
               SUM(CASE WHEN type = 'enhancement' THEN 1 ELSE 0 END) as enhancements
           FROM feedback_submissions'''
    )

    row = cursor.fetchone()
    conn.close()

    return jsonify({
        'total': row['total'] or 0,
        'pending': row['pending'] or 0,
        'processed': row['processed'] or 0,
        'failed': row['failed'] or 0,
        'bugs': row['bugs'] or 0,
        'enhancements': row['enhancements'] or 0
    })
