#!/usr/bin/env python3
"""
Cross-platform Argo CD deployment script for IRIS
Works on Windows, macOS, and Linux
"""

import subprocess
import sys
import time
import platform
import base64
from pathlib import Path

# ANSI color codes (work on Windows 10+ and Unix)
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.CYAN}{'=' * 50}")
    print(f"  {text}")
    print(f"{'=' * 50}{Colors.END}\n")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}[OK] {text}{Colors.END}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}[ERROR] {text}{Colors.END}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}[WARN] {text}{Colors.END}")

def run_command(cmd, check=True, capture_output=False):
    """Run a shell command"""
    try:
        if isinstance(cmd, str):
            # Use shell=True for string commands
            result = subprocess.run(
                cmd,
                shell=True,
                check=check,
                capture_output=capture_output,
                text=True
            )
        else:
            # Use list for better cross-platform compatibility
            result = subprocess.run(
                cmd,
                check=check,
                capture_output=capture_output,
                text=True
            )
        return result
    except subprocess.CalledProcessError as e:
        if check:
            print_error(f"Command failed: {cmd}")
            print_error(f"Error: {e.stderr if capture_output else str(e)}")
            sys.exit(1)
        return None

def check_prerequisites():
    """Check if required tools are installed"""
    print_header("Checking Prerequisites")
    
    # Detect OS
    os_name = platform.system()
    print(f"Operating System: {Colors.BOLD}{os_name}{Colors.END}")
    
    # Check kubectl
    try:
        result = run_command(["kubectl", "version", "--client"], 
                           capture_output=True, check=False)
        if result and result.returncode == 0:
            print_success(f"kubectl found: {result.stdout.strip()}")
        else:
            print_error("kubectl not found. Please install kubectl first.")
            print("  Windows: winget install Kubernetes.kubectl")
            print("  macOS: brew install kubectl")
            sys.exit(1)
    except FileNotFoundError:
        print_error("kubectl not found. Please install kubectl first.")
        sys.exit(1)
    
    # Check cluster connectivity
    try:
        result = run_command(["kubectl", "cluster-info"], 
                           capture_output=True, check=False)
        if result and result.returncode == 0:
            print_success("Kubernetes cluster accessible")
        else:
            print_error("No Kubernetes cluster found. Please configure kubectl first.")
            sys.exit(1)
    except Exception as e:
        print_error(f"Cannot connect to Kubernetes cluster: {e}")
        sys.exit(1)
    
    # Check for Argo CD CLI (optional)
    try:
        result = run_command(["argocd", "version", "--client", "--short"], 
                           capture_output=True, check=False)
        if result and result.returncode == 0:
            print_success("Argo CD CLI found")
        else:
            print_warning("Argo CD CLI not found (optional)")
            print("  Install: https://argo-cd.readthedocs.io/en/stable/cli_installation/")
    except FileNotFoundError:
        print_warning("Argo CD CLI not found (optional)")

def install_argocd():
    """Install Argo CD on the cluster"""
    print_header("Installing Argo CD")
    
    # Create namespace
    print("Creating argocd namespace...")
    run_command([
        "kubectl", "create", "namespace", "argocd",
        "--dry-run=client", "-o", "yaml"
    ], capture_output=True)
    run_command("kubectl apply -f -", check=False)
    
    # Install Argo CD
    print("Installing Argo CD...")
    argocd_url = "https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml"
    run_command([
        "kubectl", "apply", "-n", "argocd", "-f", argocd_url
    ])
    
    # Wait for Argo CD to be ready
    print("Waiting for Argo CD to be ready (this may take a few minutes)...")
    
    deployments = [
        "argocd-server",
        "argocd-repo-server",
        "argocd-application-controller"
    ]
    
    for deployment in deployments:
        print(f"  Waiting for {deployment}...")
        result = run_command([
            "kubectl", "wait",
            "--for=condition=available",
            "--timeout=300s",
            f"deployment/{deployment}",
            "-n", "argocd"
        ], check=False)
        
        if result and result.returncode == 0:
            print_success(f"{deployment} ready")
        else:
            print_warning(f"{deployment} may not be ready yet")
    
    print_success("Argo CD installed successfully")

