#!/usr/bin/env python
"""
Remediation script for orphaned Customer Users without profiles.

This script fixes users with user_type='customer' that do not have
corresponding Customer profiles. It provides two options:
1. Create missing Customer profiles
2. Delete orphaned User accounts

Run with: python fix_orphaned_users.py [create|delete] [--dry-run]
"""
import os
import sys

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings.development')

import django
django.setup()

from django.contrib.auth import get_user_model
from mainapp.models import Customer
from django.db import transaction

User = get_user_model()


def list_orphaned_users():
    """List all customer Users without Customer profiles."""
    orphaned = User.objects.filter(user_type='customer').exclude(
        customer_profile__isnull=False
    )
    
    print("=" * 80)
    print("ORPHANED CUSTOMER USERS")
    print("=" * 80)
    print(f"\nTotal orphaned users: {orphaned.count()}")
    print()
    
    for user in orphaned:
        print(f"Username: {user.username}")
        print(f"  Email: {user.email}")
        print(f"  Phone: {user.phone}")
        print(f"  First Name: {user.first_name}")
        print(f"  Last Name: {user.last_name}")
        print(f"  Created: {user.date_joined}")
        print(f"  Is Active: {user.is_active}")
        
        # Check for related data (dogs, appointments)
        # Note: We can't check for appointments directly because they require Customer
        # But we can check if this user might have related issues
        
        print()
    
    return orphaned


def create_customer_profiles(users, dry_run=False):
    """Create Customer profiles for orphaned Users."""
    print("=" * 80)
    print(f"CREATING CUSTOMER PROFILES ({'[DRY RUN]' if dry_run else '[EXECUTE]'})")
    print("=" * 80)
    print()
    
    created_count = 0
    failed_count = 0
    
    with transaction.atomic():
        for user in users:
            try:
                if dry_run:
                    print(f"[DRY RUN] Would create profile for: {user.username}")
                    print(f"  Name: {user.get_full_name() or user.username}")
                    print(f"  Email: {user.email}")
                    print(f"  Phone: {user.phone or ''}")
                    created_count += 1
                else:
                    # Create the Customer profile
                    customer = Customer.objects.create(
                        user=user,
                        name=user.get_full_name() or user.username,
                        email=user.email,
                        phone=user.phone or ''
                    )
                    print(f"Created profile for: {user.username} -> Customer ID: {customer.id}")
                    created_count += 1
                    
            except Exception as e:
                print(f"ERROR creating profile for {user.username}: {e}")
                failed_count += 1
                if not dry_run:
                    # In dry run mode, continue; in execute mode, the transaction
                    # won't be committed unless all succeed
                    raise
        
        if dry_run:
            print()
            print(f"[DRY RUN] Summary: Would create {created_count} profiles")
        else:
            print()
            print(f"EXECUTE Summary: Created {created_count} profiles, {failed_count} failed")
            print("Transaction will be committed after all operations complete.")
    
    return created_count, failed_count


def delete_orphaned_users(users, dry_run=False):
    """Delete orphaned User accounts."""
    print("=" * 80)
    print(f"DELETING ORPHANED USERS ({'[DRY RUN]' if dry_run else '[EXECUTE]'})")
    print("=" * 80)
    print()
    print("WARNING: This will PERMANENTLY DELETE User accounts!")
    print("Affected users will lose access to the system.")
    print()
    
    if not dry_run:
        response = input("Are you SURE you want to delete these accounts? Type 'yes' to confirm: ")
        if response.lower() != 'yes':
            print("Operation cancelled.")
            return 0
    
    count = 0
    for user in users:
        user_name = user.username
        if dry_run:
            print(f"[DRY RUN] Would delete user: {user_name}")
            count += 1
        else:
            try:
                user.delete()
                print(f"Deleted user: {user_name}")
                count += 1
            except Exception as e:
                print(f"ERROR deleting {user_name}: {e}")
    
    print()
    summary = f"[DRY RUN] Would delete" if dry_run else "Deleted"
    print(f"{summary} {count} users")
    
    return count


def main():
    """Main execution function."""
    action = sys.argv[1] if len(sys.argv) > 1 else None
    dry_run = '--dry-run' in sys.argv
    
    if not action or action not in ['list', 'create', 'delete']:
        print("""
usage: python fix_orphaned_users.py [command] [--dry-run]

Commands:
  list    - List all orphaned customer Users
  create  - Create Customer profiles for orphaned Users
  delete  - Delete orphaned User accounts

Options:
  --dry-run  - Preview changes without executing

Examples:
  python fix_orphaned_users.py list
  python fix_orphaned_users.py create --dry-run
  python fix_orphaned_users.py delete
  python fix_orphaned_users.py create
""")
        sys.exit(1)
    
    print()
    print("REMEDIATION SCRIPT FOR ORPHANED CUSTOMER USERS")
    print("=" * 80)
    print()
    
    # List orphaned users
    orphaned = list_orphaned_users()
    
    if orphaned.count() == 0:
        print("No orphaned users found. System is clean!")
        return
    
    print()
    
    if action == 'list':
        # Already listed above
        pass
    elif action == 'create':
        print()
        print("Creating Customer profiles for orphaned Users...")
        print()
        created, failed = create_customer_profiles(orphaned, dry_run)
        
        if not dry_run:
            print()
            print("Verification:")
            remaining = User.objects.filter(user_type='customer').exclude(
                customer_profile__isnull=False
            ).count()
            print(f"Orphaned users remaining: {remaining}")
    elif action == 'delete':
        print()
        print("Deleting orphaned User accounts...")
        print()
        deleted = delete_orphaned_users(orphaned, dry_run)
        
        if not dry_run:
            print()
            print("Verification:")
            remaining_count = User.objects.filter(user_type='customer').count()
            print(f"Total customer users remaining: {remaining_count}")
    
    print()
    print("=" * 80)
    print("Operation complete!")
    print("=" * 80)


if __name__ == '__main__':
    main()