import hashlib
import uuid
from typing import Dict, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path

class UserIdentification:
    """Handle user identification for citizen reports."""

    def __init__(self, user_db_path: str = 'data/users.json'):
        """
        Initialize user identification system.

        Args:
            user_db_path: Path to user database file
        """
        self.user_db_path = Path(user_db_path)
        self.user_db_path.parent.mkdir(exist_ok=True)
        self.users = self._load_users()

    def _load_users(self) -> Dict:
        """Load user database."""
        if self.user_db_path.exists():
            with open(self.user_db_path, 'r') as f:
                return json.load(f)
        return {}

    def _save_users(self):
        """Save user database."""
        with open(self.user_db_path, 'w') as f:
            json.dump(self.users, f, indent=2)

    def register_user(self, user_info: Dict) -> str:
        """
        Register a new user.

        Args:
            user_info: User information dictionary

        Returns:
            User ID
        """
        user_id = str(uuid.uuid4())

        user_data = {
            'user_id': user_id,
            'name': user_info.get('name', ''),
            'email': user_info.get('email', ''),
            'phone': user_info.get('phone', ''),
            'registration_date': datetime.now().isoformat(),
            'total_reports': 0,
            'valid_reports': 0,
            'rewards_earned': 0,
            'trust_score': 1.0
        }

        self.users[user_id] = user_data
        self._save_users()

        return user_id

    def authenticate_user(self, identifier: str) -> Optional[str]:
        """
        Authenticate user by email or phone.

        Args:
            identifier: Email or phone number

        Returns:
            User ID if found, None otherwise
        """
        for user_id, user_data in self.users.items():
            if user_data.get('email') == identifier or user_data.get('phone') == identifier:
                return user_id
        return None

    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get user profile by ID."""
        return self.users.get(user_id)

    def update_user_stats(self, user_id: str, report_valid: bool = True):
        """
        Update user statistics after report submission.

        Args:
            user_id: User ID
            report_valid: Whether the report was valid
        """
        if user_id in self.users:
            user = self.users[user_id]
            user['total_reports'] += 1
            if report_valid:
                user['valid_reports'] += 1
                # Update trust score
                accuracy = user['valid_reports'] / user['total_reports']
                user['trust_score'] = min(accuracy * 1.2, 1.0)  # Cap at 1.0

            self._save_users()

    def calculate_rewards(self, user_id: str, violations: list) -> float:
        """
        Calculate rewards for user based on violations reported.

        Args:
            user_id: User ID
            violations: List of violations

        Returns:
            Reward amount
        """
        if user_id not in self.users:
            return 0.0

        user = self.users[user_id]
        trust_score = user.get('trust_score', 1.0)

        # Base reward per violation
        base_reward = 10.0

        # Calculate total reward
        total_reward = len(violations) * base_reward * trust_score

        # Update rewards earned
        user['rewards_earned'] += total_reward
        self._save_users()

        return total_reward

    def generate_session_token(self, user_id: str) -> str:
        """
        Generate session token for user.

        Args:
            user_id: User ID

        Returns:
            Session token
        """
        token_data = f"{user_id}_{datetime.now().isoformat()}"
        token = hashlib.sha256(token_data.encode()).hexdigest()
        return token

    def validate_session_token(self, token: str, user_id: str) -> bool:
        """
        Validate session token.

        Args:
            token: Session token
            user_id: User ID

        Returns:
            True if valid, False otherwise
        """
        # Simple validation - in production, use proper JWT or similar
        expected_token = self.generate_session_token(user_id)
        return token == expected_token

    def get_leaderboard(self, limit: int = 10) -> list:
        """
        Get user leaderboard based on valid reports.

        Args:
            limit: Number of top users to return

        Returns:
            List of top users
        """
        sorted_users = sorted(
            self.users.values(),
            key=lambda x: (x.get('valid_reports', 0), x.get('trust_score', 0)),
            reverse=True
        )

        return sorted_users[:limit]