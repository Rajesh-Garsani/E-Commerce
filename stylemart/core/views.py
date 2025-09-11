
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, Category, Cart, Order, OrderItem, UserProfile
from .forms import SignupForm, LoginForm

from django.shortcuts import render
from .models import OrderItem, Order

# Home view: shows categories, featured and all products.
def home(request):
    categories = Category.objects.all()
    featured_products = Product.objects.all()[:4]
    all_products = Product.objects.all()
    return render(request, "home.html", {
        "categories": categories,
        "featured_products": featured_products,
        "all_products": all_products
    })

# Product detail page: shows product and a POST form to add to cart or checkout.
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)

    # If user submits "order now" (from product page), forward to place_order with one item.
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_to_cart":
            # Redirect to add_to_cart view (POST)
            return add_to_cart(request, product_id=product.id)
        elif action == "order_now":
            # Create a quick one-item order OR redirect to checkout page prefilling the product
            # We'll add product to cart (for simplicity) then redirect to place_order
            if request.user.is_authenticated:
                cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
                if not created:
                    cart_item.quantity += 1
                    cart_item.save()
                return redirect("place_order")
            else:
                messages.info(request, "Please login to order.")
                return redirect("login")

    return render(request, "product_detail.html", {"product": product})

# Products by category
def category_products(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = category.products.all()
    return render(request, "category_products.html", {"category": category, "products": products})

# Signup view using custom SignupForm
def signup_view(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created and logged in.")
            return redirect("home")
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = SignupForm()
    return render(request, "auth/signup.html", {"form": form})

# Login view
def login_view(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "Logged in successfully.")
            return redirect("home")
        else:
            messages.error(request, "Invalid credentials.")
    else:
        form = LoginForm()
    return render(request, "auth/login.html", {"form": form})

# Logout view
@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have logged out.")
    return redirect("home")

# Add to cart (accepts POST). If called internally from product_detail, request may already be POST.
@login_required
def add_to_cart(request, product_id=None):
    # Support both: direct POST with product_id or internal call with argument
    if request.method == "POST" or product_id is not None:
        # Prefer product_id from argument, else from POST
        pid = product_id or int(request.POST.get('product_id'))
        product = get_object_or_404(Product, id=pid)

        cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
        if not created:
            # Increase quantity if already in cart
            cart_item.quantity += 1
        cart_item.save()
        messages.success(request, f"{product.name} added to your cart.")
        # If AJAX call, return a minimal response (not implemented). For now redirect back.
        return redirect(request.META.get("HTTP_REFERER", "home"))
    else:
        # Non-POST to this URL: redirect to product page
        messages.error(request, "Invalid request method.")
        return redirect("home")

# View cart with totals
@login_required
def view_cart(request):
    # Get the latest "open" order for the user (assuming you track status)
    order = Order.objects.filter(user=request.user, status="cart").first()

    if order:
        cart_items = order.items.all()
    else:
        cart_items = []

    # Calculate totals
    for item in cart_items:
        item.total_price = item.product.price * item.quantity

    total = sum(item.total_price for item in cart_items)

    return render(request, "cart.html", {
        "cart_items": cart_items,
        "total": total,
    })

# Update cart item quantity or remove item (handles POST from cart page)
@login_required
def update_cart_item(request):
    if request.method == "POST":
        item_id = request.POST.get("item_id")
        action = request.POST.get("action")
        try:
            item = Cart.objects.get(id=item_id, user=request.user)
        except Cart.DoesNotExist:
            messages.error(request, "Cart item not found.")
            return redirect("view_cart")

        if action == "remove":
            item.delete()
            messages.success(request, "Item removed from cart.")
        elif action == "set_quantity":
            qty = int(request.POST.get("quantity", 1))
            if qty <= 0:
                item.delete()
            else:
                item.quantity = qty
                item.save()
                messages.success(request, "Quantity updated.")
    return redirect("view_cart")

# Checkout / place order view
@login_required
def place_order(request):
    cart_items = Cart.objects.filter(user=request.user).select_related('product')
    if not cart_items.exists():
        messages.info(request, "Your cart is empty.")
        return redirect("home")

    if request.method == "POST":
        # Use checkout form fields to create the order
        full_name = request.POST.get("full_name", "").strip()
        address = request.POST.get("address", "").strip()
        phone = request.POST.get("phone", "").strip()

        # If user has profile and fields blank, try to fill
        try:
            profile = request.user.userprofile
        except UserProfile.DoesNotExist:
            profile = None

        if not phone and profile:
            phone = profile.phone or ""
        if not full_name and profile:
            full_name = profile.full_name or ""

        order = Order.objects.create(
            user=request.user,
            phone=phone or "",
            address=address or ""
        )
        # Add items
        for item in cart_items:
            OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity)
        # Clear cart
        cart_items.delete()
        messages.success(request, "Order placed successfully.")
        return redirect("order_confirmation", order_id=order.id)

    # GET: show checkout page
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = None

    return render(request, "place_order.html", {"cart_items": cart_items, "profile": profile})

# Order confirmation
@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    total = order.total_price  # property
    return render(request, "order_confirmation.html", {"order": order, "total": total})

# Order history
@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "order_history.html", {"orders": orders})
