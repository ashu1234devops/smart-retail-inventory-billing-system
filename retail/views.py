from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.db.models.functions import TruncMonth
from django.http import HttpResponse

import json

from reportlab.pdfgen import canvas

from .models import (
    Vendor,
    Purchase,
    Sale,
    Inventory,
    ProfitLoss,
)

from .forms import (
    VendorForm,
    PurchaseForm,
    SaleForm,
    InventoryForm,
)


# =========================================================
# INVENTORY CALCULATION
# =========================================================

def update_inventory(product_name, product_company=None):
    """
    Automatically updates inventory for a product.

    Closing Stock =
    Opening Stock + Inward Stock - Outward Stock
    """

    if not product_name:
        return None

    inventory, created = Inventory.objects.get_or_create(
        product_name=product_name,
        defaults={
            "product_company": product_company or ""
        }
    )

    if product_company:
        inventory.product_company = product_company

    # -----------------------------------------------------
    # TOTAL PURCHASE QUANTITY
    # -----------------------------------------------------

    purchase_total = (
        Purchase.objects
        .filter(product_name=product_name)
        .aggregate(
            total=Sum("qty")
        )["total"]
        or 0
    )

    # -----------------------------------------------------
    # TOTAL SALES QUANTITY
    # -----------------------------------------------------

    sales_total = (
        Sale.objects
        .filter(product=product_name)
        .aggregate(
            total=Sum("sales_qty")
        )["total"]
        or 0
    )

    # -----------------------------------------------------
    # UPDATE STOCK
    # -----------------------------------------------------

    inventory.inward_stock = purchase_total

    inventory.outward_stock = sales_total

    inventory.closing_stock = (
        inventory.opening_stock
        + inventory.inward_stock
        - inventory.outward_stock
    )

    inventory.save()

    return inventory


# =========================================================
# AVAILABLE STOCK
# =========================================================

def get_available_stock(product_name, exclude_sale=None):
    """
    Calculates available stock before a sale.

    Available Stock =
    Opening Stock + Purchases - Sales

    When editing an existing sale,
    the existing sale is excluded.
    """

    if not product_name:
        return 0

    # -----------------------------------------------------
    # GET INVENTORY
    # -----------------------------------------------------

    inventory = (
        Inventory.objects
        .filter(product_name=product_name)
        .first()
    )

    if inventory:
        opening_stock = inventory.opening_stock
    else:
        opening_stock = 0

    # -----------------------------------------------------
    # PURCHASE STOCK
    # -----------------------------------------------------

    purchase_total = (
        Purchase.objects
        .filter(product_name=product_name)
        .aggregate(
            total=Sum("qty")
        )["total"]
        or 0
    )

    # -----------------------------------------------------
    # SALES STOCK
    # -----------------------------------------------------

    sales_queryset = Sale.objects.filter(
        product=product_name
    )

    if exclude_sale is not None and exclude_sale.pk:
        sales_queryset = sales_queryset.exclude(
            pk=exclude_sale.pk
        )

    sales_total = (
        sales_queryset
        .aggregate(
            total=Sum("sales_qty")
        )["total"]
        or 0
    )

    # -----------------------------------------------------
    # AVAILABLE STOCK
    # -----------------------------------------------------

    available_stock = (
        opening_stock
        + purchase_total
        - sales_total
    )

    return available_stock


# =========================================================
# VENDOR LIST + SEARCH
# =========================================================

@login_required
def vendor_list(request):

    search = request.GET.get(
        "search",
        ""
    ).strip()

    vendors = Vendor.objects.all()

    if search:
        vendors = vendors.filter(
            Q(vendor_name__icontains=search)
            |
            Q(vendor_email__icontains=search)
            |
            Q(vendor_phone__icontains=search)
            |
            Q(vendor_address__icontains=search)
            |
            Q(payment_terms__icontains=search)
            |
            Q(vendor_gst__icontains=search)
        )

    vendors = vendors.order_by(
        "-created_at"
    )

    return render(
        request,
        "retail/vendors/vendor_list.html",
        {
            "vendors": vendors,
            "search": search,
        }
    )


