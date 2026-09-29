from django.db import models
from decimal import Decimal
from datetime import timedelta


# =========================================================
# 1. VENDOR TABLE
# =========================================================

class Vendor(models.Model):

    vendor_name = models.CharField(
        max_length=150
    )

    vendor_email = models.EmailField(
        blank=True,
        null=True
    )

    vendor_phone = models.CharField(
        max_length=20
    )

    vendor_address = models.TextField(
        blank=True,
        null=True
    )

    payment_terms = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    vendor_gst = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.vendor_name


# =========================================================
# 2. PURCHASE TABLE
# =========================================================

class Purchase(models.Model):

    purchase_invoice_date = models.DateField()

    purchase_invoice_number = models.CharField(
        max_length=50,
        unique=True
    )

    vendor_name = models.CharField(
        max_length=150
    )

    product_name = models.CharField(
        max_length=150
    )

    product_company = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    payment_term = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    qty = models.PositiveIntegerField()

    rate = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    # -----------------------------------------------------
    # AUTOMATICALLY CALCULATED FIELDS
    # -----------------------------------------------------

    net_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    gst_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00")
    )

    gst_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    gross_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # =====================================================
    # AUTOMATIC PURCHASE CALCULATIONS
    # =====================================================

    def save(self, *args, **kwargs):

        # Net Amount = Quantity × Rate
        self.net_amount = (
            Decimal(self.qty or 0)
            * Decimal(self.rate or 0)
        )

        # GST Amount = Net Amount × GST % ÷ 100
        self.gst_amount = (
            self.net_amount
            * Decimal(self.gst_percent or 0)
            / Decimal("100")
        )

        # Gross Amount = Net Amount + GST Amount
        self.gross_amount = (
            self.net_amount
            + self.gst_amount
        )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.purchase_invoice_number


# =========================================================
# 3. SALES TABLE
# =========================================================

class Sale(models.Model):

    sales_invoice_date = models.DateField()

    sales_invoice_number = models.CharField(
        max_length=50,
        unique=True
    )

    customer_name = models.CharField(
        max_length=150
    )

    customer_number = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    payment_type = models.CharField(
        max_length=50
    )

    product_company = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    product = models.CharField(
        max_length=150
    )

    sales_qty = models.PositiveIntegerField()

    sales_rate = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    # -----------------------------------------------------
    # AUTOMATICALLY CALCULATED SALES FIELDS
    # -----------------------------------------------------

    sales_net_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    gst_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00")
    )

    sales_gst_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    gross_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    # -----------------------------------------------------
    # WARRANTY
    # -----------------------------------------------------

    warranty_days = models.PositiveIntegerField(
        default=0
    )

    warranty_expiry = models.DateField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # =====================================================
    # AUTOMATIC SALES CALCULATIONS
    # =====================================================

    def save(self, *args, **kwargs):

        # -------------------------------------------------
        # SALES NET AMOUNT
        # -------------------------------------------------

        # Sales Net Amount = Sales Quantity × Sales Rate

        self.sales_net_amount = (
            Decimal(self.sales_qty or 0)
            * Decimal(self.sales_rate or 0)
        )

        # -------------------------------------------------
        # SALES GST AMOUNT
        # -------------------------------------------------

        # GST Amount = Net Amount × GST % ÷ 100

        self.sales_gst_amount = (
            self.sales_net_amount
            * Decimal(self.gst_percent or 0)
            / Decimal("100")
        )

        # -------------------------------------------------
        # GROSS AMOUNT
        # -------------------------------------------------

        # Gross Amount = Net Amount + GST Amount

        self.gross_amount = (
            self.sales_net_amount
            + self.sales_gst_amount
        )

        # -------------------------------------------------
        # WARRANTY EXPIRY
        # -------------------------------------------------

        # Warranty Expiry = Sales Date + Warranty Days

        if self.sales_invoice_date:

            self.warranty_expiry = (
                self.sales_invoice_date
                + timedelta(
                    days=int(self.warranty_days or 0)
                )
            )

        else:

            self.warranty_expiry = None

        # -------------------------------------------------
        # SAVE
        # -------------------------------------------------

        super().save(*args, **kwargs)

    def __str__(self):
        return self.sales_invoice_number


# =========================================================
# 4. INVENTORY TABLE
# =========================================================

class Inventory(models.Model):

    product_name = models.CharField(
        max_length=150,
        unique=True
    )

    product_company = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    # -----------------------------------------------------
    # STOCK
    # -----------------------------------------------------

    opening_stock = models.IntegerField(
        default=0
    )

    inward_stock = models.IntegerField(
        default=0
    )

    outward_stock = models.IntegerField(
        default=0
    )

    closing_stock = models.IntegerField(
        default=0
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.product_name


# =========================================================
# 5. PROFIT & LOSS TABLE
# =========================================================

class ProfitLoss(models.Model):

    date = models.DateField(
        unique=True
    )

    purchase_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00")
    )

    sales_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00")
    )

    profit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00")
    )

    loss = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00")
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return str(self.date)