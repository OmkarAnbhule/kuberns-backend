#!/usr/bin/env python
"""
Quick script to delete a problematic security group.

Usage:
    python delete_security_group.py

This will delete the 'kuberns-Demo' security group that's causing issues.
"""

import boto3
import os
from dotenv import load_dotenv

load_dotenv()

def delete_security_group(group_name='kuberns-Demo', region='us-east-1'):
    """Delete a security group by name."""
    
    # Get AWS credentials from environment
    access_key = os.getenv('AWS_DEMO_ACCESS_KEY')
    secret_key = os.getenv('AWS_DEMO_SECRET_KEY')
    
    if not access_key or not secret_key:
        print("❌ Error: AWS credentials not found in .env file")
        print("   Please set AWS_DEMO_ACCESS_KEY and AWS_DEMO_SECRET_KEY")
        return False
    
    try:
        # Create EC2 client
        ec2 = boto3.client(
            'ec2',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        print(f"🔍 Searching for security group '{group_name}' in {region}...")
        
        # Find the security group
        response = ec2.describe_security_groups(
            Filters=[
                {'Name': 'group-name', 'Values': [group_name]}
            ]
        )
        
        if not response['SecurityGroups']:
            print(f"❌ Security group '{group_name}' not found!")
            print(f"   It may have already been deleted.")
            return False
        
        sg = response['SecurityGroups'][0]
        sg_id = sg['GroupId']
        
        print(f"✅ Found security group: {sg_id}")
        print(f"   Name: {sg['GroupName']}")
        print(f"   VPC: {sg.get('VpcId', 'N/A')}")
        print(f"   Description: {sg.get('Description', 'N/A')}")
        
        # Check if any instances are using it
        instances = ec2.describe_instances(
            Filters=[
                {'Name': 'instance.group-id', 'Values': [sg_id]},
                {'Name': 'instance-state-name', 'Values': ['pending', 'running', 'stopping', 'stopped']}
            ]
        )
        
        if instances['Reservations']:
            print(f"⚠️  Warning: {len(instances['Reservations'])} instance(s) are still using this security group!")
            print(f"   You need to terminate these instances first.")
            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    print(f"   - Instance: {instance['InstanceId']} ({instance['State']['Name']})")
            return False
        
        # Confirm deletion
        print(f"\n⚠️  Are you sure you want to delete security group '{group_name}' ({sg_id})?")
        confirm = input("   Type 'yes' to confirm: ")
        
        if confirm.lower() != 'yes':
            print("❌ Deletion cancelled.")
            return False
        
        # Delete the security group
        print(f"🗑️  Deleting security group...")
        ec2.delete_security_group(GroupId=sg_id)
        
        print(f"✅ Successfully deleted security group '{group_name}' ({sg_id})")
        print(f"\n✨ You can now create instances with project name 'Demo' again!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Security Group Cleanup Tool")
    print("=" * 60)
    print()
    
    success = delete_security_group()
    
    print()
    if success:
        print("🎉 Done! You can now retry creating your instance.")
    else:
        print("💡 Alternative: Use a different project name (e.g., 'Test' instead of 'Demo')")
    print()

