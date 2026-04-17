from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.template import Template, Context
from django.http import HttpResponse
from .models import Invoice, InvoiceItem, ShippingDocument, ShippingDocumentItem, NonReturnAct, NonReturnActItem
from deals.models import Deal
from pricing.calculator import num_to_words_ru
from documents.models import ContractTemplate, OurLegalEntity


def invoice_list(request):
    invoices = Invoice.objects.select_related('deal', 'deal__client').order_by('-date')
    status = request.GET.get('status', '')
    if status:
        invoices = invoices.filter(status=status)
    return render(request, 'billing/invoice_list.html', {
        'invoices': invoices, 'status': status,
        'page_title': 'Счета',
    })


def invoice_create(request, deal_pk):
    deal = get_object_or_404(Deal, pk=deal_pk)
    prefill_items = _get_prefill_items(deal)

    if request.method == 'POST':
        if not prefill_items:
            messages.error(request, 'Невозможно сформировать счёт: в сделке нет сумм для выставления.')
            return redirect('deal_detail', pk=deal.pk)

        invoice = Invoice.objects.create(
            deal=deal,
            invoice_type=request.POST.get('invoice_type', 'rental'),
            date=request.POST.get('date', timezone.now().date()),
            due_date=request.POST.get('due_date') or None,
            notes=request.POST.get('notes', ''),
        )

        subtotal = 0
        for item in prefill_items:
            qty = float(item['qty'])
            price = float(item['price'])
            total = qty * price
            subtotal += total
            InvoiceItem.objects.create(
                invoice=invoice,
                name=item['name'],
                qty=qty,
                unit=item['unit'],
                price=price,
                total=total,
            )

        vat = subtotal * 0.2 if deal.vat_mode == 'with_vat' else 0
        invoice.subtotal = subtotal
        invoice.vat_amount = vat
        invoice.total = subtotal + vat
        invoice.save()

        messages.success(request, f'Счёт №{invoice.number} создан.')
        return redirect('invoice_detail', pk=invoice.pk)

    return render(request, 'billing/invoice_form.html', {
        'deal': deal, 'prefill_items': prefill_items,
        'today': timezone.now().date(),
        'page_title': f'Новый счёт — сделка №{deal.number}',
    })


def _get_prefill_items(deal):
    items = []
    if deal.total_rental > 0:
        label = deal.category_names if deal.category_names != '—' else 'оборудование'
        items.append({
            'name': f'Аренда: {label} на {deal.rental_days} дн.',
            'qty': 1, 'unit': 'услуга', 'price': float(deal.total_rental), 'total': float(deal.total_rental)
        })
    if deal.deposit_amount > 0:
        items.append({
            'name': 'Залог за оборудование',
            'qty': 1, 'unit': 'услуга', 'price': float(deal.deposit_amount), 'total': float(deal.deposit_amount)
        })
    if deal.delivery_cost > 0:
        delivery_total = float(deal.delivery_cost) * 2
        items.append({
            'name': 'Доставка и возврат оборудования',
            'qty': 2, 'unit': 'рейс', 'price': float(deal.delivery_cost), 'total': delivery_total
        })
    return items


def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    return render(request, 'billing/invoice_detail.html', {
        'invoice': invoice,
        'amount_words': num_to_words_ru(invoice.total),
        'page_title': f'Счёт №{invoice.number}',
    })


