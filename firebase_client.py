"""
Firebase Firestore Client Module
Handles all Firestore database operations for the bot
"""
import firebase_admin
from firebase_admin import credentials, firestore
import json
import os
from typing import Dict, Any, Optional
from utilities.logger import bot_logger

# Initialize Firebase app (will be initialized on first use)
db = None
app_initialized = False


def initialize_firebase():
    """Initialize Firebase with credentials from environment variables"""
    global db, app_initialized

    if app_initialized:
        return db

    try:
        # Check if app already exists
        if firebase_admin._apps:
            if 'trading-vault-bot' in firebase_admin._apps:
                app = firebase_admin.get_app('trading-vault-bot')
                db = firestore.client(app=app)
                app_initialized = True
                bot_logger.info("Firebase Firestore already initialized, using existing instance")
                return db

        # Get Firebase credentials from environment
        firebase_creds = {
            "type": "service_account",
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID", ""),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n"),
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL", ""),
            "client_id": os.getenv("FIREBASE_CLIENT_ID", ""),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/{client_email}"
        }

        # Check if we have proper credentials
        if not firebase_creds["private_key"] or not firebase_creds["client_email"]:
            bot_logger.error("Firebase service account credentials not found in .env file.")
            bot_logger.error("Please add the following to your .env file:")
            bot_logger.error("  FIREBASE_PROJECT_ID=trading-vault-9e015")
            bot_logger.error("  FIREBASE_PRIVATE_KEY_ID=your_private_key_id")
            bot_logger.error("  FIREBASE_PRIVATE_KEY=your_private_key_with_newlines")
            bot_logger.error("  FIREBASE_CLIENT_EMAIL=your_service_account_email")
            bot_logger.error("  FIREBASE_CLIENT_ID=your_client_id")
            return None

        cred = credentials.Certificate(firebase_creds)
        app = firebase_admin.initialize_app(cred, name='trading-vault-bot')

        db = firestore.client(app=app)
        app_initialized = True
        bot_logger.info("Firebase Firestore initialized successfully")
        return db

    except Exception as e:
        bot_logger.error(f"Failed to initialize Firebase: {e}")
        return None


def get_db():
    """Get Firestore database instance"""
    global db
    if not app_initialized:
        db = initialize_firebase()
    if db:
        return db
    # Try to get existing db instance
    try:
        if 'trading-vault-bot' in firebase_admin._apps:
            app = firebase_admin.get_app('trading-vault-bot')
            return firestore.client(app=app)
    except:
        pass
    return None


# Generic Firestore operations
async def get_document(collection: str, document_id: str) -> Optional[Dict[str, Any]]:
    """Get a document from Firestore"""
    try:
        db_instance = get_db()
        if not db_instance:
            return None

        doc_ref = db_instance.collection(collection).document(document_id)
        doc = doc_ref.get()

        if doc.exists:
            return doc.to_dict()
        return None
    except Exception as e:
        bot_logger.error(f"Error getting document {document_id} from {collection}: {e}")
        return None


async def set_document(collection: str, document_id: str, data: Dict[str, Any]) -> bool:
    """Set a document in Firestore (creates or overwrites)"""
    try:
        db_instance = get_db()
        if not db_instance:
            return False

        doc_ref = db_instance.collection(collection).document(document_id)
        doc_ref.set(data)
        return True
    except Exception as e:
        bot_logger.error(f"Error setting document {document_id} in {collection}: {e}")
        return False


async def update_document(collection: str, document_id: str, data: Dict[str, Any]) -> bool:
    """Update a document in Firestore (merges with existing data)"""
    try:
        db_instance = get_db()
        if not db_instance:
            return False

        doc_ref = db_instance.collection(collection).document(document_id)
        doc_ref.update(data)
        return True
    except Exception as e:
        bot_logger.error(f"Error updating document {document_id} in {collection}: {e}")
        return False


