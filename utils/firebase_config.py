import os
import json
import firebase_admin
from firebase_admin import credentials, firestore, auth, storage
import streamlit as st
from typing import Optional

# Do not load from .env in deployment; rely on Streamlit secrets

# Set environment variables globally to prevent metadata service usage
# This must be done before any Google Cloud libraries are imported
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = ''
os.environ['GOOGLE_CLOUD_PROJECT'] = 'agriai-cbd8b'
os.environ['GOOGLE_AUTH_DISABLE_METADATA'] = 'true'
os.environ['GCE_METADATA_HOST'] = ''
os.environ['GCE_METADATA_ROOT'] = ''
os.environ['GCE_METADATA_TIMEOUT'] = '0'
os.environ['GOOGLE_CLOUD_DISABLE_METADATA'] = 'true'

# Additional environment variables to completely disable metadata service
os.environ['GOOGLE_AUTH_DISABLE_METADATA'] = 'true'
os.environ['GOOGLE_CLOUD_DISABLE_METADATA'] = 'true'
os.environ['GCE_METADATA_HOST'] = ''
os.environ['GCE_METADATA_ROOT'] = ''
os.environ['GCE_METADATA_TIMEOUT'] = '0'

# Monkey patch the Google Auth library at module level to prevent metadata service usage
try:
    import google.auth
    import google.auth.compute_engine
    import google.auth.transport.requests
    import google.auth.transport.grpc
    
    # Override the default credential discovery to never use metadata service
    original_default = google.auth.default
    def patched_default(scopes=None, request=None, default_scopes=None, quota_project_id=None, **kwargs):
        # Always return None to force explicit credential usage
        return None, None
    google.auth.default = patched_default
    
    # Disable compute engine credentials completely
    def disabled_compute_engine_credentials(*args, **kwargs):
        raise Exception("Compute Engine credentials disabled for Streamlit Cloud")
    google.auth.compute_engine.Credentials = disabled_compute_engine_credentials
    
    # Override the metadata service functions directly
    def disabled_metadata_get(*args, **kwargs):
        raise Exception("Metadata service disabled for Streamlit Cloud")
    
    # Patch the metadata module
    if hasattr(google.auth.compute_engine, '_metadata'):
        google.auth.compute_engine._metadata.get = disabled_metadata_get
        google.auth.compute_engine._metadata.get_service_account_info = disabled_metadata_get
    
    # Note: Do NOT override transport Request class; some libraries depend on it even with API key auth
    
except ImportError:
    pass

def initialize_firebase() -> bool:
    """Initialize Firebase Admin SDK
    
    Returns:
        bool: True if initialization successful, False otherwise
    """
    try:
        # Set environment variables to prevent metadata service usage
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = ''
        # Prefer project_id from Streamlit secrets
        project_id = None
        if hasattr(st, 'secrets') and 'firebase' in st.secrets:
            project_id = st.secrets.firebase.get('project_id')
        os.environ['GOOGLE_CLOUD_PROJECT'] = project_id or 'agriai-cbd8b'
        # Disable metadata service completely
        os.environ['GOOGLE_AUTH_DISABLE_METADATA'] = 'true'
        # Additional environment variables to prevent metadata service
        os.environ['GCE_METADATA_HOST'] = ''
        os.environ['GCE_METADATA_ROOT'] = ''
        # Force use of service account credentials
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'service_account'
        
        # Set additional environment variables to prevent metadata service usage
        os.environ['GCE_METADATA_TIMEOUT'] = '0'
        os.environ['GOOGLE_AUTH_DISABLE_METADATA'] = 'true'
        os.environ['GOOGLE_CLOUD_PROJECT'] = project_id or 'agriai-cbd8b'
        
        # Disable metadata service for all Google Cloud libraries
        os.environ['GOOGLE_CLOUD_DISABLE_METADATA'] = 'true'
        os.environ['GOOGLE_AUTH_DISABLE_METADATA'] = 'true'
        
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
            
            # Override the refresh method to prevent metadata service usage
            original_refresh = cred.refresh
            def custom_refresh(request):
                # Force use of service account credentials only
                return original_refresh(request)
            cred.refresh = custom_refresh
            
            # Get storage bucket from Streamlit secrets
            storage_bucket = None
            if hasattr(st, 'secrets') and 'firebase' in st.secrets:
                storage_bucket = st.secrets.firebase.get('firebase_storage_bucket')
            if not storage_bucket and firebase_creds.get('project_id'):
                storage_bucket = f"{firebase_creds.get('project_id')}.firebasestorage.app"
            
            # Initialize Firebase with explicit configuration
            firebase_admin.initialize_app(cred, {
                'storageBucket': storage_bucket,
                'projectId': firebase_creds.get(
                    'project_id', 'agriai-cbd8b'
                )
            })
            
            # Set the credentials as default for all Google Cloud services
            import google.auth
            project_id = firebase_creds.get('project_id', project_id or 'agriai-cbd8b')
            google.auth.default = lambda: (cred, project_id)
            
            # Monkey patch to prevent metadata service usage
            try:
                from google.auth import compute_engine
                # Override the metadata service to always fail
                def _disabled_metadata_get(*args, **kwargs):
                    raise Exception("Metadata service disabled for Streamlit Cloud")
                compute_engine._metadata.get = _disabled_metadata_get
                compute_engine._metadata.get_service_account_info = _disabled_metadata_get
                
                # Also patch the credentials class to prevent metadata service usage
                def _disabled_refresh(self, request):
                    raise Exception("Metadata service disabled for Streamlit Cloud")
                compute_engine.Credentials.refresh = _disabled_refresh
                
            except ImportError:
                pass
            
            # Additional monkey patching for Google Cloud libraries
            try:
                import google.auth.transport.requests
                # Override the default credential discovery
                original_default = google.auth.default
                def patched_default(scopes=None, request=None, default_scopes=None, quota_project_id=None, **kwargs):
                    # Return our service account credentials instead of trying metadata service
                    return (cred, project_id)
                google.auth.default = patched_default
            except ImportError:
                pass
            
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
        # Prefer Streamlit secrets exclusively in deployment
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
        # No environment fallback in deployment; return None to signal missing secrets
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
        # Ensure Firebase is initialized before creating the client
        if not firebase_admin._apps:
            initialize_firebase()
        # Return Firestore client from the initialized Firebase app
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
        # Get credentials explicitly to avoid metadata service
        firebase_creds = get_firebase_credentials()
        if firebase_creds:
            cred = credentials.Certificate(firebase_creds)
            return storage.bucket(credentials=cred)
        else:
            # Fallback to default bucket (should work if Firebase is initialized)
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
                        print("Default admin code already exists")
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
        print("Default admin code created successfully")
        return default_code
        
    except Exception as e:
        print(f"Error initializing admin codes: {str(e)}")
        return None