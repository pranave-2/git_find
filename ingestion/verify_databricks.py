import os
from dotenv import load_dotenv
from databricks.sdk import WorkspaceClient

# Load environment variables from .env file
load_dotenv()

def verify_connection():
    try:
        # The WorkspaceClient automatically looks for DATABRICKS_HOST and DATABRICKS_TOKEN
        # in the environment variables
        print("Attempting to connect to Databricks workspace...")
        print(f"Host: {os.environ.get('DATABRICKS_HOST')}")
        
        w = WorkspaceClient()
        
        # Verify by fetching the current user's information
        me = w.current_user.me()
        
        print("\n✅ Authentication Successful!")
        print(f"Logged in as: {me.user_name}")
        if hasattr(me, 'id'):
            print(f"User ID: {me.id}")
            
    except Exception as e:
        print("\n❌ Authentication Failed!")
        print(f"Error details: {str(e)}")
        print("\nPlease check that:")
        print("1. You have created a .env file in the root directory")
        print("2. It contains DATABRICKS_HOST=\"https://...\"")
        print("3. It contains DATABRICKS_TOKEN=\"dapi...\"")
        print("4. Your token has not expired")

if __name__ == "__main__":
    verify_connection()
