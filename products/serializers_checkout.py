from rest_framework import serializers


class CheckoutItemSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    qty = serializers.IntegerField(min_value=1)


class CheckoutValidateSerializer(serializers.Serializer):
    items = CheckoutItemSerializer(many=True)
    customer_name = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