# =========================================================
# ADD VENDOR
# =========================================================

@login_required
def vendor_add(request):

    if request.method == "POST":

        form = VendorForm(
            request.POST
        )

        if form.is_valid():

            form.save()

            return redirect(
                "vendor_list"
            )

    else:

        form = VendorForm()

    return render(
        request,
        "retail/vendors/vendor_form.html",
        {
            "form": form
        }
    )


# =========================================================
# EDIT VENDOR
# =========================================================

@login_required
def vendor_edit(request, pk):

    vendor = get_object_or_404(
        Vendor,
        pk=pk
    )

    if request.method == "POST":

        form = VendorForm(
            request.POST,
            instance=vendor
        )

        if form.is_valid():

            form.save()

            return redirect(
                "vendor_list"
            )

    else:

        form = VendorForm(
            instance=vendor
        )

    return render(
        request,
        "retail/vendors/vendor_form.html",
        {
            "form": form,
            "vendor": vendor
        }
    )


# =========================================================
# DELETE VENDOR
# =========================================================

@login_required
def vendor_delete(request, pk):

    vendor = get_object_or_404(
        Vendor,
        pk=pk
    )

    if request.method == "POST":

        vendor.delete()

        return redirect(
            "vendor_list"
        )

    return render(
        request,
        "retail/vendors/vendor_confirm_delete.html",
        {
            "vendor": vendor
        }
    )


# =========================================================
# PURCHASE LIST + SEARCH
# =========================================================

@login_required
def purchase_list(request):

    search = request.GET.get(
        "search",
        ""
    ).strip()

    purchases = (
        Purchase.objects
        .all()
        .order_by(
            "-purchase_invoice_date"
        )
    )

    if search:

        purchases = purchases.filter(

            Q(product_name__icontains=search)
            |
            Q(product_company__icontains=search)
            |
            Q(vendor_name__icontains=search)
            |
            Q(
                purchase_invoice_number__icontains=search
            )

        )

    return render(
        request,
        "retail/purchases/purchase_list.html",
        {
            "purchases": purchases,
            "search": search,
        }
    )


# =========================================================
# ADD PURCHASE
# =========================================================

@login_required
def purchase_add(request):

    if request.method == "POST":

        form = PurchaseForm(
            request.POST
        )

        if form.is_valid():

            purchase = form.save()

            update_inventory(
                purchase.product_name,
                purchase.product_company
            )

            return redirect(
                "purchase_list"
            )

    else:

        form = PurchaseForm()

    return render(
        request,
        "retail/purchases/purchase_form.html",
        {
            "form": form
        }
    )


# =========================================================
# EDIT PURCHASE
# =========================================================

@login_required
def purchase_edit(request, pk):

    purchase = get_object_or_404(
        Purchase,
        pk=pk
    )

    old_product_name = purchase.product_name

    if request.method == "POST":

        form = PurchaseForm(
            request.POST,
            instance=purchase
        )

        if form.is_valid():

            purchase = form.save()

            # Update old product
            update_inventory(
                old_product_name
            )

            # Update new product
            update_inventory(
                purchase.product_name,
                purchase.product_company
            )

            return redirect(
                "purchase_list"
            )

    else:

        form = PurchaseForm(
            instance=purchase
        )

    return render(
        request,
        "retail/purchases/purchase_form.html",
        {
            "form": form,
            "purchase": purchase
        }
    )


# =========================================================
# DELETE PURCHASE
# =========================================================

@login_required
def purchase_delete(request, pk):

    purchase = get_object_or_404(
        Purchase,
        pk=pk
    )

    product_name = purchase.product_name

    if request.method == "POST":

        purchase.delete()

        update_inventory(
            product_name
        )

        return redirect(
            "purchase_list"
        )

    return render(
        request,
        "retail/purchases/purchase_confirm_delete.html",
        {
            "purchase": purchase
        }
    )


