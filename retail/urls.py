from django.urls import path
from . import views


urlpatterns = [

    # =====================================================
    # DASHBOARD
    # =====================================================

    path(
        "",
        views.dashboard,
        name="dashboard"
    ),


    # =====================================================
    # VENDORS
    # =====================================================

    path(
        "vendors/",
        views.vendor_list,
        name="vendor_list"
    ),

    path(
        "vendors/add/",
        views.vendor_add,
        name="vendor_add"
    ),

    path(
        "vendors/edit/<int:pk>/",
        views.vendor_edit,
        name="vendor_edit"
    ),

    path(
        "vendors/delete/<int:pk>/",
        views.vendor_delete,
        name="vendor_delete"
    ),


    # =====================================================
    # PURCHASES
    # =====================================================

    path(
        "purchases/",
        views.purchase_list,
        name="purchase_list"
    ),

    path(
        "purchases/add/",
        views.purchase_add,
        name="purchase_add"
    ),

    path(
        "purchases/edit/<int:pk>/",
        views.purchase_edit,
        name="purchase_edit"
    ),

    path(
        "purchases/delete/<int:pk>/",
        views.purchase_delete,
        name="purchase_delete"
    ),


    # =====================================================
    # SALES
    # =====================================================

    path(
        "sales/",
        views.sale_list,
        name="sale_list"
    ),

    path(
        "sales/add/",
        views.sale_add,
        name="sale_add"
    ),

    path(
        "sales/edit/<int:pk>/",
        views.sale_edit,
        name="sale_edit"
    ),

    path(
        "sales/delete/<int:pk>/",
        views.sale_delete,
        name="sale_delete"
    ),

    path(
        "sales/<int:pk>/invoice/",
        views.sale_invoice_pdf,
        name="sale_invoice_pdf"
    ),


    # =====================================================
    # INVENTORY
    # =====================================================

    path(
        "inventory/",
        views.inventory_list,
        name="inventory_list"
    ),

    path(
        "inventory/add/",
        views.inventory_add,
        name="inventory_add"
    ),

    path(
        "inventory/<int:pk>/",
        views.inventory_detail,
        name="inventory_detail"
    ),


    # =====================================================
    # PROFIT & LOSS
    # =====================================================

    path(
        "profit-loss/",
        views.profit_loss_list,
        name="profit_loss_list"
    ),

]