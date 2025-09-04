import streamlit as st
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from firebase_admin import auth, firestore
from firebase_config import get_firestore_client, COLLECTIONS

class AuthManager:
    """Handle user authentication and management"""
    
    def __init__(self):
        pass  # Defer any Firestore operations until after Firebase is initialized
    
    def _get_db(self):
        """Get Firestore client with proper error handling"""
        db = get_firestore_client()
        if not db:
            raise Exception("Failed to get Firestore client. Firebase may not be initialized.")
        return db
    
    def _verify_admin_code(self, admin_code: str) -> bool:
        """Verify admin code from Firestore
        
        Args:
            admin_code: Admin access code to verify
            
        Returns:
            bool: True if code is valid and not expired, False otherwise
        """
        try:
            from datetime import timezone
            db = self._get_db()
            admin_codes_ref = db.collection(COLLECTIONS['admin_codes'])
            
            # Find matching admin code
            matching_codes = admin_codes_ref.where('code', '==', admin_code).limit(1).get()
            
            for doc in matching_codes:
                code_data = doc.to_dict()
                
                # Check if code is expired
                expires_at = code_data.get('expires_at')
                if expires_at:
                    # Handle both timezone-aware and naive datetime objects
                    if hasattr(expires_at, 'tzinfo') and expires_at.tzinfo is not None:
                        current_time = datetime.now(timezone.utc)
                    else:
                        current_time = datetime.now()
                    
                    if expires_at <= current_time:
                        return False
                
                # Check if code is already used (optional - you can remove this if codes can be reused)
                if code_data.get('used', False):
                    return False
                
                return True
            
            return False  # Code not found
            
        except Exception as e:
            print(f"Error verifying admin code: {str(e)}")
            return False
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user login
        
        Args:
            email: User email
            password: User password
            
        Returns:
            dict: Login result with success status and user info
        """
        try:
            # Get user from Firestore
            db = self._get_db()
            users_ref = db.collection(COLLECTIONS['users'])
            user_query = users_ref.where('email', '==', email.lower()).limit(1)
            users = user_query.get()
            
            if not users:
                return {'success': False, 'message': 'User not found'}
            
            user_doc = users[0]
            user_data = user_doc.to_dict()
            
            # Verify password
            if self._verify_password(password, user_data.get('password_hash', '')):
                # Check if account is active
                if not user_data.get('is_active', True):
                    return {'success': False, 'message': 'Account is deactivated'}
                
                # Update last login
                user_doc.reference.update({
                    'last_login': datetime.now(),
                    'login_count': user_data.get('login_count', 0) + 1
                })
                
                # Return user info
                user_info = {
                    'uid': user_doc.id,
                    'email': user_data['email'],
                    'name': user_data['name'],
                    'role': user_data.get('role', 'user'),
                    'company': user_data.get('company', ''),
                    'created_at': user_data.get('created_at'),
                    'last_login': datetime.now()
                }
                
                return {'success': True, 'user_info': user_info, 'message': 'Login successful'}
            else:
                return {'success': False, 'message': 'Invalid password'}
                
        except Exception as e:
            return {'success': False, 'message': f'Login error: {str(e)}'}
    
    def signup(self, email: str, password: str, name: str, company: str = '') -> Dict[str, Any]:
        """Register new user
        
        Args:
            email: User email
            password: User password
            name: User full name
            company: User company (optional)
            
        Returns:
            dict: Signup result with success status
        """
        try:
            # Validate input
            if len(password) < 6:
                return {'success': False, 'message': 'Password must be at least 6 characters'}
            
            # Check if user already exists
            db = self._get_db()
            users_ref = db.collection(COLLECTIONS['users'])
            existing_user = users_ref.where('email', '==', email.lower()).limit(1).get()
            
            if existing_user:
                return {'success': False, 'message': 'User already exists with this email'}
            
            # Create user document
            user_data = {
                'email': email.lower(),
                'name': name,
                'company': company,
                'password_hash': self._hash_password(password),
                'role': 'user',
                'is_active': True,
                'created_at': datetime.now(),
                'last_login': None,
                'login_count': 0,
                'analyses_count': 0
            }
            
            # Add user to Firestore
            doc_ref = users_ref.add(user_data)
            
            return {'success': True, 'message': 'Account created successfully'}
            
        except Exception as e:
            return {'success': False, 'message': f'Signup error: {str(e)}'}
    
    def admin_signup_with_code(self, email: str, password: str, name: str, organization: str, admin_code: str) -> Dict[str, Any]:
        """Register new admin user
        
        Args:
            email: Admin email
            password: Admin password
            name: Admin full name
            organization: Admin organization
            admin_code: Admin access code
            
        Returns:
            dict: Admin signup result
        """
        try:
            # Verify admin access code from Firestore
            if not self._verify_admin_code(admin_code):
                return {'success': False, 'message': 'Invalid or expired admin access code'}
            
            # Validate input
            if len(password) < 8:
                return {'success': False, 'message': 'Admin password must be at least 8 characters'}
            
            # Check if user already exists
            db = self._get_db()
            users_ref = db.collection(COLLECTIONS['users'])
            existing_user = users_ref.where('email', '==', email.lower()).limit(1).get()
            
            if existing_user:
                return {'success': False, 'message': 'User already exists with this email'}
            
            # Create admin request document
            admin_request_data = {
                'email': email.lower(),
                'name': name,
                'organization': organization,
                'password_hash': self._hash_password(password),
                'status': 'approved',  # Auto-approve for demo
                'requested_at': datetime.now(),
                'approved_at': datetime.now(),
                'approved_by': 'system'
            }
            
            # Add to admin requests collection
            admin_requests_ref = db.collection(COLLECTIONS['admin_requests'])
            admin_requests_ref.add(admin_request_data)
            
            # Create admin user directly (for demo purposes)
            user_data = {
                'email': email.lower(),
                'name': name,
                'company': organization,
                'password_hash': self._hash_password(password),
                'role': 'admin',
                'is_active': True,
                'created_at': datetime.now(),
                'last_login': None,
                'login_count': 0,
                'analyses_count': 0
            }
            
            # Add admin user to Firestore
            users_ref.add(user_data)
            
            return {'success': True, 'message': 'Admin account created successfully'}
            
        except Exception as e:
            return {'success': False, 'message': f'Admin signup error: {str(e)}'}
    
    def admin_signup(self, email: str, password: str, name: str, organization: str = '') -> Dict[str, Any]:
        """Register new admin user without admin code requirement
        
        Args:
            email: Admin email
            password: Admin password
            name: Admin full name
            organization: Admin organization (optional)
            
        Returns:
            dict: Admin signup result
        """
        try:
            # Validate input
            if len(password) < 8:
                return {'success': False, 'message': 'Admin password must be at least 8 characters'}
            
            if not name.strip():
                return {'success': False, 'message': 'Name is required'}
            
            if not email.strip():
                return {'success': False, 'message': 'Email is required'}
            
            # Check if user already exists
            db = self._get_db()
            users_ref = db.collection(COLLECTIONS['users'])
            existing_user = users_ref.where('email', '==', email.lower()).limit(1).get()
            
            if existing_user:
                return {'success': False, 'message': 'User already exists with this email'}
            
            # Create admin request document
            admin_request_data = {
                'email': email.lower(),
                'name': name,
                'organization': organization,
                'password_hash': self._hash_password(password),
                'status': 'approved',  # Auto-approve for demo
                'requested_at': datetime.now(),
                'approved_at': datetime.now(),
                'approved_by': 'system'
            }
            
            # Add to admin requests collection
            admin_requests_ref = db.collection(COLLECTIONS['admin_requests'])
            admin_requests_ref.add(admin_request_data)
            
            # Create admin user directly
            user_data = {
                'email': email.lower(),
                'name': name,
                'company': organization,
                'password_hash': self._hash_password(password),
                'role': 'admin',
                'is_active': True,
                'created_at': datetime.now(),
                'last_login': None,
                'login_count': 0,
                'analyses_count': 0
            }
            
            # Add admin user to Firestore
            users_ref.add(user_data)
            
            return {'success': True, 'message': 'Admin account created successfully'}
            
        except Exception as e:
            return {'success': False, 'message': f'Admin signup error: {str(e)}'}
    
    def reset_password(self, email: str) -> Dict[str, Any]:
        """Send password reset link
        
        Args:
            email: User email
            
        Returns:
            dict: Reset result
        """
        try:
            # Check if user exists
            db = self._get_db()
            users_ref = db.collection(COLLECTIONS['users'])
            user_query = users_ref.where('email', '==', email.lower()).limit(1)
            users = user_query.get()
            
            if not users:
                return {'success': False, 'message': 'User not found'}
            
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            reset_expires = datetime.now() + timedelta(hours=1)
            
            # Update user with reset token
            user_doc = users[0]
            user_doc.reference.update({
                'reset_token': reset_token,
                'reset_expires': reset_expires
            })
            
            # In a real application, you would send an email here
            # For demo purposes, we'll just return success
            return {'success': True, 'message': 'Password reset link sent to your email'}
            
        except Exception as e:
            return {'success': False, 'message': f'Reset error: {str(e)}'}
    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> Dict[str, Any]:
        """Change user password
        
        Args:
            user_id: User document ID
            old_password: Current password
            new_password: New password
            
        Returns:
            dict: Change password result
        """
        try:
            # Get user document
            db = self._get_db()
            user_ref = db.collection(COLLECTIONS['users']).document(user_id)
            user_doc = user_ref.get()
            
            if not user_doc.exists:
                return {'success': False, 'message': 'User not found'}
            
            user_data = user_doc.to_dict()
            
            # Verify old password
            if not self._verify_password(old_password, user_data.get('password_hash', '')):
                return {'success': False, 'message': 'Current password is incorrect'}
            
            # Validate new password
            if len(new_password) < 6:
                return {'success': False, 'message': 'New password must be at least 6 characters'}
            
            # Update password
            user_ref.update({
                'password_hash': self._hash_password(new_password),
                'password_changed_at': datetime.now()
            })
            
            return {'success': True, 'message': 'Password changed successfully'}
            
        except Exception as e:
            return {'success': False, 'message': f'Password change error: {str(e)}'}
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by document ID
        
        Args:
            user_id: User document ID
            
        Returns:
            dict: User data or None
        """
        try:
            db = self._get_db()
            user_ref = db.collection(COLLECTIONS['users']).document(user_id)
            user_doc = user_ref.get()
            
            if user_doc.exists:
                user_data = user_doc.to_dict()
                user_data['uid'] = user_doc.id
                return user_data
            
            return None
            
        except Exception as e:
            st.error(f"Error getting user: {str(e)}")
            return None
    
    def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile
        
        Args:
            user_id: User document ID
            updates: Fields to update
            
        Returns:
            dict: Update result
        """
        try:
            db = self._get_db()
            user_ref = db.collection(COLLECTIONS['users']).document(user_id)
            
            # Add timestamp
            updates['updated_at'] = datetime.now()
            
            # Update user document
            user_ref.update(updates)
            
            return {'success': True, 'message': 'Profile updated successfully'}
            
        except Exception as e:
            return {'success': False, 'message': f'Update error: {str(e)}'}
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt
        
        Args:
            password: Plain text password
            
        Returns:
            str: Hashed password
        """
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    def _verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify password against stored hash
        
        Args:
            password: Plain text password
            stored_hash: Stored password hash
            
        Returns:
            bool: True if password matches
        """
        try:
            if ':' not in stored_hash:
                return False
            
            salt, hash_part = stored_hash.split(':', 1)
            password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return password_hash == hash_part
            
        except Exception:
            return False
    
    def is_admin(self, user_info: Dict[str, Any]) -> bool:
        """Check if user is admin
        
        Args:
            user_info: User information dictionary
            
        Returns:
            bool: True if user is admin
        """
        return user_info.get('role') == 'admin'
    
    def _ensure_default_admin(self) -> None:
        """Ensure default admin user exists"""
        try:
            db = self._get_db()
            users_ref = db.collection(COLLECTIONS['users'])
            
            # Check if default admin exists
            admin_query = users_ref.where('email', '==', 'agsadmin@ags.ai').limit(1)
            existing_admin = admin_query.get()
            
            if not existing_admin:
                # Create default admin user
                admin_data = {
                    'email': 'agsadmin@ags.ai',
                    'name': 'AGS Admin',
                    'company': 'AGS AI',
                    'password_hash': self._hash_password('agsai123'),
                    'role': 'admin',
                    'is_active': True,
                    'created_at': datetime.now(),
                    'last_login': None,
                    'login_count': 0,
                    'analyses_count': 0
                }
                
                users_ref.add(admin_data)
                print("Default admin user created successfully")
                
        except Exception as e:
            print(f"Error creating default admin: {str(e)}")
    
    def logout_user(self) -> None:
        """Logout current user by clearing session state"""
        # Clear all authentication-related session state
        if hasattr(st, 'session_state'):
            keys_to_clear = [
                'authenticated', 'user_id', 'user_email', 'user_name', 
                'user_role', 'user_info', 'current_analysis', 'auth_token'
            ]
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
    
    def is_logged_in(self) -> bool:
        """Check if user is logged in"""
        return getattr(st.session_state, 'authenticated', False)
    
    def get_all_users(self) -> list:
        """Get all users (admin only)
        
        Returns:
            list: List of all users
        """
        try:
            db = self._get_db()
            users_ref = db.collection(COLLECTIONS['users'])
            users = users_ref.get()
            
            user_list = []
            for user_doc in users:
                user_data = user_doc.to_dict()
                user_data['uid'] = user_doc.id
                user_list.append(user_data)
            
            return user_list
            
        except Exception as e:
            st.error(f"Error getting users: {str(e)}")
            return []
    
    def register_user(self, email: str, password: str, full_name: str, farm_name: str = "", location: str = "") -> bool:
        """Register new user with farm details
        
        Args:
            email: User email
            password: User password
            full_name: User full name
            farm_name: Farm name (optional)
            location: Farm location (optional)
            
        Returns:
            bool: True if registration successful, False otherwise
        """
        try:
            # Validate input
            if len(password) < 6:
                st.error('Password must be at least 6 characters')
                return False
            
            # Check if user already exists
            db = self._get_db()
            users_ref = db.collection(COLLECTIONS['users'])
            existing_user = users_ref.where('email', '==', email.lower()).limit(1).get()
            
            if existing_user:
                st.error('User already exists with this email')
                return False
            
            # Create user document
            user_data = {
                'email': email.lower(),
                'name': full_name,
                'company': farm_name,
                'location': location,
                'password_hash': self._hash_password(password),
                'role': 'user',
                'is_active': True,
                'created_at': datetime.now(),
                'last_login': None,
                'login_count': 0,
                'analyses_count': 0
            }
            
            # Add user to Firestore
            doc_ref = users_ref.add(user_data)
            
            return True
            
        except Exception as e:
            st.error(f'Registration error: {str(e)}')
            return False


# Global auth manager instance
auth_manager = AuthManager()

# Standalone functions for backward compatibility
def login_user(email: str, password: str) -> Dict[str, Any]:
    """Login user"""
    return auth_manager.login(email, password)

def register_user(email: str, password: str, full_name: str, farm_name: str = "", location: str = "") -> bool:
    """Register new user"""
    return auth_manager.register_user(email, password, full_name, farm_name, location)

def reset_password(email: str) -> bool:
    """Reset user password"""
    return auth_manager.reset_password(email)

def logout_user() -> None:
    """Logout current user"""
    auth_manager.logout_user()

def is_logged_in() -> bool:
    """Check if user is logged in"""
    return auth_manager.is_logged_in()

def is_admin(user_id: str) -> bool:
    """Check if user is admin"""
    user_info = auth_manager.get_user_by_id(user_id)
    if not user_info:
        return False
    return auth_manager.is_admin(user_info)

def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user by ID"""
    return auth_manager.get_user_by_id(user_id)

def update_user_profile(user_id: str, profile_data: Dict[str, Any]) -> bool:
    """Update user profile"""
    return auth_manager.update_user_profile(user_id, profile_data)

def get_all_users() -> list:
    """Get all users (admin only)"""
    return auth_manager.get_all_users()

def admin_signup(email: str, password: str, name: str, organization: str = '') -> Dict[str, Any]:
    """Register new admin user"""
    return auth_manager.admin_signup(email, password, name, organization)

def admin_signup_with_code(email: str, password: str, name: str, organization: str, admin_code: str) -> Dict[str, Any]:
    """Register new admin user with admin code verification"""
    return auth_manager.admin_signup_with_code(email, password, name, organization, admin_code)