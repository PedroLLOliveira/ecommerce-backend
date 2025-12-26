from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ProductViewSet, CategoryViewSet, ProductImageViewSet
from .views_checkout import CheckoutValidateAPIView

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='products')
router.register(r'categories', CategoryViewSet, basename='categories')
router.register(r'product-images', ProductImageViewSet, basename='product-images')

urlpatterns = [
    path('api/v1/', include(router.urls)),
    path('api/v1/checkout/validate/', CheckoutValidateAPIView.as_view(), name='checkout-validate'),
]