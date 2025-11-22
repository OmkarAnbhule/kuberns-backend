import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.projects.models import Plan, Template


class Command(BaseCommand):
    help = 'Update Plan and Template models from JSON fixture files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--templates-only',
            action='store_true',
            help='Update only templates',
        )
        parser.add_argument(
            '--plans-only',
            action='store_true',
            help='Update only plans',
        )

    def handle(self, *args, **options):
        templates_only = options.get('templates_only', False)
        plans_only = options.get('plans_only', False)
        
        # Paths to JSON files
        base_dir = settings.BASE_DIR
        templates_json_path = os.path.join(base_dir, 'apps', 'core', 'data', 'templates.json')
        plans_json_path = os.path.join(base_dir, 'apps', 'core', 'data', 'plans.json')

        if not plans_only:
            self.update_templates(templates_json_path)
        
        if not templates_only:
            self.update_plans(plans_json_path)

        self.stdout.write(self.style.SUCCESS('Successfully updated fixtures!'))

    def update_templates(self, json_path):
        """Update Template models from templates.json"""
        self.stdout.write('Updating templates...')
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                templates_data = data.get('templates', [])

            updated_count = 0
            created_count = 0

            for template_data in templates_data:
                name = template_data.get('name')
                slug = template_data.get('slug')
                category = template_data.get('category', '')

                # Update or create template
                template, created = Template.objects.update_or_create(
                    name=name,
                    defaults={
                        'slug': slug,
                        'category': category,
                    }
                )

                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f'  Created: {name}'))
                else:
                    updated_count += 1
                    self.stdout.write(self.style.SUCCESS(f'  Updated: {name}'))

            self.stdout.write(
                self.style.SUCCESS(
                    f'Templates: {created_count} created, {updated_count} updated'
                )
            )

        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'Error: templates.json not found at {json_path}')
            )
        except json.JSONDecodeError as e:
            self.stdout.write(
                self.style.ERROR(f'Error: Invalid JSON in templates.json - {str(e)}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error updating templates: {str(e)}')
            )

    def update_plans(self, json_path):
        """Update Plan models from plans.json"""
        self.stdout.write('Updating plans...')
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                plans_data = json.load(f)

            updated_count = 0
            created_count = 0

            for plan_data in plans_data:
                name = plan_data.get('name')
                
                # Parse storage (e.g., "10 GB" -> 10)
                storage_str = plan_data.get('storage', '0 GB')
                storage_gb = int(storage_str.split()[0])
                
                # Parse bandwidth (e.g., "10 GB" -> 10)
                bandwidth_str = plan_data.get('bandwidth', '0 GB')
                bandwidth_gb = int(bandwidth_str.split()[0])
                
                # Parse memory (e.g., "10 GB" -> convert to MB)
                memory_str = plan_data.get('memory', '0 GB')
                memory_gb = int(memory_str.split()[0])
                ram_mb = memory_gb * 1024  # Convert GB to MB
                
                # Parse CPU (e.g., "2 GB" -> 2 cores, note: this seems to be in GB format but represents cores)
                cpu_str = plan_data.get('cpu', '0 GB')
                cpu_cores = int(cpu_str.split()[0])
                
                # Parse monthly cost (e.g., "₹500" -> 500.00)
                monthly_cost_str = plan_data.get('monthlyCost', '₹0')
                price_monthly = float(monthly_cost_str.replace('₹', '').replace(',', ''))
                
                # Parse hourly cost (e.g., "₹10" -> 10.00)
                hourly_cost_str = plan_data.get('pricePerHour', '₹0')
                price_hourly = float(hourly_cost_str.replace('₹', '').replace(',', ''))

                # Update or create plan
                plan, created = Plan.objects.update_or_create(
                    name=name,
                    defaults={
                        'cpu_cores': cpu_cores,
                        'ram_mb': ram_mb,
                        'bandwidth_gb': bandwidth_gb,
                        'price_monthly': price_monthly,
                        'price_hourly': price_hourly,
                        'storage_gb': storage_gb,
                    }
                )

                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f'  Created: {name}'))
                else:
                    updated_count += 1
                    self.stdout.write(self.style.SUCCESS(f'  Updated: {name}'))

            self.stdout.write(
                self.style.SUCCESS(
                    f'Plans: {created_count} created, {updated_count} updated'
                )
            )

        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'Error: plans.json not found at {json_path}')
            )
        except json.JSONDecodeError as e:
            self.stdout.write(
                self.style.ERROR(f'Error: Invalid JSON in plans.json - {str(e)}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error updating plans: {str(e)}')
            )

