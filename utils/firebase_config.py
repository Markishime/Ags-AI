import os
import json
import firebase_admin
from firebase_admin import credentials, firestore, auth, storage
import streamlit as st
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def initialize_firebase() -> bool:
    """Initialize Firebase Admin SDK
    
    Returns:
        bool: True if initialization successful, False otherwise
    """
    try:
        # Set environment variables to prevent metadata service usage
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = ''
        os.environ['GOOGLE_CLOUD_PROJECT'] = \
            'agriai-cbd8b'
        
        # Check if Firebase is already initialized
        if firebase_admin._apps:
            print("Firebase already initialized")
            return True
        
        print("Initializing Firebase...")
        
        # Get Firebase credentials from environment or Streamlit secrets
        firebase_creds = get_firebase_credentials()
        
        if firebase_creds:
            print(f"Found Firebase credentials for project: {firebase_creds.get('project_id', 'unknown')}")
            
            # Initialize Firebase with credentials
            # Create credentials object with explicit project ID
            cred = credentials.Certificate(firebase_creds)
            # Force the credentials to use the project ID from the service account
            cred.project_id = firebase_creds.get('project_id', 'agriai-cbd8b')
            
            # Get storage bucket from secrets or environment
            storage_bucket = None
            if hasattr(st, 'secrets') and 'firebase' in st.secrets:
                storage_bucket = st.secrets.firebase.get('firebase_storage_bucket')
            
            if not storage_bucket:
                storage_bucket = os.getenv('FIREBASE_STORAGE_BUCKET', 'agriai-cbd8b.firebasestorage.app')
            
            # Initialize Firebase with explicit configuration
            firebase_admin.initialize_app(cred, {
                'storageBucket': storage_bucket,
                'projectId': firebase_creds.get(
                    'project_id', 'agriai-cbd8b'
                )
            })
            
            print(f"Firebase initialized successfully with storage bucket: {storage_bucket}")
            return True
        else:
            error_msg = "Firebase credentials not found. Please check your environment variables or Streamlit secrets."
            st.error(error_msg)
            print(error_msg)
            return False
            
    except Exception as e:
        error_msg = f"Failed to initialize Firebase: {str(e)}"
        st.error("Failed to initialize Firebase. Please check your configuration.")
        print(error_msg)
        print(f"Firebase initialization error details: {type(e).__name__}: {e}")
        return False

