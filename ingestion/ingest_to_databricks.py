import os
import sys
import uuid
import time
from dotenv import load_dotenv
from databricks import sql

# Import our existing pipeline logic
from process_all_repos import (
    get_profile, 
    get_repos, 
    process_repository
)

# Load environment variables
load_dotenv()

# The catalog and schema from the screenshots
CATALOG = "workspace"
SCHEMA = "recruitment_genie"

def get_db_connection():
    """Establish a connection to the Databricks SQL Warehouse."""
    host = os.environ.get("DATABRICKS_HOST")
    if host and host.startswith("https://"):
        host = host.replace("https://", "")
        
    http_path = os.environ.get("DATABRICKS_HTTP_PATH")
    token = os.environ.get("DATABRICKS_TOKEN")
    
    if not http_path or "protocolv1/o/" in http_path:
        print("Error: DATABRICKS_HTTP_PATH is not properly set in .env")
        print("Please find this in Databricks -> SQL Warehouses -> Connection Details")
        sys.exit(1)
        
    print(f"Connecting to Databricks Warehouse at {host}...")
    return sql.connect(
        server_hostname=host,
        http_path=http_path,
        access_token=token
    )

def safe_execute(cursor, query, params=None):
    """Execute a query and handle exceptions gracefully."""
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
    except Exception as e:
        print(f"SQL Error executing: {query}\nError: {e}")
        raise

def process_and_ingest_students(students, limit=2):
    """Loop through students, process their repos via Gemini, and insert to Databricks."""
    
    gemini_token = os.environ.get("GEMINI_API_KEY")
    github_token = os.environ.get("GITHUB_TOKEN")
    
    if not gemini_token:
        print("Error: GEMINI_API_KEY is required in environment.")
        sys.exit(1)
        
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
        
    connection = get_db_connection()
    cursor = connection.cursor()
    
    for student in students:
        s_id = student["student_id"]
        s_name = student["student_name"]
        username = student["git_username"]
        
        print(f"\n=============================================")
        print(f"Processing Student: {s_name} ({username})")
        print(f"=============================================")
        
        # 1. Insert Student
        # Using MERGE to avoid duplicate keys if we run this multiple times
        student_query = f"""
            MERGE INTO {CATALOG}.{SCHEMA}.student t
            USING (SELECT ? as student_id, ? as name, ? as github_username, ? as email) s
            ON t.student_id = s.student_id
            WHEN MATCHED THEN UPDATE SET name = s.name, github_username = s.github_username
            WHEN NOT MATCHED THEN INSERT (student_id, name, github_username, email) 
                                  VALUES (s.student_id, s.name, s.github_username, s.email)
        """
        # We don't have email, passing NULL or empty string
        safe_execute(cursor, student_query, (s_id, s_name, username, ""))
        print(f"[SUCCESS] Upserted student {s_name} to database.")
        
        # Fetch their GitHub repositories
        print(f"Fetching repositories for {username}...")
        repos = get_repos(username, headers)
        if not repos:
            print(f"No repositories found for {username}. Skipping.")
            continue
            
        # Limit the number of repos
        repos = repos[:limit]
        
        for r in repos:
            repo_name = r.get("name")
            repo_url = r.get("html_url")
            
            # 2. Process repo through Gemini
            repo_data = process_repository(username, repo_name, gemini_token, headers)
            if not repo_data:
                continue
                
            # Create a unique Repo ID
            repo_id = str(uuid.uuid4())
            summary = repo_data.get("summary", "")
            
            # 3. Insert Repository
            repo_query = f"""
                INSERT INTO {CATALOG}.{SCHEMA}.repository 
                (repo_id, student_id, repo_name, repo_url, summary, commit_sha, ingested_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP())
            """
            safe_execute(cursor, repo_query, (repo_id, s_id, repo_name, repo_url, summary, "unknown"))
            print(f"[SUCCESS] Inserted repository {repo_name} to database.")
            
            # 4. Insert Skills and Evidence
            skills = repo_data.get("skills", [])
            for skill in skills:
                skill_name = skill.get("skill_name")
                category = skill.get("category", "")
                confidence = float(skill.get("confidence", 0.0))
                evidence = skill.get("evidence", "")
                
                # Generate deterministic skill_id based on name so we don't have duplicates in the skill table
                # A simple hash or string clean up
                skill_id = "sk_" + str(hash(skill_name.lower().strip()) % (10 ** 8))
                
                # Insert Skill (MERGE to prevent duplicates globally)
                skill_query = f"""
                    MERGE INTO {CATALOG}.{SCHEMA}.skill t
                    USING (SELECT ? as skill_id, ? as skill_name, ? as category, ? as description) s
                    ON t.skill_id = s.skill_id
                    WHEN NOT MATCHED THEN INSERT (skill_id, skill_name, category, description)
                                          VALUES (s.skill_id, s.skill_name, s.category, s.description)
                """
                safe_execute(cursor, skill_query, (skill_id, skill_name, category, ""))
                
                # Insert Repository_Skill mapping
                repo_skill_query = f"""
                    INSERT INTO {CATALOG}.{SCHEMA}.repository_skill
                    (repo_id, skill_id, confidence, formula_version, computed_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP())
                """
                safe_execute(cursor, repo_skill_query, (repo_id, skill_id, confidence, "gemini-2.5-flash"))
                
                # Insert Evidence
                evidence_id = str(uuid.uuid4())
                evidence_query = f"""
                    INSERT INTO {CATALOG}.{SCHEMA}.skill_evidence
                    (evidence_id, repo_id, skill_id, evidence)
                    VALUES (?, ?, ?, ?)
                """
                safe_execute(cursor, evidence_query, (evidence_id, repo_id, skill_id, evidence))
            
            print(f"[SUCCESS] Inserted {len(skills)} skills and evidences for {repo_name}.")
            
            # Sleep to respect rate limits
            time.sleep(2)
            
    cursor.close()
    connection.close()
    print("\n[COMPLETE] All students processed and ingested successfully!")

if __name__ == "__main__":
    # Example Student Data provided by user
    students = [
        {
            "student_id": "s_001",
            "student_name": "Taran",
            "git_username": "Thims08"
        },
        {
            "student_id": "s_002",
            "student_name": "Alvin",
            "git_username": "a1l2v"
        }
    ]
    
    # Process with limit of 2 repos per student
    process_and_ingest_students(students, limit=2)
