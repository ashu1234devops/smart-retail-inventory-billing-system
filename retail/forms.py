from django import forms
from django.db.models import Sum

from .models import (
    Vendor,
    Purchase,
    Sale,
    Inventory,
)


# =========================================================
# 1. VENDOR FORM
# =========================================================

class VendorForm(forms.ModelForm):

    class Meta:
        model = Vendor

        fields = [
            "vendor_name",
            "vendor_email",
            "vendor_phone",
            "vendor_address",
            "payment_terms",
            "vendor_gst",
        ]

        widgets = {

            "vendor_name": forms.TextInput(
                attrs={
                    "placeholder": "Enter vendor name"
                }
            ),

            "vendor_email": forms.EmailInput(
                attrs={
                    "placeholder": "Enter vendor email"
                }
            ),

            "vendor_phone": forms.TextInput(
                attrs={
                    "placeholder": "Enter vendor phone number"
                }
            ),

            "vendor_address": forms.Textarea(
                attrs={
                    "placeholder": "Enter vendor address",
                    "rows": 3
                }
            ),

            "payment_terms": forms.TextInput(
                attrs={
                    "placeholder": "Enter payment terms"
                }
            ),

            "vendor_gst": forms.TextInput(
                attrs={
                    "placeholder": "Enter GST number"
                }
            ),
        }


# =========================================================
# 2. PURCHASE FORM
# =========================================================

class PurchaseForm(forms.ModelForm):

    class Meta:
        model = Purchase

        fields = [
            "purchase_invoice_date",
            "purchase_invoice_number",
            "vendor_name",
            "product_name",
            "product_company",
            "payment_term",
            "qty",
            "rate",
            "gst_percent",
        ]

        widgets = {

            "purchase_invoice_date": forms.DateInput(
                attrs={
                    "type": "date"
                }
            ),

            "purchase_invoice_number": forms.TextInput(
                attrs={
                    "placeholder": "Enter purchase invoice number"
                }
            ),

            "vendor_name": forms.TextInput(
                attrs={
                    "placeholder": "Enter vendor name"
                }
            ),

            "product_name": forms.TextInput(
                attrs={
                    "placeholder": "Enter product name"
                }
            ),

            "product_company": forms.TextInput(
                attrs={
                    "placeholder": "Enter company name"
                }
            ),

            "payment_term": forms.TextInput(
                attrs={
                    "placeholder": "Cash / Credit / UPI"
                }
            ),

            "qty": forms.NumberInput(
                attrs={
                    "placeholder": "Enter quantity",
                    "min": "1"
                }
            ),

            "rate": forms.NumberInput(
                attrs={
                    "placeholder": "Enter purchase rate",
                    "step": "0.01",
                    "min": "0"
                }
            ),

            "gst_percent": forms.NumberInput(
                attrs={
                    "placeholder": "GST %",
                    "step": "0.01",
                    "min": "0"
                }
            ),
        }


# =========================================================
# 3. SALE FORM
# =========================================================

class SaleForm(forms.ModelForm):

    class Meta:
        model = Sale

        fields = [
            "sales_invoice_date",
            "sales_invoice_number",
            "customer_name",
            "customer_number",
            "payment_type",
            "product_company",
            "product",
            "sales_qty",
            "sales_rate",
            "gst_percent",
            "warranty_days",
        ]

        widgets = {

            "sales_invoice_date": forms.DateInput(
                attrs={
                    "type": "date"
                }
            ),

            "sales_invoice_number": forms.TextInput(
                attrs={
                    "placeholder": "Enter sales invoice number"
                }
            ),

            "customer_name": forms.TextInput(
                attrs={
                    "placeholder": "Enter customer name"
                }
            ),

            "customer_number": forms.TextInput(
                attrs={
                    "placeholder": "Enter customer number"
                }
            ),

            "payment_type": forms.TextInput(
                attrs={
                    "placeholder": "Cash / UPI / Card"
                }
            ),

            "product_company": forms.TextInput(
                attrs={
                    "placeholder": "Enter company name"
                }
            ),

            "product": forms.TextInput(
                attrs={
                    "placeholder": "Enter product name"
                }
            ),

            "sales_qty": forms.NumberInput(
                attrs={
                    "placeholder": "Enter sales quantity",
                    "min": "1"
                }
            ),

            "sales_rate": forms.NumberInput(
                attrs={
                    "placeholder": "Enter sales rate",
                    "step": "0.01",
                    "min": "0"
                }
            ),

            "gst_percent": forms.NumberInput(
                attrs={
                    "placeholder": "GST %",
                    "step": "0.01",
                    "min": "0"
                }
            ),

            "warranty_days": forms.NumberInput(
                attrs={
                    "placeholder": "Warranty days",
                    "min": "0"
                }
            ),
        }

    # =====================================================
    # STOCK VALIDATION
    # =====================================================

    def clean(self):

        cleaned_data = super().clean()

        product = cleaned_data.get("product")
        sales_qty = cleaned_data.get("sales_qty")

        if not product or not sales_qty:
            return cleaned_data

        # -------------------------------------------------
        # FIND INVENTORY
        # -------------------------------------------------

        inventory = Inventory.objects.filter(
            product_name=product
        ).first()

        # -------------------------------------------------
        # CALCULATE AVAILABLE STOCK
        # -------------------------------------------------

        if inventory:

            opening_stock = inventory.opening_stock

        else:

            opening_stock = 0

        purchase_total = (
            Purchase.objects
            .filter(
                product_name=product
            )
            .aggregate(
                total=Sum("qty")
            )["total"] or 0
        )

        sales_total = (
            Sale.objects
            .filter(
                product=product
            )
            .aggregate(
                total=Sum("sales_qty")
            )["total"] or 0
        )

        # -------------------------------------------------
        # EDIT SALE
        #
        # If we are editing an existing sale, add its old
        # quantity back because it is already included in
        # sales_total.
        # -------------------------------------------------

        if self.instance and self.instance.pk:

            old_product = self.instance.product

            if old_product == product:

                sales_total -= self.instance.sales_qty or 0

        # -------------------------------------------------
        # AVAILABLE STOCK
        # -------------------------------------------------

        available_stock = (
            opening_stock
            + purchase_total
            - sales_total
        )

        # -------------------------------------------------
        # CHECK STOCK
        # -------------------------------------------------

        if sales_qty > available_stock:

            raise forms.ValidationError(
                f"Insufficient stock. "
                f"Available stock for {product}: "
                f"{available_stock}"
            )

        return cleaned_data


# =========================================================
# 4. INVENTORY FORM
# =========================================================

class InventoryForm(forms.ModelForm):

    class Meta:
        model = Inventory

        fields = [
            "product_name",
            "product_company",
            "opening_stock",
        ]

        widgets = {

            "product_name": forms.TextInput(
                attrs={
                    "placeholder": "Enter product name"
                }
            ),

            "product_company": forms.TextInput(
                attrs={
                    "placeholder": "Enter company name"
                }
            ),

            "opening_stock": forms.NumberInput(
                attrs={
                    "placeholder": "Enter opening stock",
                    "min": "0"
                }
            ),
        }