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
            {'name': '1. Authentication & Registration', 'description': 'User authentication and registration endpoints'},
            {'name': '2. Donor Management (Private)', 'description': 'Private donor profile management'},
            {'name': '3. Donor Management (Public)', 'description': 'Public donor profile viewing'},
            {'name': '4. Donations', 'description': 'Donation operations'},
            {'name': '5. Admin - Donations', 'description': 'Admin donation management'},
            {'name': '6. Patient Management (Private)', 'description': 'Private patient profile operations'},
            {'name': '7. Admin - User Management', 'description': 'Admin user management'},
            {'name': '8. Patient Management (Public)', 'description': 'Public patient profile viewing'},
            {'name': '9. Admin - Patient Review & Management', 'description': 'Admin patient review and approval'},
            {'name': '10. Admin - Timeline Management', 'description': 'Admin timeline management'},
            {'name': '11. Public - Patient Profiles', 'description': 'Public patient profile listings'},
            {'name': '12. Lookups', 'description': 'Country and other lookup endpoints'},
            {'name': '13. Campaigns (Public)', 'description': 'Public campaign viewing'},
            {'name': '14. Campaigns (Launcher)', 'description': 'Campaign launcher operations'},
            {'name': '15. Admin - Campaigns', 'description': 'Admin campaign management'},
            {'name': '16. Admin - Payment Methods', 'description': 'Admin payment method management'},
        ]
        
        # Only include tags that actually exist in the schema
        existing_tags = {tag.get('name') for tag in schema.get('tags', [])}
        schema['tags'] = [tag for tag in ordered_tags if tag['name'] in existing_tags]
        
        return schema
