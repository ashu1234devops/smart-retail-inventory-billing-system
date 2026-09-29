from django.contrib import admin

from .models import (
    Vendor,
    Purchase,
    Sale,
    Inventory,
    ProfitLoss,
)


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = (
        'vendor_name',
        'vendor_email',
        'vendor_phone',
        'payment_terms',
        'vendor_gst',
    )

    search_fields = (
        'vendor_name',
        'vendor_email',
        'vendor_phone',
        'vendor_gst',
    )


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = (
        'purchase_invoice_number',
        'purchase_invoice_date',
        'vendor_name',
        'product_name',
        'qty',
        'rate',
        'gross_amount',
    )

    search_fields = (
        'purchase_invoice_number',
        'vendor_name',
        'product_name',
    )

    list_filter = (
        'purchase_invoice_date',
    )


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = (
        'sales_invoice_number',
        'sales_invoice_date',
        'customer_name',
        'product',
        'sales_qty',
        'sales_rate',
        'gross_amount',
    )

    search_fields = (
        'sales_invoice_number',
        'customer_name',
        'customer_number',
        'product',
    )

    list_filter = (
        'sales_invoice_date',
        'payment_type',
    )


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = (
        'product_name',
        'product_company',
        'opening_stock',
        'inward_stock',
        'outward_stock',
        'closing_stock',
    )

    search_fields = (
        'product_name',
        'product_company',
    )


@admin.register(ProfitLoss)
class ProfitLossAdmin(admin.ModelAdmin):
    list_display = (
        'date',
        'purchase_amount',
        'sales_amount',
        'profit',
        'loss',
    )

    list_filter = (
        'date',
    )