async def delete_document(collection: str, document_id: str) -> bool:
    """Delete a document from Firestore"""
    try:
        db_instance = get_db()
        if not db_instance:
            return False

        doc_ref = db_instance.collection(collection).document(document_id)
        doc_ref.delete()
        return True
    except Exception as e:
        bot_logger.error(f"Error deleting document {document_id} from {collection}: {e}")
        return False


async def get_collection(collection: str) -> Dict[str, Any]:
    """Get all documents from a collection"""
    try:
        db_instance = get_db()
        if not db_instance:
            return {}

        docs = db_instance.collection(collection).stream()
        result = {}
        for doc in docs:
            result[doc.id] = doc.to_dict()
        return result
    except Exception as e:
        bot_logger.error(f"Error getting collection {collection}: {e}")
        return {}


async def collection_exists(collection: str) -> bool:
    """Check if a collection exists"""
    try:
        db_instance = get_db()
        if not db_instance:
            return False

        docs = db_instance.collection(collection).limit(1).stream()
        return any(True for _ in docs)
    except Exception as e:
        bot_logger.error(f"Error checking collection {collection}: {e}")
        return False


# Specific data operations for the bot
async def get_banner_config() -> Dict[str, Any]:
    """Get banner configuration"""
    default_config = {
        "ticket_creation": True,
        "purchase_creation": True,
        "ticket_controls": True,
        "payment_info": True,
        "rating": True,
        "vouch": True,
        "config": True,
        "panel": True,
        "general": True
    }
    config = await get_document("config", "banner_config")
    return config if config else default_config


async def set_banner_config(config: Dict[str, Any]) -> bool:
    """Set banner configuration"""
    return await set_document("config", "banner_config", config)


async def get_welcome_config() -> Dict[str, Any]:
    """Get welcome configuration"""
    default_config = {
        "welcome_enabled": False,
        "welcome_channel_id": 0,
        "welcome_message": "Welcome {user} to the server!",
        "goodbye_enabled": False,
        "goodbye_channel_id": 0,
        "goodbye_message": "Goodbye {user}!",
        "styled_welcome": False,
        "welcome_image": "",
        "thumbnail_image": ""
    }
    config = await get_document("config", "welcome_config")
    return config if config else default_config


async def set_welcome_config(config: Dict[str, Any]) -> bool:
    """Set welcome configuration"""
    return await set_document("config", "welcome_config", config)


async def get_giveaways() -> Dict[str, Any]:
    """Get all giveaways"""
    return await get_collection("giveaways")


async def set_giveaway(giveaway_id: str, data: Dict[str, Any]) -> bool:
    """Set a giveaway"""
    return await set_document("giveaways", giveaway_id, data)


async def delete_giveaway(giveaway_id: str) -> bool:
    """Delete a giveaway"""
    return await delete_document("giveaways", giveaway_id)


async def get_invites() -> Dict[str, Any]:
    """Get all invites"""
    return await get_collection("invites")


async def set_invite(user_id: str, data: Dict[str, Any]) -> bool:
    """Set invite data for a user"""
    return await set_document("invites", user_id, data)


async def get_invite_state() -> Dict[str, Any]:
    """Get invite state"""
    state = await get_document("config", "invite_state")
    return state if state else {}


async def set_invite_state(state: Dict[str, Any]) -> bool:
    """Set invite state"""
    return await set_document("config", "invite_state", state)


async def get_vouches() -> Dict[str, Any]:
    """Get all vouches"""
    return await get_collection("vouches")


async def set_vouch(user_id: str, data: Dict[str, Any]) -> bool:
    """Set vouch data for a user"""
    return await set_document("vouches", user_id, data)


async def get_store_config() -> Dict[str, Any]:
    """Get store configuration"""
    config = await get_document("config", "store_config")
    return config if config else {}


async def set_store_config(config: Dict[str, Any]) -> bool:
    """Set store configuration"""
    return await set_document("config", "store_config", config)


async def get_store_data() -> Dict[str, Any]:
    """Get store data"""
    data = await get_document("config", "store_data")
    return data if data else {}


async def set_store_data(data: Dict[str, Any]) -> bool:
    """Set store data"""
    return await set_document("config", "store_data", data)
