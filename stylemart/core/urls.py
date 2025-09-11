
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("product/<slug:slug>/", views.product_detail, name="product_detail"),
    path("category/<slug:slug>/", views.category_products, name="category_products"),
    path("cart/add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/", views.view_cart, name="view_cart"),
    path("cart/update/", views.update_cart_item, name="update_cart_item"),
    path("order/", views.place_order, name="place_order"),
    path("order/confirmation/<int:order_id>/", views.order_confirmation, name="order_confirmation"),
    path("orders/", views.order_history, name="order_history"),
]