def get_argocd_password():
    """Get the Argo CD admin password"""
    print_header("Retrieving Argo CD Credentials")
    
    try:
        result = run_command([
            "kubectl", "-n", "argocd", "get", "secret",
            "argocd-initial-admin-secret",
            "-o", "jsonpath={.data.password}"
        ], capture_output=True)
        
        if result and result.stdout:
            password = base64.b64decode(result.stdout).decode('utf-8')
            return password
        else:
            print_error("Could not retrieve Argo CD password")
            return None
    except Exception as e:
        print_error(f"Error retrieving password: {e}")
        return None

def deploy_iris_project():
    """Create IRIS Argo CD project"""
    print_header("Creating IRIS Argo CD Project")
    
    project_file = Path("gitops/argocd/project.yaml")
    if not project_file.exists():
        print_error(f"Project file not found: {project_file}")
        print("Please run this script from the IRIS root directory.")
        sys.exit(1)
    
    run_command([
        "kubectl", "apply", "-f", str(project_file)
    ])
    
    print_success("IRIS project created")

def deploy_environment(env):
    """Deploy applications for a specific environment"""
    print(f"\nDeploying {env} environment applications...")
    
    services = [
        "iris-api-gateway",
        "iris-agent-router",
        "iris-web-ui",
        "postgresql",
        "ollama",
        "monitoring"
    ]
    
    for service in services:
        app_file = Path(f"gitops/applications/{service}-{env}.yaml")
        if app_file.exists():
            run_command([
                "kubectl", "apply", "-f", str(app_file)
            ])
            print_success(f"  {service}-{env} deployed")
        else:
            print_warning(f"  {app_file} not found, skipping")
    
    print_success(f"{env} environment applications deployed")

def select_environments():
    """Prompt user to select which environments to deploy"""
    print_header("Environment Selection")
    
    print("Which environments would you like to deploy?")
    print("1) Dev only")
    print("2) Dev + QA")
    print("3) All environments (dev, qa, stage, prod)")
    print("4) Custom selection")
    
    while True:
        try:
            choice = input("\nEnter choice (1-4): ").strip()
            
            if choice == "1":
                return ["dev"]
            elif choice == "2":
                return ["dev", "qa"]
            elif choice == "3":
                return ["dev", "qa", "stage", "prod"]
            elif choice == "4":
                environments = []
                for env in ["dev", "qa", "stage", "prod"]:
                    answer = input(f"Deploy {env}? (y/n): ").strip().lower()
                    if answer == "y":
                        environments.append(env)
                return environments
            else:
                print("Invalid choice. Please enter 1-4.")
        except KeyboardInterrupt:
            print("\n\nDeployment cancelled.")
            sys.exit(0)

def print_next_steps(password):
    """Print next steps for the user"""
    print_header("Deployment Complete!")
    
    print(f"{Colors.BOLD}Argo CD Access Information:{Colors.END}")
    print(f"  URL: https://localhost:8080")
    print(f"  Username: admin")
    print(f"  Password: {Colors.YELLOW}{password}{Colors.END}")
    print()
    
    print(f"{Colors.BOLD}Next Steps:{Colors.END}")
    print()
    print("1. Access Argo CD UI:")
    print("   kubectl port-forward svc/argocd-server -n argocd 8080:443")
    print("   Open https://localhost:8080 in your browser")
    print()
    print("2. Check application status:")
    print("   kubectl get applications -n argocd")
    print()
    print("3. Watch applications sync:")
    print("   kubectl get applications -n argocd -w")
    print()
    print("4. Access IRIS services (after sync completes):")
    print("   kubectl get pods -n iris-dev")
    print("   kubectl port-forward -n iris-dev svc/iris-api-gateway 8080:8080")
    print("   kubectl port-forward -n iris-dev svc/iris-web-ui 3000:3000")
    print()
    print(f"For more information, see {Colors.CYAN}gitops/README.md{Colors.END}")

def main():
    """Main deployment workflow"""
    print_header("Argo CD Deployment for IRIS")
    
    # Change to script directory's parent (IRIS root)
    script_dir = Path(__file__).parent
    iris_root = script_dir.parent
    import os
    os.chdir(iris_root)
    print(f"Working directory: {iris_root}")
    
    # Check prerequisites
    check_prerequisites()
    
    # Install Argo CD
    install_argocd()
    
    # Get admin password
    password = get_argocd_password()
    
    # Deploy IRIS project
    deploy_iris_project()
    
    # Select and deploy environments
    environments = select_environments()
    
    print_header("Deploying IRIS Applications")
    for env in environments:
        deploy_environment(env)
    
    # Print next steps
    print_next_steps(password)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDeployment cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
