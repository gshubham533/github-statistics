# GitHub Insights Dashboard

A web application that allows users to gain insights into their GitHub repositories—both individual and organizational—by integrating with GitHub's API.

## Features

- User authentication and API key management
- Dashboard displaying repository metrics
- Interactive charts and visualizations for repository insights
- Support for both personal and organizational repositories

## Technology Stack

- Backend: Django (Function-Based Views)
- Frontend: DaisyUI with Tailwind CSS
- Database: SQLite3
- Authentication: Django's built-in authentication system
- Charts: Chart.js integrated via Django templates

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd github-statistics
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install django requests
   ```

4. Make the run script executable:
   ```
   chmod +x run.sh
   ```

5. Run the application:
   ```
   ./run.sh
   ```

6. Access the application at:
   ```
   http://127.0.0.1:8000/
   ```

### Initial Login

- Username: admin
- Password: admin

## Usage

1. Register a new account or login with existing credentials
2. Add your GitHub Personal Access Token (PAT) with appropriate permissions
3. View your repositories and select one to see detailed insights
4. Explore various metrics and visualizations about your repository

## License

MIT