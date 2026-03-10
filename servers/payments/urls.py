from django.urls import path
from .views import (
    create_order, verify_payment, razorpay_webhook, payment_history, refund_payment
)
from .admin_views import admin_list_payments, admin_list_transactions

urlpatterns = [
    path('create-order/', create_order),
    path('verify/', verify_payment),
    path('webhook/', razorpay_webhook),
    path('history/', payment_history),
    path('refund/', refund_payment),
    
    # Admin Panel APIs
    path('admin/payments/', admin_list_payments),
    path('admin/transactions/', admin_list_transactions),
]
