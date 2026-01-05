"""
User profile template.

Provides schema for user/customer profile records including
user ID, name, email, demographic information, and signup date.
"""

from synth.agent.templates.base import SchemaTemplate, TemplateField


class UserProfileTemplate(SchemaTemplate):
    """
    Template for user/customer profile records.

    Fields:
    - user_id: Unique user identifier
    - username: Username or handle
    - email: Email address (unique)
    - first_name: First name
    - last_name: Last name
    - age: User age
    - country: Country of residence
    - signup_date: When the user signed up
    - is_active: Whether the account is active
    - subscription_type: Type of subscription
    """

    template_id = "user_profile"
    name = "User Profile"
    description = "User/customer profile records with demographics and account details"
    category = "user"

    def _define_fields(self) -> None:
        """Define the fields for user profiles."""
        # User ID
        self.add_field(TemplateField(
            name="user_id",
            data_type="string",
            description="Unique user identifier",
            unique=True,
            nullable=False,
            constraints={"min_length": 8, "max_length": 12},
        ))

        # Username
        self.add_field(TemplateField(
            name="username",
            data_type="string",
            description="Username or handle",
            unique=True,
            nullable=False,
            constraints={"min_length": 3, "max_length": 20},
        ))

        # Email
        self.add_field(TemplateField(
            name="email",
            data_type="string",
            description="Email address",
            unique=True,
            nullable=False,
            constraints={"min_length": 10, "max_length": 50},
        ))

        # First Name
        self.add_field(TemplateField(
            name="first_name",
            data_type="string",
            description="First name",
            nullable=False,
            constraints={"min_length": 2, "max_length": 30},
        ))

        # Last Name
        self.add_field(TemplateField(
            name="last_name",
            data_type="string",
            description="Last name",
            nullable=False,
            constraints={"min_length": 2, "max_length": 30},
        ))

        # Age
        self.add_field(TemplateField(
            name="age",
            data_type="integer",
            description="User age",
            nullable=False,
            constraints={"range": (13, 100)},
        ))

        # Country
        self.add_field(TemplateField(
            name="country",
            data_type="categorical",
            description="Country of residence",
            nullable=False,
            constraints={
                "values": [
                    "USA",
                    "UK",
                    "Canada",
                    "Germany",
                    "France",
                    "Australia",
                    "Japan",
                    "Other",
                ]
            },
        ))

        # Signup Date
        self.add_field(TemplateField(
            name="signup_date",
            data_type="datetime",
            description="Account registration date",
            nullable=False,
        ))

        # Is Active
        self.add_field(TemplateField(
            name="is_active",
            data_type="boolean",
            description="Whether the account is active",
            nullable=False,
        ))

        # Subscription Type
        self.add_field(TemplateField(
            name="subscription_type",
            data_type="categorical",
            description="Subscription tier",
            nullable=False,
            constraints={"values": ["free", "basic", "premium", "enterprise"]},
        ))