# =========================================================
# SALES LIST + SEARCH
# =========================================================

@login_required
def sale_list(request):

    search = request.GET.get(
        "search",
        ""
    ).strip()

    sales = (
        Sale.objects
        .all()
        .order_by(
            "-sales_invoice_date"
        )
    )

    if search:

        sales = sales.filter(

            Q(product__icontains=search)
            |
            Q(product_company__icontains=search)
            |
            Q(customer_name__icontains=search)
            |
            Q(
                sales_invoice_number__icontains=search
            )

        )

    return render(
        request,
        "retail/sales/sale_list.html",
        {
            "sales": sales,
            "search": search,
        }
    )


# =========================================================
# ADD SALE
# =========================================================

@login_required
def sale_add(request):

    if request.method == "POST":

        form = SaleForm(
            request.POST
        )

        if form.is_valid():

            product_name = form.cleaned_data[
                "product"
            ]

            sales_qty = form.cleaned_data[
                "sales_qty"
            ]

            # Check available stock
            available_stock = get_available_stock(
                product_name
            )

            if sales_qty > available_stock:

                form.add_error(
                    "sales_qty",
                    (
                        "Insufficient stock. "
                        f"Available stock: {available_stock}"
                    )
                )

            else:

                sale = form.save()

                update_inventory(
                    sale.product,
                    sale.product_company
                )

                return redirect(
                    "sale_list"
                )

    else:

        form = SaleForm()

    return render(
        request,
        "retail/sales/sale_form.html",
        {
            "form": form
        }
    )


# =========================================================
# EDIT SALE
# =========================================================

@login_required
def sale_edit(request, pk):

    sale = get_object_or_404(
        Sale,
        pk=pk
    )

    old_product = sale.product

    if request.method == "POST":

        form = SaleForm(
            request.POST,
            instance=sale
        )

        if form.is_valid():

            new_product = form.cleaned_data[
                "product"
            ]

            new_quantity = form.cleaned_data[
                "sales_qty"
            ]

            available_stock = get_available_stock(
                new_product,
                exclude_sale=sale
            )

            if new_quantity > available_stock:

                form.add_error(
                    "sales_qty",
                    (
                        "Insufficient stock. "
                        f"Available stock: {available_stock}"
                    )
                )

            else:

                sale = form.save()

                # Update old product
                update_inventory(
                    old_product
                )

                # Update new product
                update_inventory(
                    sale.product,
                    sale.product_company
                )

                return redirect(
                    "sale_list"
                )

    else:

        form = SaleForm(
            instance=sale
        )

    return render(
        request,
        "retail/sales/sale_form.html",
        {
            "form": form,
            "sale": sale
        }
    )


# =========================================================
# DELETE SALE
# =========================================================

@login_required
def sale_delete(request, pk):

    sale = get_object_or_404(
        Sale,
        pk=pk
    )

    product_name = sale.product

    if request.method == "POST":

        sale.delete()

        update_inventory(
            product_name
        )

        return redirect(
            "sale_list"
        )

    return render(
        request,
        "retail/sales/sale_confirm_delete.html",
        {
            "sale": sale
        }
    )


# =========================================================
# INVENTORY LIST
# =========================================================

