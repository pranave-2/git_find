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
            sys.exit(1)
    else:
        print(f"Error calling Gemini API: HTTP {response.status_code}")
        print(response.text)
        sys.exit(1)

def get_default_branch(username, repo, headers):
    global github_api_calls
    url = f"https://api.github.com/repos/{username}/{repo}"
    response = requests.get(url, headers=headers)
    github_api_calls += 1
    if response.status_code == 200:
        return response.json().get('default_branch', 'main')
    else:
        print(f"Error fetching repo info: HTTP {response.status_code}")
        print(response.text)
        sys.exit(1)

def get_git_tree(username, repo, branch, headers):
    global github_api_calls
    url = f"https://api.github.com/repos/{username}/{repo}/git/trees/{branch}?recursive=1"
    response = requests.get(url, headers=headers)
    github_api_calls += 1
    if response.status_code == 200:
        return response.json().get('tree', [])
    else:
        print(f"Error fetching git tree: HTTP {response.status_code}")
        sys.exit(1)

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
    """Fetch contents of common fundamental files."""
    core_files_to_check = ['README.md', 'README.txt', 'package.json', 'requirements.txt', 'pom.xml', 'docker-compose.yml', 'Dockerfile', 'main.py', 'index.js', 'app.py']
    
    # Create a fast lookup
    tree_paths = [item['path'] for item in tree if item['type'] == 'blob']
    
    fetched_contents = {}
    for core_file in core_files_to_check:
        if core_file in tree_paths:
            content = get_file_content(username, repo, core_file, branch, headers)
            if content:
                fetched_contents[core_file] = content
                
    return fetched_contents

def clean_json_response(text):
    """Clean the markdown formatting from the JSON response."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    
    if text.endswith("```"):
        text = text[:-3]
        
    return text.strip()

def main():
    global gemini_api_calls
    
    parser = argparse.ArgumentParser(description="Summarize a GitHub repository interactively using Gemini.")
    parser.add_argument("username", help="GitHub username")
    parser.add_argument("repo", help="Repository name")
    parser.add_argument("--github-token", "-gt", help="GitHub Personal Access Token")
    parser.add_argument("--gemini-token", "-ai", help="Gemini API Key")
    
    args = parser.parse_args()
    username = args.username
    repo = args.repo
    github_token = args.github_token or os.environ.get("GITHUB_TOKEN")
    gemini_token = args.gemini_token or os.environ.get("GEMINI_API_KEY")
    
    if not gemini_token:
        print("Error: Gemini API token is required. Use --gemini-token or set GEMINI_API_KEY environment variable.")
        sys.exit(1)
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    print(f"--- Fetching basic information for {username}/{repo} ---")
    branch = get_default_branch(username, repo, headers)
    print(f"Default branch: {branch}")
    
    tree = get_git_tree(username, repo, branch, headers)
    tree_paths = [item['path'] for item in tree if item['type'] == 'blob']
    
    print(f"Found {len(tree_paths)} files in the repository.")
    
    print("Fetching core fundamental files...")
    core_files = fetch_core_files(username, repo, branch, tree, headers)
    print(f"Found core files: {list(core_files.keys())}")
    
    # ---------------- PHASE 1: LLM Planning ----------------
    print("\n--- Phase 1: Planning with Gemini ---")
    tree_str = "\n".join(tree_paths)
    
    core_files_str = ""
    for path, content in core_files.items():
        core_files_str += f"\n--- {path} ---\n{content}\n"
    
    planning_prompt = f"""You are an expert software engineer analyzing a repository.
Your task is to review the following repository structure and core files, and identify up to 7 OTHER specific files you need to read to fully understand and summarize the project's architecture, business logic, and features.

Repository File Structure:
{tree_str}

Core Files Content:
{core_files_str}

Please reply ONLY with a valid JSON list containing the exact file paths of up to 7 files you wish to inspect. 
Do not include files already provided in the Core Files Content above. Do not include markdown formatting, just the raw JSON array.
Example response:
["src/main.py", "api/routes.py", "database/models.py"]
"""
    print("Sending repository structure to Gemini to determine what files it needs...")
    try:
        response_text = call_gemini(planning_prompt, gemini_token)
        json_str = clean_json_response(response_text)
        requested_files = json.loads(json_str)
        print(f"Gemini requested {len(requested_files)} files: {requested_files}")
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        print(f"Raw response: {response_text if 'response_text' in locals() else 'None'}")
        sys.exit(1)
        
    # Enforce limit of 10 files max just in case
    if len(requested_files) > 10:
        print("Warning: Gemini requested more than 10 files. Limiting to first 10 to save API calls.")
        requested_files = requested_files[:10]
        
    # ---------------- SECONDARY FETCH ----------------
    print("\n--- Phase 2: Fetching Requested Files ---")
    requested_contents = {}
    for path in requested_files:
        if path in tree_paths:
            print(f"Fetching {path}...")
            content = get_file_content(username, repo, path, branch, headers)
            if content:
                requested_contents[path] = content
        else:
            print(f"File {path} not found in tree, skipping.")
            
    # ---------------- PHASE 3: Final Summarization ----------------
    print("\n--- Phase 3: Final Summarization ---")
    requested_files_str = ""
    for path, content in requested_contents.items():
        requested_files_str += f"\n--- {path} ---\n{content}\n"
        
    summary_prompt = f"""You are an expert software engineer.
You previously reviewed the file structure and core files of this repository. 
You then requested specific files to understand the project better.

Here is the content of the files you requested:
{requested_files_str}

Based on the file structure, the core files (like README and dependencies), and these additional files, write a comprehensive, high-quality Markdown summary of the entire repository.
Include:
1. What the project is and its primary purpose.
2. The Tech Stack and Architecture.
3. Key Features and how they work.
4. Any notable design decisions or complexities.
"""
    print("Generating final summary with Gemini...")
    summary = call_gemini(summary_prompt, gemini_token)
        
    output_filename = f"{repo}_summary.md"
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(summary)
        
    print(f"\n✅ Summary successfully generated and saved to {output_filename}")
    
    print(f"\n📊 API Usage Statistics:")
    print(f"  - GitHub API Calls: {github_api_calls}")
    print(f"  - Gemini API Calls: {gemini_api_calls}")
    print(f"  - Total API Calls: {github_api_calls + gemini_api_calls}")

if __name__ == "__main__":
    main()
