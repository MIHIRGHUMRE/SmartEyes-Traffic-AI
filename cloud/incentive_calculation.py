from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path

class IncentiveCalculator:
    """Calculate incentives and rewards for users."""

    def __init__(self, config_path: str = 'config/incentive_config.json'):
        """
        Initialize incentive calculator.

        Args:
            config_path: Path to incentive configuration
        """
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: str) -> Dict:
        """Load incentive configuration."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return self._default_config()

    def _default_config(self) -> Dict:
        """Default incentive configuration."""
        return {
            'base_reward_per_violation': 10.0,
            'bonus_multipliers': {
                'high_confidence': 1.5,  # OCR confidence > 0.9
                'multiple_violations': 1.2,  # Same vehicle, multiple violations
                'peak_hours': 1.3,  # 8-10 AM, 5-8 PM
                'trusted_user': 1.1  # Trust score > 0.8
            },
            'penalties': {
                'false_report': -50.0,
                'duplicate_report': -10.0
            },
            'monthly_limits': {
                'max_rewards': 5000.0,
                'max_reports': 100
            },
            'tier_bonuses': {
                'bronze': {'min_reports': 10, 'bonus': 0.05},  # 5% bonus
                'silver': {'min_reports': 50, 'bonus': 0.10},  # 10% bonus
                'gold': {'min_reports': 100, 'bonus': 0.15}    # 15% bonus
            }
        }

    def calculate_reward(self, violation_data: Dict, user_profile: Dict) -> Dict:
        """
        Calculate reward for a violation report.

        Args:
            violation_data: Violation information
            user_profile: User profile data

        Returns:
            Reward calculation details
        """
        base_reward = self.config['base_reward_per_violation']
        multipliers = []

        # Base reward for each violation
        total_reward = base_reward * len(violation_data.get('violations', []))

        # Apply multipliers
        multipliers_data = self._calculate_multipliers(violation_data, user_profile)
        total_multiplier = 1.0

        for multiplier_name, multiplier_value in multipliers_data.items():
            total_multiplier *= multiplier_value
            multipliers.append({
                'type': multiplier_name,
                'value': multiplier_value
            })

        total_reward *= total_multiplier

        # Apply tier bonuses
        tier_bonus = self._calculate_tier_bonus(user_profile)
        if tier_bonus > 0:
            total_reward *= (1 + tier_bonus)
            multipliers.append({
                'type': 'tier_bonus',
                'value': 1 + tier_bonus
            })

        # Check monthly limits
        monthly_limit_check = self._check_monthly_limits(user_profile, total_reward)

        if not monthly_limit_check['within_limit']:
            total_reward = monthly_limit_check['adjusted_reward']

        return {
            'total_reward': total_reward,
            'base_reward': base_reward,
            'multipliers': multipliers,
            'monthly_limit_applied': not monthly_limit_check['within_limit'],
            'breakdown': {
                'violations_count': len(violation_data.get('violations', [])),
                'multiplier_total': total_multiplier,
                'tier_bonus': tier_bonus
            }
        }

    def _calculate_multipliers(self, violation_data: Dict, user_profile: Dict) -> Dict:
        """Calculate applicable multipliers."""
        multipliers = {}

        # High confidence multiplier
        ocr_confidence = violation_data.get('license_plate', {}).get('confidence', 0)
        if ocr_confidence > 0.9:
            multipliers['high_confidence'] = self.config['bonus_multipliers']['high_confidence']

        # Multiple violations multiplier
        violations_count = len(violation_data.get('violations', []))
        if violations_count > 1:
            multipliers['multiple_violations'] = self.config['bonus_multipliers']['multiple_violations']

        # Peak hours multiplier
        if self._is_peak_hour(violation_data.get('timestamp')):
            multipliers['peak_hours'] = self.config['bonus_multipliers']['peak_hours']

        # Trusted user multiplier
        trust_score = user_profile.get('trust_score', 0)
        if trust_score > 0.8:
            multipliers['trusted_user'] = self.config['bonus_multipliers']['trusted_user']

        return multipliers

    def _is_peak_hour(self, timestamp: datetime) -> bool:
        """Check if timestamp is during peak hours."""
        if not timestamp:
            return False

        hour = timestamp.hour
        # Peak hours: 8-10 AM, 5-8 PM
        return (8 <= hour <= 10) or (17 <= hour <= 20)

    def _calculate_tier_bonus(self, user_profile: Dict) -> float:
        """Calculate tier bonus based on user performance."""
        valid_reports = user_profile.get('valid_reports', 0)

        if valid_reports >= self.config['tier_bonuses']['gold']['min_reports']:
            return self.config['tier_bonuses']['gold']['bonus']
        elif valid_reports >= self.config['tier_bonuses']['silver']['min_reports']:
            return self.config['tier_bonuses']['silver']['bonus']
        elif valid_reports >= self.config['tier_bonuses']['bronze']['min_reports']:
            return self.config['tier_bonuses']['bronze']['bonus']

        return 0.0

    def _check_monthly_limits(self, user_profile: Dict, reward_amount: float) -> Dict:
        """Check if reward is within monthly limits."""
        # In a real implementation, this would check actual monthly earnings
        # For demo, we'll assume limits are not exceeded
        return {
            'within_limit': True,
            'adjusted_reward': reward_amount
        }

    def calculate_bulk_rewards(self, violations_list: List[Dict], user_profiles: Dict) -> List[Dict]:
        """
        Calculate rewards for multiple violation reports.

        Args:
            violations_list: List of violation data
            user_profiles: Dictionary of user profiles

        Returns:
            List of reward calculations
        """
        rewards = []
        for violation_data in violations_list:
            user_id = violation_data.get('user_id')
            user_profile = user_profiles.get(user_id, {})

            reward_calc = self.calculate_reward(violation_data, user_profile)
            rewards.append({
                'violation_id': violation_data.get('evidence_id'),
                'user_id': user_id,
                'reward': reward_calc
            })

        return rewards

    def get_user_tier(self, user_profile: Dict) -> str:
        """Get user tier based on performance."""
        valid_reports = user_profile.get('valid_reports', 0)

        if valid_reports >= self.config['tier_bonuses']['gold']['min_reports']:
            return 'gold'
        elif valid_reports >= self.config['tier_bonuses']['silver']['min_reports']:
            return 'silver'
        elif valid_reports >= self.config['tier_bonuses']['bronze']['min_reports']:
            return 'bronze'

        return 'basic'

    def get_leaderboard_rewards(self, users: List[Dict], limit: int = 10) -> List[Dict]:
        """
        Get leaderboard of users by rewards earned.

        Args:
            users: List of user profiles
            limit: Number of top users

        Returns:
            Leaderboard data
        """
        sorted_users = sorted(
            users,
            key=lambda x: x.get('rewards_earned', 0),
            reverse=True
        )

        leaderboard = []
        for i, user in enumerate(sorted_users[:limit]):
            leaderboard.append({
                'rank': i + 1,
                'user_id': user.get('id'),
                'name': user.get('name', 'Anonymous'),
                'rewards_earned': user.get('rewards_earned', 0),
                'tier': self.get_user_tier(user)
            })

        return leaderboard