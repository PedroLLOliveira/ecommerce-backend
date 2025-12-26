from rest_framework.viewsets import ModelViewSet
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser

from .models import Product, Category, ProductImage
from .serializers import (
    ProductReadSerializer,
    ProductWriteSerializer,
    CategorySerializer,
    ProductImageSerializer,
)


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all().order_by("name")
    serializer_class = CategorySerializer
    lookup_field = "id"
    lookup_url_kwarg = "pk"


class ProductViewSet(ModelViewSet):
    queryset = Product.objects.all().prefetch_related(
      "images",
      "categories__category").order_by("name")
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    lookup_field = "id"
    lookup_url_kwarg = "pk"

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return ProductReadSerializer
        return ProductWriteSerializer


class ProductImageViewSet(ModelViewSet):
    '''
    Opcional: endpoint direto para gerenciar imagens (CRUD).
    Útil se você quiser editar imagem/alt_text sem passar pelo Product.
    '''
    queryset = ProductImage.objects.select_related('product').all()
    serializer_class = ProductImageSerializer
    parser_classes = (JSONParser, MultiPartParser, FormParser)