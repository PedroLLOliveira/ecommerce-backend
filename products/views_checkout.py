from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import quote

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Product
from .serializers_checkout import CheckoutValidateSerializer


def _money(d: Decimal) -> Decimal:
    return d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def _brl(d: Decimal) -> str:
    s = f'{_money(d):.2f}'
    return s.replace('.', ',')


def _build_message(customer_name: str, items_ok: list, total: Decimal, notes: str) -> str:
    lines = []
    if customer_name:
        lines.append(f'Olá! Meu nome é {customer_name}. Gostaria de fazer um pedido:')
    else:
        lines.append('Olá! Gostaria de fazer um pedido:')

    lines.append('')
    for it in items_ok:
        lines.append(f'- {it["name"]} x{it["qty"]} (R$ {_brl(it["unit_price"])}) = R$ {_brl(it["subtotal"])}')

    lines.append('')
    lines.append(f'Total: R$ {_brl(total)}')

    if notes:
        lines.append('')
        lines.append(f'Observações: {notes}')

    return '\n'.join(lines)


def _build_whatsapp_url(phone: str, message: str) -> str:
    phone_digits = ''.join([c for c in (phone or '') if c.isdigit()])
    text = quote(message, safe='')
    return f'https://wa.me/{phone_digits}?text={text}'


class CheckoutValidateAPIView(APIView):
    '''
    POST /api/v1/checkout/validate/

    Body:
    {
      'items': [{'product_id': '<uuid>', 'qty': 2}],
      'customer_name': 'Pedro',
      'notes': 'Entregar no período da tarde'
    }

    Response 200:
    {
      'ok': true/false,
      'items': [...],
      'total_value': '159.80',
      'message': '...',
      'whatsapp_url': 'https://wa.me/55....?text=...'
    }
    '''

    def post(self, request):
        serializer = CheckoutValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        items = serializer.validated_data['items']
        customer_name = serializer.validated_data.get('customer_name', '')
        notes = serializer.validated_data.get('notes', '')

        product_ids = [it['product_id'] for it in items]

        products = Product.objects.filter(id__in=product_ids).only('id', 'name', 'price', 'stock')
        products_map = {p.id: p for p in products}

        missing = [str(pid) for pid in product_ids if pid not in products_map]
        if missing:
            return Response(
                {'ok': False, 'error': 'Produtos não encontrados', 'missing_product_ids': missing},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_items = []
        ok = True
        total = Decimal('0.00')

        # valida item a item
        for it in items:
            p = products_map[it['product_id']]
            requested = int(it['qty'])
            available = int(p.stock)

            unit_price = Decimal(str(p.price))
            subtotal = _money(unit_price * requested)

            in_stock = available >= requested
            if not in_stock:
                ok = False

            response_items.append(
                {
                    'product_id': str(p.id),
                    'name': p.name,
                    'requested_qty': requested,
                    'available_qty': available,
                    'in_stock': in_stock,
                    'unit_price': f'{_money(unit_price):.2f}',
                    'subtotal': f'{subtotal:.2f}',
                }
            )

            if in_stock:
                total += subtotal

        # monta mensagem só com itens válidos (em estoque)
        items_ok = [
            {
                'name': r['name'],
                'qty': r['requested_qty'],
                'unit_price': Decimal(r['unit_price']),
                'subtotal': Decimal(r['subtotal']),
            }
            for r in response_items
            if r['in_stock']
        ]

        message = _build_message(customer_name, items_ok, total, notes)

        phone = getattr(settings, 'WHATSAPP_PHONE_NUMBER', '') or ''
        whatsapp_url = _build_whatsapp_url(phone, message) if phone else ''

        return Response(
            {
                'ok': ok,
                'items': response_items,
                'total_value': f'{_money(total):.2f}',
                'message': message,
                'whatsapp_url': whatsapp_url,
            },
            status=status.HTTP_200_OK,
        )
