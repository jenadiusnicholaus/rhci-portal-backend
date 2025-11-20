"""
Custom Swagger/OpenAPI schema generator for ordered tag display
"""
from drf_yasg.generators import OpenAPISchemaGenerator
from collections import OrderedDict


class OrderedTagSchemaGenerator(OpenAPISchemaGenerator):
    """
    Custom schema generator that ensures tags are ordered numerically
    instead of alphabetically in Swagger UI.
    """
    
    def get_schema(self, request=None, public=False):
        """Override to define explicit tag ordering"""
        schema = super().get_schema(request, public)
        
        # Define the explicit tag order
        ordered_tags = [
            {'name': 'Authentication & Registration', 'description': 'User authentication and registration endpoints'},
            {'name': 'Donor Management (Private)', 'description': 'Private donor profile management'},
            {'name': 'Donor Management (Public)', 'description': 'Public donor profile viewing'},
            {'name': 'Donations', 'description': 'Donation operations'},
            {'name': 'Admin - Donations', 'description': 'Admin donation management'},
            {'name': 'Patient Management (Private)', 'description': 'Private patient profile operations'},
            {'name': 'Admin - User Management', 'description': 'Admin user management'},
            {'name': 'Patient Management (Public)', 'description': 'Public patient profile viewing'},
            {'name': 'Admin - Patient Review & Management', 'description': 'Admin patient review and approval'},
            {'name': 'Admin - Timeline Management', 'description': 'Admin timeline management'},
            {'name': 'Public - Patient Profiles', 'description': 'Public patient profile listings'},
            {'name': 'Lookups', 'description': 'Country and other lookup endpoints'},
            {'name': 'Campaigns (Public)', 'description': 'Public campaign viewing'},
            {'name': 'Campaigns (Launcher)', 'description': 'Campaign launcher operations'},
            {'name': 'Admin - Campaigns', 'description': 'Admin campaign management'},
            {'name': 'Admin - Payment Methods', 'description': 'Admin payment method management'},
        ]
        
        # Collect all existing tags from the schema
        existing_tags = {}
        for tag in schema.get('tags', []):
            tag_name = tag.get('name', '')
            existing_tags[tag_name] = tag
        
        # Replace with ordered tags, only including those that exist
        schema['tags'] = [tag for tag in ordered_tags if tag['name'] in existing_tags]
        
        # Debug: Add any tags that weren't in our ordered list (to catch issues)
        for tag_name, tag_data in existing_tags.items():
            if not any(t['name'] == tag_name for t in schema['tags']):
                # Add unmatched tags at the end with a warning prefix
                schema['tags'].append({
                    'name': f'⚠️ {tag_name}',
                    'description': f'WARNING: Tag not in ordered list - {tag_data.get("description", "")}'
                })
        
        return schema
