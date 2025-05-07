from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UserProfile
import requests
import json
from django.http import JsonResponse
from collections import defaultdict

def register_view(request):
    """
    Handle user registration
    """
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful")
            return redirect("dashboard")
        messages.error(request, "Registration failed")
    else:
        form = UserCreationForm()
    return render(request, "dashboard/register.html", {"form": form})

def login_view(request):
    """
    Handle user login
    """
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome, {username}!")
                return redirect("dashboard")
            else:
                messages.error(request, "Invalid username or password")
        else:
            messages.error(request, "Invalid username or password")
    else:
        form = AuthenticationForm()
    return render(request, "dashboard/login.html", {"form": form})

def logout_view(request):
    """
    Handle user logout
    """
    logout(request)
    messages.success(request, "Logged out successfully")
    return redirect("login")

@login_required
def add_api_key_view(request):
    """
    Allow users to add their GitHub Personal Access Tokens
    """
    if request.method == "POST":
        token = request.POST.get("github_token")
        if token:
            # Validate token by making a test API call
            headers = {"Authorization": f"token {token}"}
            response = requests.get("https://api.github.com/user", headers=headers)
            if response.status_code == 200:
                profile = UserProfile.objects.get(user=request.user)
                profile.github_token = token
                profile.save()
                messages.success(request, "GitHub token added successfully")
                return redirect("dashboard")
            else:
                messages.error(request, "Invalid GitHub token")
    return render(request, "dashboard/add_api_key.html")

@login_required
def dashboard_view(request):
    """
    Display the main dashboard with repository listing
    """
    profile = UserProfile.objects.get(user=request.user)
    if not profile.github_token:
        messages.warning(request, "Please add your GitHub token to view repositories")
        return redirect("add_api_key")
    
    headers = {"Authorization": f"token {profile.github_token}"}
    
    # Get user repositories
    repos_response = requests.get("https://api.github.com/user/repos", headers=headers)
    repos = []
    
    if repos_response.status_code == 200:
        repos = repos_response.json()
    
    # Get user orgs
    orgs_response = requests.get("https://api.github.com/user/orgs", headers=headers)
    orgs = []
    org_repos = []
    
    if orgs_response.status_code == 200:
        orgs = orgs_response.json()
        for org in orgs:
            org_repos_response = requests.get(f"https://api.github.com/orgs/{org['login']}/repos", headers=headers)
            if org_repos_response.status_code == 200:
                org_repos.extend(org_repos_response.json())
    
    return render(request, "dashboard/dashboard.html", {
        "repos": repos,
        "org_repos": org_repos,
        "orgs": orgs,
    })

@login_required
def repository_insights_view(request, owner, repo):
    """
    Display insights for a specific repository
    """
    profile = UserProfile.objects.get(user=request.user)
    headers = {"Authorization": f"token {profile.github_token}"}
    
    # Get repository details
    repo_response = requests.get(f"https://api.github.com/repos/{owner}/{repo}", headers=headers)
    if repo_response.status_code != 200:
        messages.error(request, "Repository not found")
        return redirect("dashboard")
    
    repo_data = repo_response.json()
    
    # Get commit activity
    commit_activity_response = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/stats/commit_activity", 
        headers=headers
    )
    commit_activity = []
    if commit_activity_response.status_code == 200:
        commit_activity = commit_activity_response.json()
    
    # Get code frequency
    code_frequency_response = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/stats/code_frequency", 
        headers=headers
    )
    code_frequency = []
    if code_frequency_response.status_code == 200:
        code_frequency = code_frequency_response.json()
    
    # Get contributors
    contributors_response = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/stats/contributors", 
        headers=headers
    )
    contributors = []
    if contributors_response.status_code == 200:
        contributors = contributors_response.json()
    
    # Get traffic views
    traffic_views_response = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/traffic/views", 
        headers=headers
    )
    traffic_views = {}
    if traffic_views_response.status_code == 200:
        traffic_views = traffic_views_response.json()
    
    # Get traffic clones
    traffic_clones_response = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/traffic/clones", 
        headers=headers
    )
    traffic_clones = {}
    if traffic_clones_response.status_code == 200:
        traffic_clones = traffic_clones_response.json()
        
    # Get popular referrers
    referrers_response = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/traffic/popular/referrers", 
        headers=headers
    )
    referrers = []
    if referrers_response.status_code == 200:
        referrers = referrers_response.json()
    
    # Get popular paths
    paths_response = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/traffic/popular/paths", 
        headers=headers
    )
    paths = []
    if paths_response.status_code == 200:
        paths = paths_response.json()
    
    return render(request, "dashboard/repository_insights.html", {
        "repo": repo_data,
        "commit_activity": json.dumps(commit_activity),
        "code_frequency": json.dumps(code_frequency),
        "contributors": json.dumps(contributors),
        "traffic_views": json.dumps(traffic_views),
        "traffic_clones": json.dumps(traffic_clones),
        "referrers": referrers,
        "paths": paths,
    })