def get_firebase_credentials() -> Optional[dict]:
    """Get Firebase credentials from environment variables or Streamlit secrets
    
    Returns:
        dict: Firebase service account credentials or None
    """
    try:
        # First, try to get from FIREBASE_SERVICE_ACCOUNT_KEY environment variable
        service_account_key = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY')
        if service_account_key:
            try:
                # Remove surrounding quotes if present
                service_account_key = service_account_key.strip("'\"")
                credentials = json.loads(service_account_key)
                print("Successfully loaded Firebase credentials from FIREBASE_SERVICE_ACCOUNT_KEY")
                return credentials
            except json.JSONDecodeError as e:
                print(f"Error parsing FIREBASE_SERVICE_ACCOUNT_KEY: {e}")
                print(f"Raw key (first 100 chars): {service_account_key[:100]}...")
        
        # Try to get from Streamlit secrets
        try:
            if hasattr(st, 'secrets') and 'firebase' in st.secrets:
                print("Loading Firebase credentials from Streamlit secrets")
                firebase_secrets = st.secrets.firebase
                
                # Construct credentials from individual fields in secrets
                firebase_config = {
                    "type": firebase_secrets.get('firebase_type', 'service_account'),
                    "project_id": firebase_secrets.get('project_id'),
                    "private_key_id": firebase_secrets.get('firebase_private_key_id'),
                    "private_key": firebase_secrets.get('firebase_private_key', '').replace('\\n', '\n'),
                    "client_email": firebase_secrets.get('firebase_client_email'),
                    "client_id": firebase_secrets.get('firebase_client_id'),
                    "auth_uri": firebase_secrets.get('firebase_auth_uri', 'https://accounts.google.com/o/oauth2/auth'),
                    "token_uri": firebase_secrets.get('firebase_token_uri', 'https://oauth2.googleapis.com/token'),
                    "auth_provider_x509_cert_url": firebase_secrets.get('firebase_auth_provider_x509_cert_url', 'https://www.googleapis.com/oauth2/v1/certs'),
                    "client_x509_cert_url": firebase_secrets.get('firebase_client_x509_cert_url'),
                    "universe_domain": firebase_secrets.get('firebase_universe_domain', 'googleapis.com')
                }
                
                # Check if all required fields are present
                required_fields = ['project_id', 'private_key', 'client_email']
                missing_fields = [field for field in required_fields if not firebase_config.get(field)]
                
                if not missing_fields:
                    print("Successfully loaded Firebase credentials from Streamlit secrets")
                    return firebase_config
                else:
                    print(f"Missing required Firebase credentials in secrets: {missing_fields}")
                    
            elif hasattr(st, 'secrets') and 'FIREBASE_SERVICE_ACCOUNT_KEY' in st.secrets:
                return dict(st.secrets['FIREBASE_SERVICE_ACCOUNT_KEY'])
        except Exception as e:
            print(f"Error loading Firebase credentials from Streamlit secrets: {e}")
        
        # Fallback: construct from individual environment variables
        print("Attempting to construct Firebase credentials from individual environment variables")
        firebase_config = {
            "type": os.getenv('FIREBASE_TYPE', 'service_account'),
            "project_id": os.getenv('FIREBASE_PROJECT_ID'),
            "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
            "private_key": os.getenv('FIREBASE_PRIVATE_KEY', '').replace('\\n', '\n'),
            "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
            "client_id": os.getenv('FIREBASE_CLIENT_ID'),
            "auth_uri": os.getenv('FIREBASE_AUTH_URI', 'https://accounts.google.com/o/oauth2/auth'),
            "token_uri": os.getenv('FIREBASE_TOKEN_URI', 'https://oauth2.googleapis.com/token'),
            "auth_provider_x509_cert_url": os.getenv('FIREBASE_AUTH_PROVIDER_X509_CERT_URL', 'https://www.googleapis.com/oauth2/v1/certs'),
            "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_X509_CERT_URL'),
            "universe_domain": os.getenv('FIREBASE_UNIVERSE_DOMAIN', 'googleapis.com')
        }
        
        # Check if all required fields are present
        required_fields = ['project_id', 'private_key', 'client_email']
        missing_fields = [field for field in required_fields if not firebase_config.get(field)]
        
        if not missing_fields:
            print("Successfully constructed Firebase credentials from environment variables")
            return firebase_config
        else:
            print(f"Missing required Firebase credentials: {missing_fields}")
        
        return None
        
    except Exception as e:
        st.error(f"Error loading Firebase credentials: {str(e)}")
        print(f"Error loading Firebase credentials: {e}")
        return None

def get_firestore_client():
    """Get Firestore client instance
    
    Returns:
        firestore.Client: Firestore client instance
    """
    try:
        return firestore.client()
    except Exception as e:
        # Firebase initialization handled elsewhere, silently return None
        return None

def get_storage_bucket():
    """Get Firebase Storage bucket instance
    
    Returns:
        storage.Bucket: Storage bucket instance
    """
    try:
        return storage.bucket()
    except Exception as e:
        st.error(f"Failed to get Storage bucket: {str(e)}")
        return None

def get_auth_client():
    """Get Firebase Auth client
    
    Returns:
        auth: Firebase Auth client
    """
    try:
        return auth
    except Exception as e:
        st.error(f"Failed to get Auth client: {str(e)}")
        return None

# Collection names
COLLECTIONS = {
    'users': 'users',
    'analyses': 'analyses',
    'analysis_results': 'analysis_results',
    'analysis_prompts': 'analysis_prompts',
    'feedback': 'feedback',
    'admin_requests': 'admin_requests',
    'admin_codes': 'admin_codes',
    'reference_documents': 'reference_documents',
    'ai_configuration': 'ai_configuration',
    'reference_materials': 'reference_materials',
    'output_formats': 'output_formats',
    'tagging_config': 'tagging_config',
    'prompt_templates': 'prompt_templates'
}

