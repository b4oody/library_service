from .models import Purchase


def cart_count(request):
    cart_items_count = 0
    if request.user.is_authenticated:
        try:
            cart = Purchase.objects.get(user=request.user, payment_status="pending")
            cart_items_count = sum(item.quantity for item in cart.purchaseitem_set.all())
        except Purchase.DoesNotExist:
            cart_items_count = 0

    return {"cart_items_count": cart_items_count}