@login_required
def inventory_list(request):

    inventories = (
        Inventory.objects
        .all()
        .order_by(
            "product_name"
        )
    )

    # Update every product
    for inventory in inventories:

        update_inventory(
            inventory.product_name,
            inventory.product_company
        )

    # Get updated inventory
    inventories = (
        Inventory.objects
        .all()
        .order_by(
            "product_name"
        )
    )

    # -----------------------------------------------------
    # TOTAL OPENING STOCK
    # -----------------------------------------------------

    total_opening_stock = sum(
        inventory.opening_stock
        for inventory in inventories
    )

    # -----------------------------------------------------
    # TOTAL INWARD STOCK
    # -----------------------------------------------------

    total_inward_stock = sum(
        inventory.inward_stock
        for inventory in inventories
    )

    # -----------------------------------------------------
    # TOTAL OUTWARD STOCK
    # -----------------------------------------------------

    total_outward_stock = sum(
        inventory.outward_stock
        for inventory in inventories
    )

    # -----------------------------------------------------
    # TOTAL CLOSING STOCK
    # -----------------------------------------------------

    total_closing_stock = sum(
        inventory.closing_stock
        for inventory in inventories
    )

    context = {

        "inventories":
            inventories,

        "total_opening_stock":
            total_opening_stock,

        "total_inward_stock":
            total_inward_stock,

        "total_outward_stock":
            total_outward_stock,

        "total_closing_stock":
            total_closing_stock,

    }

    return render(
        request,
        "retail/inventory/inventory_list.html",
        context
    )


# =========================================================
# ADD INVENTORY PRODUCT
# =========================================================

@login_required
def inventory_add(request):

    if request.method == "POST":

        form = InventoryForm(
            request.POST
        )

        if form.is_valid():

            inventory = form.save()

            update_inventory(
                inventory.product_name,
                inventory.product_company
            )

            return redirect(
                "inventory_list"
            )

    else:

        form = InventoryForm()

    return render(
        request,
        "retail/inventory/inventory_form.html",
        {
            "form": form
        }
    )


# =========================================================
# INVENTORY DETAIL
# =========================================================

@login_required
def inventory_detail(request, pk):

    inventory = get_object_or_404(
        Inventory,
        pk=pk
    )

    update_inventory(
        inventory.product_name,
        inventory.product_company
    )

    inventory.refresh_from_db()

    return render(
        request,
        "retail/inventory/inventory_detail.html",
        {
            "inventory": inventory
        }
    )


# =========================================================
# PROFIT & LOSS
# =========================================================

@login_required
def profit_loss_list(request):

    from_date = request.GET.get(
        "from_date",
        ""
    ).strip()

    to_date = request.GET.get(
        "to_date",
        ""
    ).strip()

    # =====================================================
    # PURCHASE DATA BY DATE
    # =====================================================

    purchase_data = (
        Purchase.objects
        .values(
            "purchase_invoice_date"
        )
        .annotate(
            total=Sum("net_amount")
        )
    )

    purchase_dict = {

        item["purchase_invoice_date"]:
            item["total"] or 0

        for item in purchase_data

    }

    # =====================================================
    # SALES DATA BY DATE
    # =====================================================

    sales_data = (
        Sale.objects
        .values(
            "sales_invoice_date"
        )
        .annotate(
            total=Sum("sales_net_amount")
        )
    )

    sales_dict = {

        item["sales_invoice_date"]:
            item["total"] or 0

        for item in sales_data

    }

    # =====================================================
    # COMBINE ALL DATES
    # =====================================================

    dates = (
        set(purchase_dict.keys())
        |
        set(sales_dict.keys())
    )

    # =====================================================
    # CREATE / UPDATE P&L RECORDS
    # =====================================================

    for date in dates:

        purchase_amount = purchase_dict.get(
            date,
            0
        )

        sales_amount = sales_dict.get(
            date,
            0
        )

        difference = (
            sales_amount
            - purchase_amount
        )

        if difference > 0:

            profit = difference
            loss = 0

        elif difference < 0:

            profit = 0
            loss = abs(difference)

        else:

            profit = 0
            loss = 0

        ProfitLoss.objects.update_or_create(

            date=date,

            defaults={

                "purchase_amount":
                    purchase_amount,

                "sales_amount":
                    sales_amount,

                "profit":
                    profit,

                "loss":
                    loss,

            }

        )

    # =====================================================
    # GET P&L RECORDS
    # =====================================================

    profit_losses = (
        ProfitLoss.objects
        .all()
        .order_by(
            "-date"
        )
    )

    # =====================================================
    # DATE FILTER - FROM
    # =====================================================

    if from_date:

        profit_losses = profit_losses.filter(
            date__gte=from_date
        )

    # =====================================================
    # DATE FILTER - TO
    # =====================================================

    if to_date:

        profit_losses = profit_losses.filter(
            date__lte=to_date
        )

    # =====================================================
    # TOTAL PURCHASE
    # =====================================================

    total_purchase = (
        profit_losses
        .aggregate(
            total=Sum("purchase_amount")
        )["total"]
        or 0
    )

    # =====================================================
    # TOTAL SALES
    # =====================================================

    total_sales = (
        profit_losses
        .aggregate(
            total=Sum("sales_amount")
        )["total"]
        or 0
    )

    # =====================================================
    # TOTAL PROFIT
    # =====================================================

    total_profit = (
        profit_losses
        .aggregate(
            total=Sum("profit")
        )["total"]
        or 0
    )

    # =====================================================
    # TOTAL LOSS
    # =====================================================

    total_loss = (
        profit_losses
        .aggregate(
            total=Sum("loss")
        )["total"]
        or 0
    )

    # =====================================================
    # NET RESULT
    # =====================================================

    net_result = (
        total_profit
        - total_loss
    )

    # =====================================================
    # CONTEXT
    # =====================================================

    context = {

        "profit_losses":
            profit_losses,

        "total_purchase":
            total_purchase,

        "total_sales":
            total_sales,

        "total_profit":
            total_profit,

        "total_loss":
            total_loss,

        "net_result":
            net_result,

        "from_date":
            from_date,

        "to_date":
            to_date,

    }

    return render(
        request,
        "retail/profit_loss/profit_loss_list.html",
        context
    )


