# 🚀 CI/CD Setup and Deployment Guide

This document explains the CI/CD pipeline setup for the Interview Agent application.

## Overview

The project uses GitHub Actions for continuous integration and deployment with the following features:

- **Automated Testing**: Unit tests, code coverage, and quality checks
- **Code Quality**: Linting, formatting, and security scanning
- **Multi-Python Support**: Tests across Python 3.8, 3.9, 3.10, and 3.11
- **Docker Support**: Containerized deployment
- **Streamlit Cloud**: Easy web deployment

## Pipeline Structure

### 1. Continuous Integration (CI)

The CI pipeline runs on every push to `main`/`develop` branches and all pull requests:

- **Code Quality Checks**:
  - `flake8` for linting
  - `black` for code formatting
  - `isort` for import sorting
  - `bandit` for security scanning
  - `safety` for dependency vulnerability checks

- **Testing**:
  - Unit tests with `pytest`
  - Code coverage reporting
  - Coverage upload to Codecov

- **Multi-Python Testing**:
  - Matrix testing across Python 3.8-3.11
  - Ensures compatibility across versions

### 2. Docker Build

On successful CI for the `main` branch:
- Builds Docker image
- Pushes to Docker Hub
- Uses build caching for efficiency

### 3. Streamlit Cloud Deployment

Automatically triggers deployment to Streamlit Cloud when:
- CI passes
- Code is pushed to `main` branch

## Setup Instructions

### Required GitHub Secrets

Add these secrets to your GitHub repository:

```
OPENAI_API_KEY          # Your OpenAI API key
DOCKER_USERNAME         # Docker Hub username
DOCKER_PASSWORD         # Docker Hub password or access token
```

### Local Development Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

2. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

3. **Run tests**:
   ```bash
   pytest
   ```

4. **Run code quality checks**:
   ```bash
   black .
   isort .
   flake8 .
   bandit -r .
   safety check
   ```

### Docker Usage

1. **Build image**:
   ```bash
   docker build -t interview-agent .
   ```

2. **Run container**:
   ```bash
   docker run -p 8501:8501 -e OPENAI_API_KEY=your_key interview-agent
   ```

### Streamlit Cloud Setup

1. Connect your GitHub repository to Streamlit Cloud
2. Set the main file to `app.py`
3. Add your `OPENAI_API_KEY` in the Streamlit Cloud secrets
4. Deploy!

## Code Quality Standards

### Formatting
- **Black**: Line length 88 characters
- **isort**: Black-compatible import sorting

### Linting
- **flake8**: Maximum line length 88, compatible with Black
- **bandit**: Security linting for Python code
- **safety**: Checks for known security vulnerabilities

### Testing
- **pytest**: Unit test framework
- **Coverage**: Minimum 80% code coverage required
- **Mocking**: Extensive use of mocks for external dependencies

## Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality:

- Trailing whitespace removal
- End-of-file fixing
- YAML/JSON validation
- Code formatting (Black)
- Import sorting (isort)
- Linting (flake8)
- Security scanning (bandit)
- Dependency checking (safety)
- Test execution (pytest)

## Deployment Environments

### Development
- **Branch**: `develop`
- **Triggers**: Push, PR
- **Actions**: CI only (no deployment)

### Production
- **Branch**: `main`
- **Triggers**: Push to main
- **Actions**: CI + Docker build + Streamlit deployment

## Monitoring and Alerts

- **GitHub Actions**: Build status in repository
- **Codecov**: Code coverage reports
- **Docker Hub**: Container image repository
- **Streamlit Cloud**: Application health monitoring

## Troubleshooting

### Common Issues

1. **Tests failing**: Check if `OPENAI_API_KEY` is set in secrets
2. **Docker build failing**: Ensure Dockerfile syntax is correct
3. **Streamlit deployment failing**: Check app.py syntax and dependencies
4. **Coverage too low**: Add more tests or adjust coverage threshold

### Debugging Tips

- Check GitHub Actions logs for detailed error messages
- Run tests locally with `pytest -v` for verbose output
- Use `docker build --no-cache` to rebuild without cache
- Verify secrets are correctly set in GitHub repository settings

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and quality checks locally
5. Submit a pull request

The CI pipeline will automatically run on your PR to ensure code quality and test coverage. 