@login_required
def organization_insights_view(request, org_name):
    """
    Display organization-level insights
    """
    profile = UserProfile.objects.get(user=request.user)
    headers = {"Authorization": f"token {profile.github_token}"}
    
    # 1. Get organization details
    org_response = requests.get(f"https://api.github.com/orgs/{org_name}", headers=headers)
    if org_response.status_code != 200:
        messages.error(request, "Organization not found")
        return redirect("dashboard")
    
    org_data = org_response.json()
    
    # 2. Get all repositories for the organization
    repos_response = requests.get(f"https://api.github.com/orgs/{org_name}/repos?per_page=100", headers=headers)
    repos = []
    if repos_response.status_code == 200:
        repos = repos_response.json()

    # Calculate repository statistics
    total_repos = len(repos)
    public_repos = sum(1 for repo in repos if not repo.get("private", False))
    private_repos = total_repos - public_repos
    forked_repos = sum(1 for repo in repos if repo.get("fork", False))
    template_repos = sum(1 for repo in repos if repo.get("is_template", False))
    archived_repos = sum(1 for repo in repos if repo.get("archived", False))
    
    # Track creation dates for timeline
    creation_dates = [repo.get("created_at", "").split("T")[0] for repo in repos]
    creation_dates_count = defaultdict(int)
    for date in creation_dates:
        if date:
            creation_dates_count[date] += 1
    
    # 3. Get language data across repositories
    language_data = {}
    for repo in repos[:25]:  # Limit to 25 repos to avoid API rate limits
        lang_response = requests.get(f"https://api.github.com/repos/{org_name}/{repo['name']}/languages", headers=headers)
        if lang_response.status_code == 200:
            repo_langs = lang_response.json()
            for lang, bytes_count in repo_langs.items():
                language_data[lang] = language_data.get(lang, 0) + bytes_count
    
    # 4. Get commit activity for active repositories
    active_repos = []
    commits_per_repo = {}
    top_contributors = defaultdict(int)
    
    for repo in repos[:10]:  # Limit to 10 most recently updated repos
        # Get commit activity
        commit_activity_response = requests.get(
            f"https://api.github.com/repos/{org_name}/{repo['name']}/stats/commit_activity", 
            headers=headers
        )
        
        if commit_activity_response.status_code == 200:
            commit_data = commit_activity_response.json()
            total_commits = sum(week.get("total", 0) for week in commit_data)
            if total_commits > 0:
                active_repos.append(repo)
                commits_per_repo[repo['name']] = total_commits

                # Get contributors for this repo
                contributors_response = requests.get(
                    f"https://api.github.com/repos/{org_name}/{repo['name']}/contributors", 
                    headers=headers
                )
                if contributors_response.status_code == 200:
                    contributors = contributors_response.json()
                    for contributor in contributors:
                        top_contributors[contributor.get('login', 'unknown')] += contributor.get('contributions', 0)

    # Sort active repos by commit count
    active_repos_data = [{"name": name, "commits": count} 
                       for name, count in sorted(commits_per_repo.items(), 
                                              key=lambda x: x[1], reverse=True)]
                                              
    # Get top 10 contributors
    top_contributors_data = [{"login": login, "contributions": contributions} 
                          for login, contributions in sorted(top_contributors.items(), 
                                                         key=lambda x: x[1], reverse=True)[:10]]

    # 5. Get traffic data (aggregate for top repos)
    traffic_views_data = {}
    traffic_clones_data = {}
    all_referrers = {}
    
    for repo in repos[:5]:  # Limit to top 5 repos
        # Get traffic views
        traffic_views_response = requests.get(
            f"https://api.github.com/repos/{org_name}/{repo['name']}/traffic/views", 
            headers=headers
        )
        if traffic_views_response.status_code == 200:
            traffic_data = traffic_views_response.json()
            if 'views' in traffic_data:
                for view in traffic_data['views']:
                    date = view.get('timestamp', '').split('T')[0]
                    count = view.get('count', 0)
                    if date:
                        if date not in traffic_views_data:
                            traffic_views_data[date] = count
                        else:
                            traffic_views_data[date] += count
        
        # Get traffic clones
        traffic_clones_response = requests.get(
            f"https://api.github.com/repos/{org_name}/{repo['name']}/traffic/clones", 
            headers=headers
        )
        if traffic_clones_response.status_code == 200:
            clones_data = traffic_clones_response.json()
            if 'clones' in clones_data:
                for clone in clones_data['clones']:
                    date = clone.get('timestamp', '').split('T')[0]
                    count = clone.get('count', 0)
                    if date:
                        if date not in traffic_clones_data:
                            traffic_clones_data[date] = count
                        else:
                            traffic_clones_data[date] += count
        
        # Get referrers
        referrers_response = requests.get(
            f"https://api.github.com/repos/{org_name}/{repo['name']}/traffic/popular/referrers", 
            headers=headers
        )
        if referrers_response.status_code == 200:
            referrers = referrers_response.json()
            for referrer in referrers:
                name = referrer.get('referrer', '')
                count = referrer.get('count', 0)
                if name:
                    if name not in all_referrers:
                        all_referrers[name] = count
                    else:
                        all_referrers[name] += count
    
    # Prepare traffic views and clones for charts
    traffic_dates = sorted(set(list(traffic_views_data.keys()) + list(traffic_clones_data.keys())))
    
    views_data = [{"date": date, "count": traffic_views_data.get(date, 0)} for date in traffic_dates]
    clones_data = [{"date": date, "count": traffic_clones_data.get(date, 0)} for date in traffic_dates]
    
    # Prepare referrers for display
    top_referrers = [{"referrer": referrer, "count": count} 
                   for referrer, count in sorted(all_referrers.items(), 
                                              key=lambda x: x[1], reverse=True)[:10]]

    # 6. Prepare security metrics
    security_metrics = {
        "open_issues": sum(repo.get("open_issues_count", 0) for repo in repos),
        "stale_repos": sum(1 for repo in repos if not repo.get("pushed_at", "").startswith(repo.get("updated_at", "")[:7]))
    }

    return render(request, "dashboard/organization_insights.html", {
        "org": org_data,
        "repo_stats": {
            "total": total_repos,
            "public": public_repos,
            "private": private_repos,
            "forked": forked_repos,
            "template": template_repos,
            "archived": archived_repos
        },
        "timeline_data": json.dumps([{"date": date, "count": count} 
                                  for date, count in sorted(creation_dates_count.items())]),
        "language_data": json.dumps(language_data),
        "active_repos": json.dumps(active_repos_data),
        "top_contributors": json.dumps(top_contributors_data),
        "traffic_views": json.dumps(views_data),
        "traffic_clones": json.dumps(clones_data),
        "top_referrers": top_referrers,
        "security_metrics": security_metrics,
    })

def index_view(request):
    """
    Landing page view
    """
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "dashboard/index.html")
