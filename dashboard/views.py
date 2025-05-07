from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UserProfile
import requests
import json
from django.http import JsonResponse

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

def index_view(request):
    """
    Landing page view
    """
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "dashboard/index.html")
