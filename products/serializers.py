from django.db import transaction
from rest_framework import serializers

from .models import Product, Category, ProductCategory, ProductImage


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'description', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class ProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ('id', 'image', 'image_url', 'alt_text', 'created_at', 'updated_at')
        read_only_fields = ('id', 'image_url', 'created_at', 'updated_at')

    def get_image_url(self, obj):
        return obj.get_image_url()


class ProductReadSerializer(serializers.ModelSerializer):
    is_in_stock = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            'id',
            'name',
            'description',
            'price',
            'stock',
            'is_in_stock',
            'categories',
            'images',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields

    def get_is_in_stock(self, obj):
        return obj.is_in_stock()

    def get_categories(self, obj):
        pcs = obj.categories.select_related('category').all()
        cats = [pc.category for pc in pcs]
        return CategorySerializer(cats, many=True).data


class ProductWriteSerializer(serializers.ModelSerializer):
    '''
    Escrita (UUID):
    - category_ids: lista de UUIDs de Category
    - images: lista de operações (JSON)
        [
          {'file_key': 'img1', 'alt_text': 'Frente'},                          # cria
          {'id': '<uuid>', 'alt_text': 'Novo alt'},                            # atualiza metadata
          {'id': '<uuid>', 'delete': true},                                    # deleta
          {'id': '<uuid>', 'file_key': 'img_new', 'alt_text': 'Nova foto'}     # atualiza arquivo + metadata
        ]

    Multipart:
    - 'images' deve ser enviado como string JSON
    - arquivos em keys separadas (img1, img_new, etc.)
    '''
    category_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
        write_only=True,
    )

    images = serializers.JSONField(required=False, write_only=True)

    class Meta:
        model = Product
        fields = ('id', 'name', 'description', 'price', 'stock', 'category_ids', 'images')
        read_only_fields = ('id',)

    def validate_category_ids(self, value):
        # value já vem como lista de UUID (python uuid.UUID)
        existing = set(Category.objects.filter(id__in=value).values_list('id', flat=True))
        missing = [cid for cid in value if cid not in existing]
        if missing:
            # stringifica para ficar legível
            missing_str = [str(x) for x in missing]
            raise serializers.ValidationError(f'Categorias não encontradas: {missing_str}')
        return value

    def validate_images(self, value):
        if value is None:
            return value
        if not isinstance(value, list):
            raise serializers.ValidationError('images deve ser uma lista.')

        allowed = {'id', 'alt_text', 'delete', 'file_key'}

        for i, item in enumerate(value):
            if not isinstance(item, dict):
                raise serializers.ValidationError(f'images[{i}] deve ser um objeto.')

            extra = set(item.keys()) - allowed
            if extra:
                raise serializers.ValidationError(f'images[{i}] possui campos inválidos: {sorted(extra)}')

            # valida id se vier
            if 'id' in item and item['id'] not in (None, ''):
                try:
                    serializers.UUIDField().to_internal_value(item['id'])
                except Exception:
                    raise serializers.ValidationError(f'images[{i}].id precisa ser um UUID válido.')

            if item.get('delete') is True and not item.get('id'):
                raise serializers.ValidationError(f'images[{i}]: para deletar é obrigatório informar "id".')

            if not item.get('id') and not item.get('file_key'):
                raise serializers.ValidationError(
                    f'images[{i}]: para criar uma imagem, informe "file_key" (campo do arquivo no multipart).'
                )

        return value

    def _get_uploaded_file(self, file_key: str):
        request = self.context.get('request')
        if not request:
            return None
        return request.FILES.get(file_key)

    @transaction.atomic
    def create(self, validated_data):
        category_ids = validated_data.pop('category_ids', [])
        images_ops = validated_data.pop('images', [])

        product = Product.objects.create(**validated_data)

        if category_ids:
            ProductCategory.objects.bulk_create(
                [ProductCategory(product=product, category_id=cid) for cid in category_ids],
                ignore_conflicts=True,
            )

        # create-only: não aceita id nas imagens
        for op in images_ops:
            if op.get('id'):
                raise serializers.ValidationError('Na criação, não envie "id" em images[].')

            file_key = op.get('file_key')
            file_obj = self._get_uploaded_file(file_key) if file_key else None
            if not file_obj:
                raise serializers.ValidationError(f'Arquivo não encontrado no form-data para file_key="{file_key}".')

            ProductImage.objects.create(
                product=product,
                image=file_obj,
                alt_text=op.get('alt_text', ''),
            )

        return product

    @transaction.atomic
    def update(self, instance, validated_data):
        category_ids = validated_data.pop('category_ids', None)
        images_ops = validated_data.pop('images', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if category_ids is not None:
            ProductCategory.objects.filter(product=instance).delete()
            if category_ids:
                ProductCategory.objects.bulk_create(
                    [ProductCategory(product=instance, category_id=cid) for cid in category_ids],
                    ignore_conflicts=True,
                )

        if images_ops is not None:
            uuid_field = serializers.UUIDField()

            for op in images_ops:
                raw_id = op.get('id')
                img_id = uuid_field.to_internal_value(raw_id) if raw_id else None

                to_delete = op.get('delete') is True
                alt_text = op.get('alt_text', None)
                file_key = op.get('file_key', None)

                if img_id:
                    try:
                        img = ProductImage.objects.get(id=img_id, product=instance)
                    except ProductImage.DoesNotExist:
                        raise serializers.ValidationError(f'Imagem id={str(img_id)} não pertence a este produto.')

                    if to_delete:
                        img.delete()
                        continue

                    if alt_text is not None:
                        img.alt_text = alt_text

                    if file_key:
                        file_obj = self._get_uploaded_file(file_key)
                        if not file_obj:
                            raise serializers.ValidationError(
                                f'Arquivo não encontrado no form-data para file_key="{file_key}".'
                            )
                        img.image = file_obj

                    img.save()

                else:
                    if to_delete:
                        continue

                    if not file_key:
                        raise serializers.ValidationError('Para criar nova imagem, informe file_key.')
                    file_obj = self._get_uploaded_file(file_key)
                    if not file_obj:
                        raise serializers.ValidationError(f'Arquivo não encontrado no form-data para file_key="{file_key}".')

                    ProductImage.objects.create(
                        product=instance,
                        image=file_obj,
                        alt_text=alt_text or '',
                    )

        return instance