"""
AWS provisioning utilities using boto3 for EC2 instance management.
"""

import boto3
from typing import Dict, Optional
from django.conf import settings
import logging
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)

# Hardcoded configuration for minimal instance setup
DEFAULT_INSTANCE_TYPE = "t3.micro"  # Smallest general purpose (2 vCPU, 1GB RAM)
DEFAULT_DISK_SIZE_GB = 8  # Minimum allowed disk size

# Region to AMI mapping for Ubuntu 22.04 LTS (as of 2024)
# These are official Canonical Ubuntu AMIs
REGION_AMI_MAPPING = {
    # US Regions
    'us-east-1': 'ami-0c7217cdde317cfec',      # N. Virginia
    'us-east-2': 'ami-0a695f0d95cefc163',      # Ohio
    'us-west-1': 'ami-0ce2cb35386fc22e9',      # N. California
    'us-west-2': 'ami-008fe2fc65df48dac',      # Oregon
    
    # Europe Regions
    'eu-west-1': 'ami-0905a3c97561e0b69',      # Ireland
    'eu-west-2': 'ami-0eb260c4d5475b901',      # London
    'eu-west-3': 'ami-00ac45f3035ff009e',      # Paris
    'eu-central-1': 'ami-0faab6bdbac9158f4',   # Frankfurt
    'eu-north-1': 'ami-0014ce3e52359afbd',     # Stockholm
    
    # Asia Pacific Regions
    'ap-south-1': 'ami-0f58b397bc5c1f2e8',     # Mumbai
    'ap-northeast-1': 'ami-0d52744d6551d851e', # Tokyo
    'ap-northeast-2': 'ami-0c9c942bd7bf113a2', # Seoul
    'ap-southeast-1': 'ami-0dc2d3e4c0f9ebd18', # Singapore
    'ap-southeast-2': 'ami-0310483fb2b488153', # Sydney
    
    # Canada
    'ca-central-1': 'ami-0c9bfc21ac5bf10eb',   # Canada Central
    
    # South America
    'sa-east-1': 'ami-0c820c196a818d66a',      # São Paulo
}

# Default ports to open (SSH + user-specified port)
DEFAULT_PORTS = [22]  # SSH is always included


