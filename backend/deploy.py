import boto3
import time
import sys
import subprocess
import os

def get_git_info():
    """Detects the git remote and branch of the current repository."""
    try:
        # Get remote URL
        remote = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], text=True).strip()
        # Clean remote URL if it's SSH format
        if remote.startswith("git@github.com:"):
            remote = remote.replace("git@github.com:", "https://github.com/").replace(".git", "")
        elif remote.endswith(".git"):
            remote = remote[:-4]
            
        # Get current branch
        branch = subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()
        return remote, branch
    except Exception as e:
        print(f"Warning: Could not automatically detect Git settings: {e}")
        return None, None

def deploy():
    region = "us-east-1"  # Standard region for App Runner and Amplify
    print(f"Starting AetherCOO Automated AWS Deployment in region: {region}...")
    
    session = boto3.Session(region_name=region)
    apprunner = session.client("apprunner")
    amplify = session.client("amplify")
    
    repo_url, branch = get_git_info()
    if not repo_url or not branch:
        print("Please ensure you are running this from a initialized Git repository with an origin remote.")
        sys.exit(1)
        
    print(f"Detected GitHub Repository: {repo_url}")
    print(f"Detected Active Branch: {branch}")
    
    # 1. Handle GitHub Connection
    connection_arn = None
    existing_connections = apprunner.list_connections()["ConnectionSummaryList"]
    for conn in existing_connections:
        if conn["ConnectionName"] == "aethercoo-github" and conn["Status"] == "AVAILABLE":
            connection_arn = conn["ConnectionArn"]
            print(f"Reusing existing GitHub connection: {connection_arn}")
            break
            
    if not connection_arn:
        print("\nStep 1: Creating a new AWS App Runner connection to GitHub...")
        conn_res = apprunner.create_connection(
            ConnectionName="aethercoo-github",
            ProviderType="GITHUB"
        )
        connection_arn = conn_res["Connection"]["ConnectionArn"]
        
        # Guide the user to complete handshake
        print("\n" + "="*80)
        print("ACTION REQUIRED:")
        print("Please visit the following URL in your browser to authorize AWS to access your GitHub:")
        print(f"https://console.aws.amazon.com/apprunner/home?region={region}#/connections")
        print("\nOnce there, click on 'aethercoo-github' (status will be PENDING_HANDSHAKE) and")
        print("complete the OAuth handshake.")
        print("="*80 + "\n")
        
        print("Waiting for handshake validation...")
        while True:
            conn_status = apprunner.list_connections()["ConnectionSummaryList"]
            active_conn = next((c for c in conn_status if c["ConnectionArn"] == connection_arn), None)
            if active_conn and active_conn["Status"] == "AVAILABLE":
                print("✓ GitHub Connection is now AVAILABLE!")
                break
            time.sleep(5)
            
    # 2. Deploy App Runner Service
    service_arn = None
    backend_url = None
    print("\nStep 2: Deploying FastAPI Backend to AWS App Runner...")
    
    try:
        # Check if already exists
        services = apprunner.list_services()["ServiceSummaryList"]
        existing_service = next((s for s in services if s["ServiceName"] == "aethercoo-backend"), None)
        
        if existing_service:
            service_arn = existing_service["ServiceArn"]
            backend_url = "https://" + existing_service["ServiceUrl"]
            print(f"Backend service already exists: {backend_url}")
        else:
            create_res = apprunner.create_service(
                ServiceName="aethercoo-backend",
                SourceConfiguration={
                    "CodeRepository": {
                        "RepositoryUrl": repo_url,
                        "SourceCodeVersion": {
                            "Type": "BRANCH",
                            "Value": branch
                        },
                        "ConfigurationSource": "REPOSITORY"
                    },
                    "AutoDeploymentsEnabled": True
                },
                InstanceConfiguration={
                    "Cpu": "1 vCPU",
                    "Memory": "2 GB"
                }
            )
            service_arn = create_res["Service"]["ServiceArn"]
            print(f"Service creation initiated. Service ARN: {service_arn}")
            
            print("Waiting for backend service to finish provisioning (this can take 3-5 minutes)...")
            while True:
                desc = apprunner.describe_service(ServiceArn=service_arn)["Service"]
                status = desc["Status"]
                print(f"Current Status: {status}")
                if status == "RUNNING":
                    backend_url = "https://" + desc["ServiceUrl"]
                    print(f"✓ Backend deployed successfully at: {backend_url}")
                    break
                elif status in ["FAILED", "DELETED"]:
                    print("Error: App Runner service deployment failed.")
                    sys.exit(1)
                time.sleep(15)
    except Exception as e:
        print(f"Failed to deploy App Runner: {e}")
        print("Note: If you received a SubscriptionRequiredException, please verify your AWS billing account.")
        sys.exit(1)

    # 3. Deploy AWS Amplify App
    print("\nStep 3: Deploying Vite React Frontend to AWS Amplify...")
    
    try:
        # Check if app already exists
        apps = amplify.list_apps()["apps"]
        existing_app = next((a for a in apps if a["name"] == "aethercoo-frontend"), None)
        
        # Prepare Env Vars
        env_vars = {
            "VITE_API_URL": backend_url,
            "VITE_WS_URL": backend_url.replace("https://", "wss://")
        }
        
        app_id = None
        if existing_app:
            app_id = existing_app["appId"]
            print(f"Frontend app already exists (ID: {app_id}). Updating environment variables...")
            amplify.update_app(
                appId=app_id,
                environmentVariables=env_vars
            )
        else:
            # We require a GitHub personal access token (PAT) or Oauth configuration
            # In the AWS Console, this is linked automatically.
            # Programmatically, we create the App and direct the user to connect it, or try with basic settings.
            create_app_res = amplify.create_app(
                name="aethercoo-frontend",
                description="AetherCOO Frontend Dashboard",
                repository=repo_url,
                platform="WEB",
                environmentVariables=env_vars
            )
            app_id = create_app_res["app"]["appId"]
            print(f"Created Amplify App: {create_app_res['app']['defaultDomain']}")
            
            # Create a branch
            amplify.create_branch(
                appId=app_id,
                branchName=branch,
                enableAutoBuild=True
            )
            print(f"Linked branch: {branch}")
            
            # Start job build
            amplify.start_job(
                appId=app_id,
                branchName=branch,
                jobType="RELEASE"
            )
            print("Triggered initial build pipeline on AWS Amplify!")
            
        print("\n" + "="*80)
        print("DEPLOYMENT CONFIGURATION COMPLETE!")
        print(f"1. Backend (App Runner): {backend_url}")
        print(f"2. Frontend (Amplify Console): https://console.aws.amazon.com/amplify/home?region={region}#/{app_id}")
        print("="*80)
        
    except Exception as e:
        print(f"Amplify deployment failed: {e}")

if __name__ == "__main__":
    deploy()