# =========================================================
# DASHBOARD
# =========================================================

@login_required
def dashboard(request):

    # =====================================================
    # BASIC COUNTS
    # =====================================================

    total_vendors = Vendor.objects.count()

    total_purchases = Purchase.objects.count()

    total_sales = Sale.objects.count()

    total_products = Inventory.objects.count()

    # =====================================================
    # TOTAL PURCHASE AMOUNT
    # =====================================================

    total_purchase_amount = (
        Purchase.objects
        .aggregate(
            total=Sum("net_amount")
        )["total"]
        or 0
    )

    # =====================================================
    # TOTAL SALES AMOUNT
    # =====================================================

    total_sales_amount = (
        Sale.objects
        .aggregate(
            total=Sum("sales_net_amount")
        )["total"]
        or 0
    )

    # =====================================================
    # UPDATE INVENTORY
    # =====================================================

    inventories = (
        Inventory.objects
        .all()
    )

    for inventory in inventories:

        update_inventory(
            inventory.product_name,
            inventory.product_company
        )

    # =====================================================
    # GET UPDATED INVENTORY
    # =====================================================

    inventories = (
        Inventory.objects
        .all()
        .order_by(
            "product_name"
        )
    )

    # =====================================================
    # TOTAL STOCK UNITS
    # =====================================================

    total_stock_units = sum(
        inventory.closing_stock
        for inventory in inventories
    )

    # =====================================================
    # LOW STOCK COUNT
    # =====================================================

    low_stock_count = sum(
        1
        for inventory in inventories
        if inventory.closing_stock <= 5
    )

    # =====================================================
    # NEGATIVE STOCK COUNT
    # =====================================================

    negative_stock_count = sum(
        1
        for inventory in inventories
        if inventory.closing_stock < 0
    )

    # =====================================================
    # MONTHLY PURCHASES
    # =====================================================

    purchase_monthly = (
        Purchase.objects
        .annotate(
            month=TruncMonth(
                "purchase_invoice_date"
            )
        )
        .values(
            "month"
        )
        .annotate(
            total=Sum("net_amount")
        )
        .order_by(
            "month"
        )
    )

    # =====================================================
    # MONTHLY SALES
    # =====================================================

    sales_monthly = (
        Sale.objects
        .annotate(
            month=TruncMonth(
                "sales_invoice_date"
            )
        )
        .values(
            "month"
        )
        .annotate(
            total=Sum("sales_net_amount")
        )
        .order_by(
            "month"
        )
    )

    # =====================================================
    # COMBINE MONTHLY DATA
    # =====================================================

    monthly_data = {}

    # -----------------------------------------------------
    # PURCHASE MONTHS
    # -----------------------------------------------------

    for item in purchase_monthly:

        month = item["month"]

        if month:

            month_key = month.strftime(
                "%b %Y"
            )

            if month_key not in monthly_data:

                monthly_data[month_key] = {
                    "purchase": 0,
                    "sales": 0,
                }

            monthly_data[
                month_key
            ]["purchase"] = float(
                item["total"] or 0
            )

    # -----------------------------------------------------
    # SALES MONTHS
    # -----------------------------------------------------

    for item in sales_monthly:

        month = item["month"]

        if month:

            month_key = month.strftime(
                "%b %Y"
            )

            if month_key not in monthly_data:

                monthly_data[month_key] = {
                    "purchase": 0,
                    "sales": 0,
                }

            monthly_data[
                month_key
            ]["sales"] = float(
                item["total"] or 0
            )

    # =====================================================
    # MONTH ORDER
    # =====================================================

    month_order = [

        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",

    ]

    # =====================================================
    # SORT MONTHS
    # =====================================================

    sorted_months = sorted(

        monthly_data.keys(),

        key=lambda x: (

            int(
                x.split()[1]
            ),

            month_order.index(
                x.split()[0]
            )

        )

    )

    # =====================================================
    # CHART LABELS
    # =====================================================

    month_labels = sorted_months

    # =====================================================
    # PURCHASE CHART VALUES
    # =====================================================

    purchase_values = [

        monthly_data[
            month
        ]["purchase"]

        for month in sorted_months

    ]

    # =====================================================
    # SALES CHART VALUES
    # =====================================================

    sales_values = [

        monthly_data[
            month
        ]["sales"]

        for month in sorted_months

    ]

    # =====================================================
    # STOCK CHART LABELS
    # =====================================================

    stock_labels = [

        inventory.product_name

        for inventory in inventories

    ]

    # =====================================================
    # STOCK CHART VALUES
    # =====================================================

    stock_values = [

        inventory.closing_stock

        for inventory in inventories

    ]

    # =====================================================
    # DASHBOARD CONTEXT
    # =====================================================

    context = {

        "total_vendors":
            total_vendors,

        "total_purchases":
            total_purchases,

        "total_sales":
            total_sales,

        "total_products":
            total_products,

        "total_purchase_amount":
            total_purchase_amount,

        "total_sales_amount":
            total_sales_amount,

        "total_stock_units":
            total_stock_units,

        "low_stock_count":
            low_stock_count,

        "negative_stock_count":
            negative_stock_count,

        "month_labels":
            json.dumps(
                month_labels
            ),

        "purchase_values":
            json.dumps(
                purchase_values
            ),

        "sales_values":
            json.dumps(
                sales_values
            ),

        "stock_labels":
            json.dumps(
                stock_labels
            ),

        "stock_values":
            json.dumps(
                stock_values
            ),

    }

    return render(
        request,
        "retail/dashboard.html",
        context
    )