def provision_ec2_instance(
    aws_access_key: str,
    aws_secret_key: str,
    region: str,
    project_name: str,
    port: int = 80
) -> Dict:
    """
    Provision a minimal EC2 instance using boto3.
    
    Uses hardcoded minimal configuration:
    - Instance Type: t3.micro (2 vCPU, 1GB RAM)
    - Disk Size: 8 GB (minimum)
    - AMI: Ubuntu 22.04 LTS (auto-selected for region)
    - Ports: 22 (SSH) + user-specified port
    
    Args:
        aws_access_key: AWS access key
        aws_secret_key: AWS secret key
        region: AWS region (e.g., 'us-east-1')
        project_name: Project name for tagging
        port: Single application port to open (SSH port 22 always included)
    
    Returns:
        Dict with instance details: {
            'instance_id': str, 
            'public_ip': str, 
            'private_ip': str,
            'status': str,
            'instance_type': str,
            'ami_id': str
        }
    
    Raises:
        Exception: If provisioning fails
    """
    
    # Use hardcoded defaults
    instance_type = DEFAULT_INSTANCE_TYPE
    disk_size_gb = DEFAULT_DISK_SIZE_GB
    instance_name = f'kuberns-{project_name}'
    
    # Ports: SSH (22) + user-specified port
    ports = [22, port] if port != 22 else [22]
    
    # Create user data script to install and run a simple web server
    user_data_script = f"""#!/bin/bash
# Update system
apt-get update -y

# Install nginx
apt-get install -y nginx

# Create a simple welcome page
cat > /var/www/html/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Kuberns Instance</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        .container {{
            background: rgba(255,255,255,0.1);
            padding: 30px;
            border-radius: 10px;
            backdrop-filter: blur(10px);
        }}
        h1 {{ margin-top: 0; }}
        .info {{ background: rgba(255,255,255,0.2); padding: 15px; border-radius: 5px; margin: 20px 0; }}
        code {{ background: rgba(0,0,0,0.3); padding: 2px 6px; border-radius: 3px; }}
        .badge {{ 
            display: inline-block;
            background: rgba(0,255,0,0.2);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.9em;
            margin-right: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Kuberns Instance Running!</h1>
        <p>Your EC2 instance is successfully deployed and running.</p>
        
        <div class="info">
            <strong>Project:</strong> {project_name}<br>
            <strong>Instance Type:</strong> t3.micro<br>
            <strong>Port:</strong> {port}<br>
            <strong>Region:</strong> {region}
        </div>
        
        <h2>Instance Details</h2>
        <ul>
            <li><span class="badge">&#x2713;</span> Nginx web server is installed and running</li>
            <li><span class="badge">&#x2713;</span> Ubuntu 22.04 LTS operating system</li>
            <li><span class="badge">&#x2713;</span> Security group configured for ports: {', '.join(map(str, ports))}</li>
        </ul>
        
        <h2>Next Steps</h2>
        <p>You can now deploy your application to this instance via SSH or your CI/CD pipeline.</p>
        
        <p style="margin-top: 30px; font-size: 0.9em; opacity: 0.8;">
            Powered by Kuberns
        </p>
    </div>
</body>
</html>
EOF

# Configure nginx to listen on the specified port
if [ {port} -ne 80 ]; then
    cat > /etc/nginx/sites-available/default << EOF
server {{
    listen {port} default_server;
    listen [::]:{port} default_server;
    
    root /var/www/html;
    index index.html;
    
    server_name _;
    
    location / {{
        try_files \$uri \$uri/ =404;
    }}
}}
EOF
fi

# Restart nginx to apply changes
systemctl restart nginx
systemctl enable nginx
"""
    
    try:
        # Create EC2 client
        ec2_client = boto3.client(
            'ec2',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region
        )
        
        logger.info(f"Provisioning EC2 instance in {region} for project {project_name}")
        
        # Get AMI from region mapping
        ami = REGION_AMI_MAPPING.get(region)
        if not ami:
            # Fallback to dynamic lookup if region not in mapping
            logger.warning(f"No AMI mapping found for region {region}, attempting dynamic lookup")
            ami = get_default_ubuntu_ami(ec2_client)
        
        logger.info(f"Using AMI: {ami} for region {region}")
        
        # Create or get security group
        security_group_id = ensure_security_group(ec2_client, project_name, ports)
        logger.info(f"Using security group: {security_group_id}")
        
        # Prepare launch parameters with minimal configuration
        launch_params = {
            'ImageId': ami,
            'MinCount': 1,
            'MaxCount': 1,
            'InstanceType': instance_type,
            'SecurityGroupIds': [security_group_id],
            'UserData': user_data_script,  # Install and run nginx on startup
            'BlockDeviceMappings': [{
                'DeviceName': '/dev/sda1',
                'Ebs': {
                    'VolumeSize': disk_size_gb,
                    'VolumeType': 'gp3',
                    'DeleteOnTermination': True
                }
            }],
            'TagSpecifications': [{
                'ResourceType': 'instance',
                'Tags': [
                    {'Key': 'Name', 'Value': instance_name},
                    {'Key': 'Project', 'Value': project_name},
                    {'Key': 'ManagedBy', 'Value': 'Kuberns'},
                    {'Key': 'InstanceType', 'Value': instance_type},
                    {'Key': 'DiskSize', 'Value': str(disk_size_gb)}
                ]
            }]
        }
        
        # Launch instance
        response = ec2_client.run_instances(**launch_params)
        instance = response['Instances'][0]
        instance_id = instance['InstanceId']
        
        logger.info(f"Launched instance: {instance_id}")
        
        # Wait for instance to be running
        waiter = ec2_client.get_waiter('instance_running')
        waiter.wait(InstanceIds=[instance_id])
        
        logger.info(f"Instance {instance_id} is now running")
        
        # Get instance details
        instances = ec2_client.describe_instances(InstanceIds=[instance_id])
        instance = instances['Reservations'][0]['Instances'][0]
        
        return {
            'instance_id': instance_id,
            'public_ip': instance.get('PublicIpAddress'),
            'private_ip': instance.get('PrivateIpAddress'),
            'status': instance['State']['Name'],
            'instance_type': instance['InstanceType'],
            'ami_id': instance['ImageId']
        }
    
    except NoCredentialsError:
        logger.error("AWS credentials not found or invalid")
        raise Exception("Invalid AWS credentials provided")
    
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"AWS ClientError [{error_code}]: {error_message}")
        raise Exception(f"AWS Error: {error_message}")
    
    except Exception as e:
        logger.error(f"Unexpected error during provisioning: {str(e)}")
        raise


def get_default_ubuntu_ami(ec2_client) -> str:
    """
    Get the latest Ubuntu 22.04 LTS AMI ID for the region.
    
    Returns:
        AMI ID string
    """
    try:
        response = ec2_client.describe_images(
            Filters=[
                {'Name': 'name', 'Values': ['ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*']},
                {'Name': 'architecture', 'Values': ['x86_64']},
                {'Name': 'state', 'Values': ['available']}
            ],
            Owners=['099720109477']  # Canonical
        )
        
        # Sort by creation date and get the latest
        if response['Images']:
            images = sorted(response['Images'], key=lambda x: x['CreationDate'], reverse=True)
            return images[0]['ImageId']
        else:
            # Fallback AMI for us-east-1 (Ubuntu 22.04 LTS)
            logger.warning("Could not find Ubuntu AMI, using fallback")
            return "ami-0c7217cdde317cfec"
    
    except Exception as e:
        logger.error(f"Error finding Ubuntu AMI: {str(e)}")
        # Fallback AMI for us-east-1
        return "ami-0c7217cdde317cfec"


