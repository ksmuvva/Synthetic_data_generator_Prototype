"""
E-commerce order template.

Provides schema for e-commerce order records including
order ID, customer ID, product details, quantity, price, and status.
"""

from synth.agent.templates.base import SchemaTemplate, TemplateField


class ECommerceOrderTemplate(SchemaTemplate):
    """
    Template for e-commerce order records.

    Fields:
    - order_id: Unique order identifier
    - customer_id: Customer who placed the order
    - product_id: Product identifier
    - product_name: Name of the product
    - quantity: Number of items ordered
    - unit_price: Price per unit
    - total_price: Total price (quantity * unit_price)
    - order_date: When the order was placed
    - status: Order status
    - shipping_address: Delivery address
    """

    template_id = "ecommerce_order"
    name = "E-commerce Order"
    description = "E-commerce order records with product, quantity, and status details"
    category = "ecommerce"

    def _define_fields(self) -> None:
        """Define the fields for e-commerce orders."""
        # Order ID
        self.add_field(TemplateField(
            name="order_id",
            data_type="string",
            description="Unique order identifier",
            unique=True,
            nullable=False,
            constraints={"min_length": 10, "max_length": 15},
        ))

        # Customer ID
        self.add_field(TemplateField(
            name="customer_id",
            data_type="string",
            description="Customer identifier",
            nullable=False,
            constraints={"min_length": 8, "max_length": 12},
        ))

        # Product ID
        self.add_field(TemplateField(
            name="product_id",
            data_type="string",
            description="Product identifier",
            nullable=False,
            constraints={"min_length": 6, "max_length": 10},
        ))

        # Product Name
        self.add_field(TemplateField(
            name="product_name",
            data_type="string",
            description="Name of the product",
            nullable=False,
            constraints={"min_length": 5, "max_length": 100},
        ))

        # Quantity
        self.add_field(TemplateField(
            name="quantity",
            data_type="integer",
            description="Number of items",
            nullable=False,
            constraints={"range": (1, 100)},
        ))

        # Unit Price
        self.add_field(TemplateField(
            name="unit_price",
            data_type="float",
            description="Price per unit",
            nullable=False,
            constraints={"range": (1.0, 5000.0)},
        ))

        # Total Price
        self.add_field(TemplateField(
            name="total_price",
            data_type="float",
            description="Total order price",
            nullable=False,
            constraints={"range": (1.0, 10000.0)},
        ))

        # Order Date
        self.add_field(TemplateField(
            name="order_date",
            data_type="datetime",
            description="When the order was placed",
            nullable=False,
        ))

        # Status
        self.add_field(TemplateField(
            name="status",
            data_type="categorical",
            description="Order status",
            nullable=False,
            constraints={
                "values": [
                    "pending",
                    "confirmed",
                    "processing",
                    "shipped",
                    "delivered",
                    "cancelled",
                    "refunded",
                ]
            },
        ))

        # Shipping Address
        self.add_field(TemplateField(
            name="shipping_address",
            data_type="string",
            description="Delivery address",
            nullable=True,
            constraints={"min_length": 10, "max_length": 200},
        ))
