from standard.models import StandardModel
from django.db import models
from django.utils.translation import gettext_lazy as _


class Product(StandardModel):
    '''
      Modelo para representar produtos no sistema.
    '''
    name = models.CharField(max_length=255, verbose_name=_("Name"))
    description = models.TextField(verbose_name=_("Description"))
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Price"))
    stock = models.PositiveIntegerField(verbose_name=_("Stock Quantity"))

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
        ordering = ['name']

    def __str__(self):
        return self.name

    def is_in_stock(self):
        return self.stock > 0


class Category(StandardModel):
    '''
      Modelo para categorizar produtos.
    '''
    name = models.CharField(max_length=255, verbose_name=_("Name"))
    description = models.TextField(verbose_name=_("Description"), blank=True)

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        ordering = ['name']

    def __str__(self):
        return self.name


class ProductCategory(StandardModel):
    '''
      Modelo intermediario para relacionar produtos e categorias (Many-to-Many).
    '''
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='categories', verbose_name=_("Product"))
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name=_("Category"))

    class Meta:
        verbose_name = _("Product Category")
        verbose_name_plural = _("Product Categories")
        unique_together = ('product', 'category')

    def __str__(self):
        return f"{self.product.name} - {self.category.name}"


class ProductImage(StandardModel):
    '''
      Modelo para armazenar imagens de produtos.
    '''
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name=_("Product"))
    image = models.ImageField(upload_to='product_images/', verbose_name=_("Image"))
    alt_text = models.CharField(max_length=255, blank=True, verbose_name=_("Alternative Text"))

    class Meta:
        verbose_name = _("Product Image")
        verbose_name_plural = _("Product Images")

    def __str__(self):
        return f"Image for {self.product.name}"

    def get_image_url(self):
        if self.image:
            return self.image.url
        return ""

