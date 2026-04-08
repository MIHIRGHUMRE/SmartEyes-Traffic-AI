from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import requests
import json
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = 'traffic_violation_dashboard_secret_key'

# Cloud API base URL
CLOUD_API_URL = os.getenv('CLOUD_API_URL', 'http://localhost:8000')

@app.route('/')
def index():
    """Dashboard home page."""
    try:
        # Get dashboard stats
        response = requests.get(f"{CLOUD_API_URL}/api/dashboard/stats")
        stats = response.json() if response.status_code == 200 else {}

        # Get recent violations
        response = requests.get(f"{CLOUD_API_URL}/api/violations?limit=10")
        recent_violations = response.json() if response.status_code == 200 else []

        # Get leaderboard
        response = requests.get(f"{CLOUD_API_URL}/api/leaderboard?limit=10")
        leaderboard = response.json() if response.status_code == 200 else []

        return render_template('index.html',
                             stats=stats,
                             recent_violations=recent_violations,
                             leaderboard=leaderboard)

    except Exception as e:
        flash(f"Error loading dashboard: {str(e)}", "error")
        return render_template('index.html', stats={}, recent_violations=[], leaderboard=[])

@app.route('/violations')
def violations():
    """Violations page."""
    try:
        status = request.args.get('status')
        user_id = request.args.get('user_id')

        params = {'limit': 100}
        if status:
            params['status'] = status
        if user_id:
            params['user_id'] = user_id

        response = requests.get(f"{CLOUD_API_URL}/api/violations", params=params)
        violations = response.json() if response.status_code == 200 else []

        return render_template('violations.html', violations=violations)

    except Exception as e:
        flash(f"Error loading violations: {str(e)}", "error")
        return render_template('violations.html', violations=[])

@app.route('/users')
def users():
    """Users page."""
    try:
        # This would need an endpoint to get all users
        # For now, show leaderboard
        response = requests.get(f"{CLOUD_API_URL}/api/leaderboard?limit=50")
        users = response.json() if response.status_code == 200 else []

        return render_template('users.html', users=users)

    except Exception as e:
        flash(f"Error loading users: {str(e)}", "error")
        return render_template('users.html', users=[])

@app.route('/user/<user_id>')
def user_profile(user_id):
    """User profile page."""
    try:
        response = requests.get(f"{CLOUD_API_URL}/api/user/{user_id}")
        user = response.json() if response.status_code == 200 else None

        if not user:
            flash("User not found", "error")
            return redirect(url_for('users'))

        # Get user's violations
        response = requests.get(f"{CLOUD_API_URL}/api/violations?user_id={user_id}&limit=20")
        violations = response.json() if response.status_code == 200 else []

        return render_template('user_profile.html', user=user, violations=violations)

    except Exception as e:
        flash(f"Error loading user profile: {str(e)}", "error")
        return redirect(url_for('users'))

@app.route('/reports')
def reports():
    """Reports and analytics page."""
    try:
        # Get various statistics
        response = requests.get(f"{CLOUD_API_URL}/api/dashboard/stats")
        stats = response.json() if response.status_code == 200 else {}

        # Calculate some derived metrics
        if stats:
            stats['violation_rate'] = stats.get('total_violations', 0) / max(stats.get('total_users', 1), 1)
            stats['payment_rate'] = 1 - (stats.get('pending_challans', 0) / max(stats.get('total_violations', 1), 1))

        return render_template('reports.html', stats=stats)

    except Exception as e:
        flash(f"Error loading reports: {str(e)}", "error")
        return render_template('reports.html', stats={})

@app.route('/api/violations/<violation_id>/status', methods=['POST'])
def update_violation_status(violation_id):
    """Update violation status (AJAX endpoint)."""
    try:
        data = request.get_json()
        new_status = data.get('status')

        # In a real implementation, this would update the database
        # For demo, just return success

        return jsonify({'status': 'success', 'message': f'Violation {violation_id} status updated to {new_status}'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/settings')
def settings():
    """Settings page."""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    return render_template('settings.html', now=current_time)

@app.route('/health')
def health():
    """Health check."""
    try:
        response = requests.get(f"{CLOUD_API_URL}/health")
        cloud_health = response.json() if response.status_code == 200 else {'status': 'unreachable'}

        return jsonify({
            'dashboard': 'healthy',
            'cloud_api': cloud_health,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'dashboard': 'healthy',
            'cloud_api': {'status': 'error', 'error': str(e)},
            'timestamp': datetime.now().isoformat()
        })

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)