# Default MPOB standards
DEFAULT_MPOB_STANDARDS = {
    'leaf_standards': {
        'N': {'min': 2.4, 'max': 2.8, 'unit': '%', 'optimal': 2.6},
        'P': {'min': 0.15, 'max': 0.18, 'unit': '%', 'optimal': 0.165},
        'K': {'min': 0.9, 'max': 1.2, 'unit': '%', 'optimal': 1.05},
        'Mg': {'min': 0.25, 'max': 0.35, 'unit': '%', 'optimal': 0.3},
        'Ca': {'min': 0.5, 'max': 0.7, 'unit': '%', 'optimal': 0.6},
        'B': {'min': 15, 'max': 25, 'unit': 'mg/kg', 'optimal': 20},
        'Cu': {'min': 4, 'max': 8, 'unit': 'mg/kg', 'optimal': 6},
        'Zn': {'min': 15, 'max': 25, 'unit': 'mg/kg', 'optimal': 20}
    },
    'soil_standards': {
        'pH': {'min': 4.5, 'max': 5.5, 'unit': '', 'optimal': 5.0},
        'Nitrogen': {'min': 0.08, 'max': 0.15, 'unit': '%', 'optimal': 0.12},
        'Organic_Carbon': {'min': 0.6, 'max': 1.2, 'unit': '%', 'optimal': 0.9},
        'Total_P': {'min': 50, 'max': 100, 'unit': 'mg/kg', 'optimal': 75},
        'Available_P': {'min': 3, 'max': 8, 'unit': 'mg/kg', 'optimal': 5},
        'Exch_K': {'min': 0.08, 'max': 0.15, 'unit': 'meq%', 'optimal': 0.12},
        'Exch_Ca': {'min': 0.2, 'max': 0.5, 'unit': 'meq%', 'optimal': 0.35},
        'Exch_Mg': {'min': 0.15, 'max': 0.25, 'unit': 'meq%', 'optimal': 0.2},
        'CEC': {'min': 5.0, 'max': 15.0, 'unit': '', 'optimal': 10.0}
    }
}

def initialize_admin_codes():
    """Initialize default admin codes in Firestore"""
    import secrets
    import string
    from datetime import datetime, timedelta, timezone
    
    try:
        db = get_firestore_client()
        if not db:
            print("Failed to get Firestore client")
            return None
        
        admin_codes_ref = db.collection(COLLECTIONS['admin_codes'])
        
        # Check if default admin code already exists
        existing_codes = admin_codes_ref.where('is_default', '==', True).limit(1).get()
        
        if existing_codes:
            # Return existing default code
            for doc in existing_codes:
                code_data = doc.to_dict()
                expires_at = code_data.get('expires_at')
                # Handle both timezone-aware and naive datetime objects
                if expires_at:
                    if hasattr(expires_at, 'tzinfo') and expires_at.tzinfo is not None:
                        current_time = datetime.now(timezone.utc)
                    else:
                        current_time = datetime.now()
                    
                    if expires_at > current_time:
                        print(f"Default admin code already exists: {code_data['code']}")
                        return code_data['code']
        
        # Generate new default admin code
        alphabet = string.ascii_uppercase + string.digits
        default_code = ''.join(secrets.choice(alphabet) for _ in range(8))
        
        # Set expiration to 1 year from now (timezone-aware)
        current_time = datetime.now(timezone.utc)
        expires_at = current_time + timedelta(days=365)
        
        # Store in Firestore
        admin_code_data = {
            'code': default_code,
            'is_default': True,
            'created_at': current_time,
            'expires_at': expires_at,
            'used': False,
            'created_by': 'system',
            'description': 'Default admin registration code'
        }
        
        admin_codes_ref.add(admin_code_data)
        print(f"Default admin code created: {default_code}")
        return default_code
        
    except Exception as e:
        print(f"Error initializing admin codes: {str(e)}")
        return None