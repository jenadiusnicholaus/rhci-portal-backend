"""
Management command to fix billing calculation errors
Fixes cases where total was calculated as monthly_rate * months * 7 instead of monthly_rate * months
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fix billing calculation errors where total was multiplied by 7 days'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes',
        )
        parser.add_argument(
            '--fix-all',
            action='store_true',
            help='Fix all incorrect billing records',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        fix_all = options['fix_all']

        if not fix_all and not dry_run:
            self.stdout.write(
                self.style.ERROR('Please specify either --dry-run or --fix-all')
            )
            return

        self.stdout.write(
            self.style.SUCCESS('Starting billing calculation fix...')
        )

        # Note: This is a template since the actual billing models are not in this project
        # You'll need to adapt this to your actual billing model structure
        
        incorrect_records = self.find_incorrect_records()
        
        if not incorrect_records:
            self.stdout.write(
                self.style.SUCCESS('No incorrect billing records found!')
            )
            return

        self.stdout.write(
            f"Found {len(incorrect_records)} incorrect billing records"
        )

        if dry_run:
            self.show_dry_run(incorrect_records)
        else:
            self.fix_records(incorrect_records)

    def find_incorrect_records(self):
        """
        Find billing records where total was calculated incorrectly
        This is a template - adapt to your actual billing model
        """
        # Example logic - replace with your actual billing model
        incorrect_records = []
        
        # Pseudocode - replace with your actual model and field names
        """
        from billing.models import Bill  # Replace with your actual model
        
        bills = Bill.objects.filter(
            monthly_rate__isnull=False,
            number_of_months__isnull=False,
            total_amount__isnull=False
        )
        
        for bill in bills:
            expected_total = bill.monthly_rate * bill.number_of_months
            # Check if it was incorrectly multiplied by 7
            if bill.total_amount == expected_total * 7:
                incorrect_records.append({
                    'id': bill.id,
                    'monthly_rate': bill.monthly_rate,
                    'months': bill.number_of_months,
                    'current_total': bill.total_amount,
                    'correct_total': expected_total,
                    'bill': bill
                })
        """
        
        return incorrect_records

    def show_dry_run(self, incorrect_records):
        """Show what would be fixed"""
        self.stdout.write(self.style.WARNING('\n=== DRY RUN - What would be fixed ==='))
        
        for record in incorrect_records:
            self.stdout.write(
                f"\nBill ID: {record['id']}\n"
                f"  Monthly Rate: TZS {record['monthly_rate']:,}\n"
                f"  Months: {record['months']}\n"
                f"  Current (Wrong) Total: TZS {record['current_total']:,}\n"
                f"  Correct Total: TZS {record['correct_total']:,}\n"
                f"  Difference: TZS {record['current_total'] - record['correct_total']:,}"
            )

    def fix_records(self, incorrect_records):
        """Fix the incorrect billing records"""
        self.stdout.write(self.style.WARNING('\n=== FIXING RECORDS ==='))
        
        with transaction.atomic():
            for record in incorrect_records:
                bill = record['bill']
                old_total = bill.total_amount
                new_total = record['correct_total']
                
                # Update the total amount
                bill.total_amount = new_total
                bill.save(update_fields=['total_amount'])
                
                self.stdout.write(
                    f"Fixed Bill {record['id']}: "
                    f"TZS {old_total:,} → TZS {new_total:,} "
                    f"(saved TZS {old_total - new_total:,})"
                )

        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully fixed {len(incorrect_records)} billing records!')
        )

    def create_correction_report(self, incorrect_records):
        """Create a report of all corrections made"""
        total_overcharged = sum(
            record['current_total'] - record['correct_total'] 
            for record in incorrect_records
        )
        
        self.stdout.write(self.style.SUCCESS('\n=== CORRECTION SUMMARY ==='))
        self.stdout.write(f"Total Records Fixed: {len(incorrect_records)}")
        self.stdout.write(f"Total Amount Overcharged: TZS {total_overcharged:,}")
        
        # You could also create a CSV report here
        import csv
        from datetime import datetime
        
        filename = f"billing_correction_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                'Bill ID', 'Monthly Rate', 'Months', 
                'Wrong Total', 'Correct Total', 'Amount Overcharged'
            ])
            
            for record in incorrect_records:
                writer.writerow([
                    record['id'],
                    record['monthly_rate'],
                    record['months'],
                    record['current_total'],
                    record['correct_total'],
                    record['current_total'] - record['correct_total']
                ])
        
        self.stdout.write(f"Detailed report saved to: {filename}")