def invoice_status_change(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        invoice.status = new_status
        invoice.save()
        if new_status == 'paid' and invoice.deal.status in ('invoice_sent',):
            invoice.deal.status = 'paid'
            invoice.deal.save()
        messages.success(request, f'Статус счёта изменён.')
    return redirect('invoice_detail', pk=pk)


def invoice_print(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    company = _company_from_deal(invoice.deal)
    context = {
        'invoice': invoice,
        'company': company,
        'amount_words': num_to_words_ru(invoice.total),
    }
    custom_html, template_obj, render_error = _render_custom_document_template('invoice', context)
    debug_mode = request.GET.get('debug_template') == '1'
    if custom_html:
        response = HttpResponse(custom_html)
        response['X-Document-Template-Source'] = f'custom:{template_obj.slug}'
        return response
    if debug_mode and render_error:
        messages.warning(request, f'Ошибка рендера шаблона счета "{template_obj.name}": {render_error}')
    response = render(request, 'billing/invoice_print.html', context)
    response['X-Document-Template-Source'] = 'builtin:billing/invoice_print.html'
    return response


def shipping_doc_create(request, deal_pk):
    deal = get_object_or_404(Deal, pk=deal_pk)
    equipment_items = deal.equipment_items.select_related('equipment_type').all()

    if request.method == 'POST':
        doc = ShippingDocument.objects.create(
            deal=deal,
            number=request.POST.get('number', ''),
            date=request.POST.get('date', timezone.now().date()),
            doc_type=request.POST.get('doc_type', 'issue'),
            notes=request.POST.get('notes', ''),
        )
        for item in equipment_items:
            qty = int(request.POST.get(f'qty_{item.pk}', item.quantity) or 0)
            if qty > 0:
                ShippingDocumentItem.objects.create(
                    document=doc,
                    equipment_type=item.equipment_type,
                    quantity=qty,
                    unit_price=item.unit_price,
                )
        messages.success(request, 'Документ отгрузки создан.')
        return redirect('shipping_doc_print', pk=doc.pk)

    return render(request, 'billing/shipping_doc_form.html', {
        'deal': deal, 'equipment_items': equipment_items,
        'today': timezone.now().date(),
        'page_title': 'Документ отгрузки',
    })


def shipping_doc_print(request, pk):
    doc = get_object_or_404(ShippingDocument, pk=pk)
    company = _company_from_deal(doc.deal)
    total_value = sum(i.quantity * float(i.unit_price) for i in doc.items.all())
    context = {
        'doc': doc, 'company': company,
        'total_value': total_value,
        'amount_words': num_to_words_ru(total_value),
    }
    custom_html, template_obj, render_error = _render_custom_document_template('act', context)
    debug_mode = request.GET.get('debug_template') == '1'
    if custom_html:
        response = HttpResponse(custom_html)
        response['X-Document-Template-Source'] = f'custom:{template_obj.slug}'
        return response
    if debug_mode and render_error:
        messages.warning(request, f'Ошибка рендера шаблона акта "{template_obj.name}": {render_error}')
    response = render(request, 'billing/shipping_doc_print.html', context)
    response['X-Document-Template-Source'] = 'builtin:billing/shipping_doc_print.html'
    return response


def non_return_act_create(request, deal_pk):
    deal = get_object_or_404(Deal, pk=deal_pk)
    equipment_items = deal.equipment_items.select_related('equipment_type').all()

    if request.method == 'POST':
        act = NonReturnAct.objects.create(
            deal=deal,
            number=request.POST.get('number', ''),
            date=request.POST.get('date', timezone.now().date()),
            notes=request.POST.get('notes', ''),
        )
        total = 0
        for item in equipment_items:
            qty_ret = int(request.POST.get(f'qty_ret_{item.pk}', 0) or 0)
            NonReturnActItem.objects.create(
                act=act,
                equipment_type=item.equipment_type,
                quantity_issued=item.quantity,
                quantity_returned=qty_ret,
                unit_price=item.unit_price,
            )
            total += (item.quantity - qty_ret) * float(item.unit_price)

        act.total_amount = total
        act.save()

        deal.status = 'non_return'
        deal.save()

        messages.success(request, 'Акт невозврата создан.')
        return redirect('non_return_act_print', pk=act.pk)

    return render(request, 'billing/non_return_form.html', {
        'deal': deal, 'equipment_items': equipment_items,
        'today': timezone.now().date(),
        'page_title': f'Акт невозврата — сделка №{deal.number}',
    })


def non_return_act_print(request, pk):
    act = get_object_or_404(NonReturnAct, pk=pk)
    company = _company_from_deal(act.deal)
    context = {
        'act': act, 'company': company,
        'amount_words': num_to_words_ru(act.total_amount),
    }
    custom_html, template_obj, render_error = _render_custom_document_template('act', context)
    debug_mode = request.GET.get('debug_template') == '1'
    if custom_html:
        response = HttpResponse(custom_html)
        response['X-Document-Template-Source'] = f'custom:{template_obj.slug}'
        return response
    if debug_mode and render_error:
        messages.warning(request, f'Ошибка рендера шаблона акта "{template_obj.name}": {render_error}')
    response = render(request, 'billing/non_return_print.html', context)
    response['X-Document-Template-Source'] = 'builtin:billing/non_return_print.html'
    return response


def _render_custom_document_template(document_type, context_dict):
    template_obj = ContractTemplate.objects.filter(
        document_type=document_type,
        is_active=True,
    ).order_by('-updated_at').first()
    if not template_obj:
        return None, None, None
    try:
        rendered_html = Template(template_obj.body).render(Context(context_dict))
        return rendered_html, template_obj, None
    except Exception as exc:
        return None, template_obj, str(exc)


def _company_from_deal(deal):
    entity = getattr(deal, 'our_entity', None) or OurLegalEntity.objects.filter(is_default=True).first()
    return {
        'name': entity.name if entity else '',
        'full_name': entity.company_full_name if entity and entity.company_full_name else (entity.name if entity else ''),
        'inn': entity.inn if entity else '',
        'kpp': entity.kpp if entity else '',
        'ogrn': entity.ogrn if entity else '',
        'address': (entity.legal_address or entity.address) if entity else '',
        'director': entity.director if entity else '',
        'director_short': entity.director_short if entity else '',
        'bank': entity.bank_name if entity else '',
        'account': entity.bank_account if entity else '',
        'bik': entity.bank_bik if entity else '',
        'corr_account': entity.bank_corr_account if entity else '',
    }
