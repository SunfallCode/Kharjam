"""Pending update service for email and phone number changes"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from app.core.redis import get_cache

logger = logging.getLogger(__name__)


class PendingUpdateService:
    """Service for managing pending email/phone updates"""

    @staticmethod
    def cache_pending_update(user_id: str, field: str, value: str) -> Dict[str, Any]:
        """Cache a pending update for 30 minutes"""
        if field not in ["email", "phone_number"]:
            raise ValueError("Field must be either 'email' or 'phone_number'")

        cache_key = f"pending_update:{user_id}:{field}"
        update_data = {
            "value": value,
            "created_at": datetime.utcnow().isoformat(),
            "field": field
        }

        cache = get_cache()
        success = cache.set(cache_key, update_data, expire=1800)  # 30 minutes

        if not success:
            logger.warning(f"Failed to cache pending update for user {user_id}, field {field}")

        return {
            "user_id": user_id,
            "field": field,
            "value": value,
            "expires_in": 1800,
            "cached": success
        }

    @staticmethod
    def get_pending_update(user_id: str, field: str) -> Optional[Dict[str, Any]]:
        """Get pending update if it exists and hasn't expired"""
        cache_key = f"pending_update:{user_id}:{field}"
        cache = get_cache()
        update_data = cache.get(cache_key)

        if not update_data:
            return None

        # Check expiration
        created_at_str = update_data.get("created_at")
        if created_at_str:
            try:
                created_at = datetime.fromisoformat(created_at_str)
                if datetime.utcnow() - created_at > timedelta(minutes=30):
                    cache.delete(cache_key)
                    return None
            except (ValueError, TypeError):
                cache.delete(cache_key)
                return None

        return update_data

    @staticmethod
    def clear_pending_update(user_id: str, field: str) -> bool:
        """Clear a pending update after successful verification"""
        cache_key = f"pending_update:{user_id}:{field}"
        cache = get_cache()
        return cache.delete(cache_key)

    @staticmethod
    def get_all_pending_updates(user_id: str) -> Dict[str, Dict[str, Any]]:
        """Get all pending updates for a user"""
        cache = get_cache()
        updates = {}

        # Check for email update
        email_update = PendingUpdateService.get_pending_update(user_id, "email")
        if email_update:
            updates["email"] = email_update

        # Check for phone update
        phone_update = PendingUpdateService.get_pending_update(user_id, "phone_number")
        if phone_update:
            updates["phone_number"] = phone_update

        return updates
