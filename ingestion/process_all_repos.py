import os
import sys
import requests
import json
import argparse
import time

github_api_calls = 0
gemini_api_calls = 0

def call_gemini(prompt, api_key, model_name="gemini-2.5-flash"):
    global gemini_api_calls
    gemini_api_calls += 1
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        try:
            return result['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError):
            print(f"Error parsing Gemini response: {result}")
            return None
    else:
        print(f"Error calling Gemini API: HTTP {response.status_code}")
        print(response.text)
        return None

def clean_json_response(text):
    """Clean the markdown formatting from the JSON response."""
    if not text:
        return ""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    
    if text.endswith("```"):
        text = text[:-3]
        
    return text.strip()

def make_github_request(url, headers):
    global github_api_calls
    github_api_calls += 1
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error calling GitHub API ({url}): HTTP {response.status_code}")
        return None

def get_profile(username, headers):
    url = f"https://api.github.com/users/{username}"
    return make_github_request(url, headers)

def get_repos(username, headers):
    # Just getting the first page for simplicity, can handle pagination later if needed
    url = f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated"
    return make_github_request(url, headers)

def get_default_branch(username, repo, headers):
    url = f"https://api.github.com/repos/{username}/{repo}"
    data = make_github_request(url, headers)
    if data:
        return data.get('default_branch', 'main')
    return 'main'

def get_git_tree(username, repo, branch, headers):
    url = f"https://api.github.com/repos/{username}/{repo}/git/trees/{branch}?recursive=1"
    data = make_github_request(url, headers)
    if data:
        return data.get('tree', [])
    return []

def get_file_content(username, repo, path, branch, headers):
    global github_api_calls
    url = f"https://raw.githubusercontent.com/{username}/{repo}/{branch}/{path}"
    # Raw content doesn't need the typical v3 JSON accept header, but passing auth helps for private repos
    response = requests.get(url, headers={"Authorization": headers.get("Authorization")} if "Authorization" in headers else {})
    github_api_calls += 1
    if response.status_code == 200:
        return response.text
    return None

def fetch_core_files(username, repo, branch, tree, headers):
    core_files_to_check = ['README.md', 'README.txt', 'package.json', 'requirements.txt', 'pom.xml', 'docker-compose.yml', 'Dockerfile', 'main.py', 'index.js', 'app.py']
    tree_paths = [item['path'] for item in tree if item['type'] == 'blob']
    
    fetched_contents = {}
    for core_file in core_files_to_check:
        if core_file in tree_paths:
            content = get_file_content(username, repo, core_file, branch, headers)
            if content:
                fetched_contents[core_file] = content
                
    return fetched_contents, tree_paths

def process_repository(username, repo_name, gemini_token, headers):
    print(f"\n--- Processing Repository: {repo_name} ---")
    branch = get_default_branch(username, repo_name, headers)
    tree = get_git_tree(username, repo_name, branch, headers)
    
    if not tree:
        print(f"Skipping {repo_name} (empty or failed to fetch tree)")
        return None

    core_files, tree_paths = fetch_core_files(username, repo_name, branch, tree, headers)
    
    # ---------------- PHASE 1: LLM Planning ----------------
    tree_str = "\n".join(tree_paths[:200]) # Limit to 200 paths to avoid token explosion
    
    core_files_str = ""
    for path, content in core_files.items():
        core_files_str += f"\n--- {path} ---\n{content[:5000]}\n" # Limit content length
    
    planning_prompt = f"""You are an expert software engineer analyzing a repository.
Your task is to review the following repository structure and core files, and identify up to 5 OTHER specific files you need to read to extract the technologies, frameworks, and architecture used.

Repository File Structure:
{tree_str}

Core Files Content:
{core_files_str}

Please reply ONLY with a valid JSON list containing the exact file paths of up to 5 files you wish to inspect. 
Do not include files already provided in the Core Files Content above. Do not include markdown formatting, just the raw JSON array.
Example: ["src/main.py", "api/routes.py"]
"""
    response_text = call_gemini(planning_prompt, gemini_token)
    if not response_text:
        return None
        
    try:
        json_str = clean_json_response(response_text)
        requested_files = json.loads(json_str)
        if len(requested_files) > 5:
            requested_files = requested_files[:5]
    except Exception as e:
        print(f"Error parsing Gemini file request JSON for {repo_name}. Proceeding with core files only.")
        requested_files = []

    # ---------------- SECONDARY FETCH ----------------
    requested_contents = {}
    for path in requested_files:
        if path in tree_paths:
            content = get_file_content(username, repo_name, path, branch, headers)
            if content:
                requested_contents[path] = content[:5000] # Limit content length
                
    # ---------------- PHASE 3: Extraction and DB Schema Alignment ----------------
    requested_files_str = ""
    for path, content in requested_contents.items():
        requested_files_str += f"\n--- {path} ---\n{content}\n"
        
    extraction_prompt = f"""You are an expert technical evaluator. Analyze the following repository and extract skills and technologies.

Core Files Content:
{core_files_str}

Deep-Dive Files Content:
{requested_files_str}

You must extract the skills demonstrated in this repository and assign a confidence score between 0.0 and 1.0 (where 1.0 means highly evident in the code). 
Also provide a short "evidence" string explaining HOW it was used based on the code.

Reply EXACTLY with a JSON object matching this schema. DO NOT include markdown formatting (like ```json), just the raw JSON:

{{
  "repo_name": "{repo_name}",
  "summary": "A 1-2 sentence summary of what this repo does",
  "skills": [
    {{
      "skill_name": "Python",
      "category": "Programming",
      "confidence": 0.98,
      "evidence": "Backend services implemented in Python using SQLAlchemy."
    }}
  ]
}}
"""
    final_text = call_gemini(extraction_prompt, gemini_token)
    if not final_text:
        return None
        
    try:
        json_str = clean_json_response(final_text)
        repo_data = json.loads(json_str)
        return repo_data
    except Exception as e:
        print(f"Error parsing final JSON for {repo_name}: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Process all repositories for a user into a unified JSON knowledge base.")
    parser.add_argument("username", help="GitHub username")
    parser.add_argument("--github-token", "-gt", help="GitHub Personal Access Token")
    parser.add_argument("--gemini-token", "-ai", help="Gemini API Key")
    parser.add_argument("--limit", type=int, default=0, help="Limit the number of repositories to process (for testing)")
    
    args = parser.parse_args()
    username = args.username
    github_token = args.github_token or os.environ.get("GITHUB_TOKEN")
    gemini_token = args.gemini_token or os.environ.get("GEMINI_API_KEY")
    limit = args.limit
    
    if not gemini_token:
        print("Error: Gemini API token is required. Use --gemini-token or set GEMINI_API_KEY.")
        sys.exit(1)
        
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
        
    print(f"Fetching profile for {username}...")
    profile = get_profile(username, headers)
    if not profile:
        sys.exit(1)
        
    print(f"Fetching repositories...")
    repos = get_repos(username, headers)
    if not repos:
        sys.exit(1)
        
    if limit > 0:
        repos = repos[:limit]
        print(f"Limiting processing to {limit} repositories...")
        
    final_output = {
        "student": {
            "github_user_id": str(profile.get('id', '')),
            "github_username": profile.get('login', ''),
            "name": profile.get('name', ''),
            "bio": profile.get('bio', '')
        },
        "repositories": []
    }
    
    for r in repos:
        repo_name = r.get('name')
        if not repo_name:
            continue
            
        repo_data = process_repository(username, repo_name, gemini_token, headers)
        if repo_data:
            final_output["repositories"].append(repo_data)
            
        # Small delay to avoid API rate limits
        time.sleep(1)
        
    output_filename = f"{username}_knowledge_base.json"
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, indent=2)
        
    print(f"\n[SUCCESS] Processing complete! Saved to {output_filename}")
    
    print(f"\n[STATS] API Usage Statistics:")
    print(f"  - GitHub API Calls: {github_api_calls}")
    print(f"  - Gemini API Calls: {gemini_api_calls}")
    print(f"  - Total API Calls: {github_api_calls + gemini_api_calls}")

if __name__ == "__main__":
    main()
