import requests
import json
import csv
import argparse
import sys
from datetime import datetime

def get_user_profile(username, headers):
    """Fetch the user's profile information."""
    url = f"https://api.github.com/users/{username}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        print(f"Error: User '{username}' not found.")
        sys.exit(1)
    else:
        print(f"Error fetching profile: HTTP {response.status_code}")
        print(response.text)
        sys.exit(1)

def get_user_repositories(username, headers):
    """Fetch all repositories for the given user, handling pagination."""
    repos = []
    page = 1
    per_page = 100 # Maximum allowed by GitHub API
    
    print(f"Fetching repositories for user: {username}...")
    
    while True:
        url = f"https://api.github.com/users/{username}/repos?page={page}&per_page={per_page}"
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"Error fetching repositories: HTTP {response.status_code}")
            print(response.text)
            break
            
        page_repos = response.json()
        if not page_repos:
            break # No more repositories found
            
        repos.extend(page_repos)
        print(f"Fetched page {page} ({len(page_repos)} repos)...")
        page += 1
        
    return repos

def get_repo_commits(username, repo_name, headers):
    """Fetch the latest commits for a specific repository."""
    url = f"https://api.github.com/repos/{username}/{repo_name}/commits?per_page=30"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 409: # Empty repository (Git Repository is empty)
        return []
    else:
        print(f"Error fetching commits for {repo_name}: HTTP {response.status_code}")
        return []

def save_to_json(data, filename):
    """Save data to a JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    print(f"Data saved to {filename}")

def save_to_csv(repos, filename):
    """Save repository data to a CSV file extracting key fields."""
    if not repos:
        print("No repositories to save.")
        return
        
    # Define the fields we want to extract
    fields = [
        'name', 'full_name', 'description', 'html_url', 
        'stargazers_count', 'watchers_count', 'forks_count', 
        'language', 'created_at', 'updated_at', 'size', 'default_branch'
    ]
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        
        for repo in repos:
            # Extract only the specified fields, replacing None with empty strings
            row = {field: repo.get(field) or "" for field in fields}
            writer.writerow(row)
            
    print(f"Data saved to {filename}")

def main():
    parser = argparse.ArgumentParser(description="Fetch GitHub profile and repository data.")
    parser.add_argument("username", help="GitHub username to fetch data for")
    parser.add_argument("--token", "-t", help="GitHub Personal Access Token (for higher rate limits and private repos)", default=None)
    parser.add_argument("--commits", "-c", action="store_true", help="Fetch recent commits for each repository")
    
    args = parser.parse_args()
    username = args.username
    token = args.token
    
    # Set up headers for the API request
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
        print("Using provided authentication token.")
    else:
        print("Warning: Running without token. You may hit rate limits (60 req/hr).")
    
    # 1. Fetch Profile Data
    profile = get_user_profile(username, headers)
    print("\n--- Profile Information ---")
    print(f"Name: {profile.get('name')}")
    print(f"Bio: {profile.get('bio')}")
    print(f"Public Repos: {profile.get('public_repos')}")
    print(f"Followers: {profile.get('followers')}")
    print("---------------------------\n")
    
    # 2. Fetch Repositories Data
    repos = get_user_repositories(username, headers)
    print(f"\nTotal repositories fetched: {len(repos)}")
    
    commits_data = {}
    if args.commits:
        print("\n--- Fetching Commits ---")
        for repo in repos:
            repo_name = repo['name']
            print(f"Fetching commits for {repo_name}...")
            commits = get_repo_commits(username, repo_name, headers)
            commits_data[repo_name] = commits
        print("------------------------")
    
    # 3. Save Data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    profile_filename = f"{username}_profile_{timestamp}.json"
    save_to_json(profile, profile_filename)
    
    repos_json_filename = f"{username}_repos_{timestamp}.json"
    save_to_json(repos, repos_json_filename)
    
    repos_csv_filename = f"{username}_repos_{timestamp}.csv"
    save_to_csv(repos, repos_csv_filename)
    
    if args.commits:
        commits_json_filename = f"{username}_commits_{timestamp}.json"
        save_to_json(commits_data, commits_json_filename)
    
    print("\nDone! Check the generated JSON and CSV files to see the extent of data available.")

if __name__ == "__main__":
    main()