# =========================================================
# SALES INVOICE PDF
# =========================================================

@login_required
def sale_invoice_pdf(request, pk):

    sale = get_object_or_404(
        Sale,
        pk=pk
    )

    # =====================================================
    # PDF RESPONSE
    # =====================================================

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'inline; '
        f'filename="Invoice_{sale.sales_invoice_number}.pdf"'
    )

    # =====================================================
    # CREATE PDF
    # =====================================================

    pdf = canvas.Canvas(
        response
    )

    width = 595
    height = 842

    # =====================================================
    # HEADER
    # =====================================================

    pdf.setFillColorRGB(
        0.12,
        0.16,
        0.22
    )

    pdf.rect(
        0,
        height - 100,
        width,
        100,
        fill=1,
        stroke=0
    )

    pdf.setFillColorRGB(
        1,
        1,
        1
    )

    pdf.setFont(
        "Helvetica-Bold",
        26
    )

    pdf.drawString(
        50,
        height - 50,
        "SMART RETAIL"
    )

    pdf.setFont(
        "Helvetica",
        11
    )

    pdf.drawString(
        50,
        height - 72,
        "Inventory, Billing & Profit Management System"
    )

    pdf.setFont(
        "Helvetica-Bold",
        18
    )

    pdf.drawRightString(
        width - 50,
        height - 55,
        "SALES INVOICE"
    )

    # =====================================================
    # INVOICE INFORMATION
    # =====================================================

    y = height - 140

    pdf.setFillColorRGB(
        0.1,
        0.1,
        0.1
    )

    pdf.setFont(
        "Helvetica-Bold",
        11
    )

    pdf.drawString(
        50,
        y,
        "Invoice Number:"
    )

    pdf.setFont(
        "Helvetica",
        11
    )

    pdf.drawString(
        155,
        y,
        str(
            sale.sales_invoice_number
        )
    )

    pdf.setFont(
        "Helvetica-Bold",
        11
    )

    pdf.drawString(
        350,
        y,
        "Invoice Date:"
    )

    pdf.setFont(
        "Helvetica",
        11
    )

    pdf.drawString(
        435,
        y,
        sale.sales_invoice_date.strftime(
            "%d %b %Y"
        )
    )

    # =====================================================
    # CUSTOMER
    # =====================================================

    y -= 45

    pdf.setFont(
        "Helvetica-Bold",
        13
    )

    pdf.drawString(
        50,
        y,
        "Bill To"
    )

    y -= 25

    pdf.setFont(
        "Helvetica-Bold",
        11
    )

    pdf.drawString(
        50,
        y,
        "Customer Name:"
    )

    pdf.setFont(
        "Helvetica",
        11
    )

    pdf.drawString(
        150,
        y,
        str(
            sale.customer_name
        )
    )

    y -= 20

    pdf.setFont(
        "Helvetica-Bold",
        11
    )

    pdf.drawString(
        50,
        y,
        "Customer Number:"
    )

    pdf.setFont(
        "Helvetica",
        11
    )

    pdf.drawString(
        150,
        y,
        str(
            sale.customer_number
            or "-"
        )
    )

    # =====================================================
    # PRODUCT TABLE HEADER
    # =====================================================

    y -= 50

    pdf.setFillColorRGB(
        0.12,
        0.16,
        0.22
    )

    pdf.rect(
        40,
        y - 25,
        515,
        30,
        fill=1,
        stroke=0
    )

    pdf.setFillColorRGB(
        1,
        1,
        1
    )

    pdf.setFont(
        "Helvetica-Bold",
        10
    )

    pdf.drawString(
        50,
        y - 15,
        "Product"
    )

    pdf.drawString(
        200,
        y - 15,
        "Company"
    )

    pdf.drawString(
        310,
        y - 15,
        "Qty"
    )

    pdf.drawString(
        365,
        y - 15,
        "Rate"
    )

    pdf.drawString(
        450,
        y - 15,
        "Amount"
    )

    # =====================================================
    # PRODUCT
    # =====================================================

    y -= 55

    pdf.setFillColorRGB(
        0.1,
        0.1,
        0.1
    )

    pdf.setFont(
        "Helvetica",
        10
    )

    pdf.drawString(
        50,
        y,
        str(
            sale.product
        )
    )

    pdf.drawString(
        200,
        y,
        str(
            sale.product_company
            or "-"
        )
    )

    pdf.drawString(
        310,
        y,
        str(
            sale.sales_qty
        )
    )

    pdf.drawString(
        365,
        y,
        f"Rs. {sale.sales_rate:.2f}"
    )

    pdf.drawString(
        450,
        y,
        f"Rs. {sale.sales_net_amount:.2f}"
    )

    # =====================================================
    # NET AMOUNT
    # =====================================================

    y -= 70

    pdf.setFont(
        "Helvetica-Bold",
        11
    )

    pdf.drawString(
        350,
        y,
        "Net Amount:"
    )

    pdf.setFont(
        "Helvetica",
        11
    )

    pdf.drawRightString(
        545,
        y,
        f"Rs. {sale.sales_net_amount:.2f}"
    )

    # =====================================================
    # GST
    # =====================================================

    y -= 25

    pdf.setFont(
        "Helvetica-Bold",
        11
    )

    pdf.drawString(
        350,
        y,
        f"GST ({sale.gst_percent:.2f}%):"
    )

    pdf.setFont(
        "Helvetica",
        11
    )

    pdf.drawRightString(
        545,
        y,
        f"Rs. {sale.sales_gst_amount:.2f}"
    )

    # =====================================================
    # GRAND TOTAL
    # =====================================================

    y -= 35

    pdf.setFillColorRGB(
        0.12,
        0.16,
        0.22
    )

    pdf.rect(
        330,
        y - 10,
        225,
        40,
        fill=1,
        stroke=0
    )

    pdf.setFillColorRGB(
        1,
        1,
        1
    )

    pdf.setFont(
        "Helvetica-Bold",
        13
    )

    pdf.drawString(
        345,
        y + 5,
        "GRAND TOTAL"
    )

    pdf.drawRightString(
        545,
        y + 5,
        f"Rs. {sale.gross_amount:.2f}"
    )

    # =====================================================
    # PAYMENT TYPE
    # =====================================================

    y -= 75

    pdf.setFillColorRGB(
        0.1,
        0.1,
        0.1
    )

    pdf.setFont(
        "Helvetica-Bold",
        11
    )

    pdf.drawString(
        50,
        y,
        "Payment Type:"
    )

    pdf.setFont(
        "Helvetica",
        11
    )

    pdf.drawString(
        145,
        y,
        str(
            sale.payment_type
        )
    )

    # =====================================================
    # WARRANTY
    # =====================================================

    y -= 25

    pdf.setFont(
        "Helvetica-Bold",
        11
    )

    pdf.drawString(
        50,
        y,
        "Warranty:"
    )

    pdf.setFont(
        "Helvetica",
        11
    )

    pdf.drawString(
        145,
        y,
        f"{sale.warranty_days} days"
    )

    # =====================================================
    # WARRANTY EXPIRY
    # =====================================================

    y -= 25

    pdf.setFont(
        "Helvetica-Bold",
        11
    )

    pdf.drawString(
        50,
        y,
        "Warranty Expiry:"
    )

    pdf.setFont(
        "Helvetica",
        11
    )

    if sale.warranty_expiry:

        pdf.drawString(
            145,
            y,
            sale.warranty_expiry.strftime(
                "%d %b %Y"
            )
        )

    else:

        pdf.drawString(
            145,
            y,
            "-"
        )

    # =====================================================
    # FOOTER LINE
    # =====================================================

    pdf.setStrokeColorRGB(
        0.8,
        0.8,
        0.8
    )

    pdf.line(
        50,
        80,
        545,
        80
    )

    # =====================================================
    # FOOTER TEXT
    # =====================================================

    pdf.setFillColorRGB(
        0.4,
        0.4,
        0.4
    )

    pdf.setFont(
        "Helvetica",
        9
    )

    pdf.drawCentredString(
        width / 2,
        60,
        "Thank you for shopping with SMART RETAIL"
    )

    pdf.drawCentredString(
        width / 2,
        45,
        "This is a computer-generated invoice."
    )

    # =====================================================
    # FINISH PDF
    # =====================================================

    pdf.showPage()

    pdf.save()

    return response