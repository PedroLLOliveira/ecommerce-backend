from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Product, Category, ProductCategory, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'image_url')
    readonly_fields = ('image_url',)

    @admin.display(description=_('Image URL'))
    def image_url(self, obj):
        return obj.get_image_url()


class ProductCategoryInline(admin.TabularInline):
    model = ProductCategory
    extra = 1
    autocomplete_fields = ('category',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'is_in_stock_display', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    inlines = (ProductCategoryInline, ProductImageInline)
    list_editable = ('price', 'stock')

    @admin.display(boolean=True, description=_('In stock'))
    def is_in_stock_display(self, obj):
        return obj.is_in_stock()


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    list_filter = ('created_at', 'updated_at')


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'category', 'created_at', 'updated_at')
    search_fields = ('product__name', 'category__name')
    list_filter = ('created_at', 'updated_at')
    autocomplete_fields = ('product', 'category')


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'alt_text', 'image_url', 'created_at', 'updated_at')
    search_fields = ('product__name', 'alt_text')
    list_filter = ('created_at', 'updated_at')
    autocomplete_fields = ('product',)
    fields = ('product', 'image', 'alt_text', 'image_url')
    readonly_fields = ('image_url',)

    @admin.display(description=_('Image URL'))
    def image_url(self, obj):
        return obj.get_image_url()