def ensure_security_group(ec2_client, project_name: str, ports: list = None) -> str:
    """
    Create or get existing security group with proper rules.
    
    Args:
        ec2_client: boto3 EC2 client
        project_name: Project name for security group naming
        ports: List of ports to open (default: [22, 80, 443, 3000, 8000, 8080])
    
    Returns:
        Security group ID
    """
    if ports is None:
        ports = [22, 80, 443, 3000, 8000, 8080]
    
    group_name = f"kuberns-{project_name}"
    
    try:
        # Try to find existing security group
        response = ec2_client.describe_security_groups(
            Filters=[
                {'Name': 'group-name', 'Values': [group_name]}
            ]
        )
        
        if response['SecurityGroups']:
            security_group_id = response['SecurityGroups'][0]['GroupId']
            logger.info(f"Using existing security group: {security_group_id}")
            return security_group_id
    
    except ClientError:
        pass
    
    # Create new security group
    try:
        # Get default VPC
        vpc_response = ec2_client.describe_vpcs(Filters=[{'Name': 'isDefault', 'Values': ['true']}])
        vpc_id = vpc_response['Vpcs'][0]['VpcId'] if vpc_response['Vpcs'] else None
        
        create_params = {
            'GroupName': group_name,
            'Description': f'Kuberns security group for {project_name}'
        }
        
        if vpc_id:
            create_params['VpcId'] = vpc_id
        
        response = ec2_client.create_security_group(**create_params)
        security_group_id = response['GroupId']
        
        logger.info(f"Created new security group: {security_group_id}")
        
        # Add ingress rules dynamically based on ports list
        ip_permissions = []
        
        # Create a permission rule for each port
        for port in ports:
            port_name = {
                22: 'SSH',
                80: 'HTTP',
                443: 'HTTPS',
                3000: 'App port 3000',
                8000: 'App port 8000',
                8080: 'App port 8080'
            }.get(port, f'Port {port}')
            
            ip_permissions.append({
                'IpProtocol': 'tcp',
                'FromPort': port,
                'ToPort': port,
                'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': port_name}]
            })
        
        ec2_client.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=ip_permissions
        )
        
        logger.info(f"Added ingress rules to security group {security_group_id}")
        
        return security_group_id
    
    except ClientError as e:
        logger.error(f"Error creating security group: {str(e)}")
        raise


def get_instance_status(
    aws_access_key: str,
    aws_secret_key: str,
    region: str,
    instance_id: str
) -> Dict:
    """
    Get the current status of an EC2 instance.
    
    Args:
        aws_access_key: AWS access key
        aws_secret_key: AWS secret key
        region: AWS region
        instance_id: EC2 instance ID
    
    Returns:
        Dict with instance status information
    """
    try:
        ec2_client = boto3.client(
            'ec2',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region
        )
        
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        
        if not response['Reservations']:
            raise Exception(f"Instance {instance_id} not found")
        
        instance = response['Reservations'][0]['Instances'][0]
        
        return {
            'instance_id': instance_id,
            'status': instance['State']['Name'],
            'public_ip': instance.get('PublicIpAddress'),
            'private_ip': instance.get('PrivateIpAddress'),
            'instance_type': instance['InstanceType'],
            'launch_time': instance['LaunchTime'].isoformat()
        }
    
    except ClientError as e:
        logger.error(f"Error getting instance status: {str(e)}")
        raise Exception(f"Failed to get instance status: {str(e)}")
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise


def terminate_instance(
    aws_access_key: str,
    aws_secret_key: str,
    region: str,
    instance_id: str
) -> bool:
    """
    Terminate an EC2 instance.
    
    Args:
        aws_access_key: AWS access key
        aws_secret_key: AWS secret key
        region: AWS region
        instance_id: EC2 instance ID
    
    Returns:
        True if termination was successful
    """
    try:
        ec2_client = boto3.client(
            'ec2',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region
        )
        
        logger.info(f"Terminating instance {instance_id} in {region}")
        
        response = ec2_client.terminate_instances(InstanceIds=[instance_id])
        
        if response['TerminatingInstances']:
            current_state = response['TerminatingInstances'][0]['CurrentState']['Name']
            logger.info(f"Instance {instance_id} is now {current_state}")
            return True
        
        return False
    
    except ClientError as e:
        logger.error(f"Error terminating instance: {str(e)}")
        raise Exception(f"Failed to terminate instance: {str(e)}")
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise