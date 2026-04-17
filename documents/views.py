from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q

from clients.models import Client
from deals.models import Deal
from .models import OurLegalEntity, ContractTemplate, GeneratedContract
from .forms import OurLegalEntityForm, ContractTemplateForm, GeneratedContractForm
from .rendering import build_contract_context, render_contract_html, ContractRenderError
from billing.models import Invoice, NonReturnAct, ShippingDocument

DOC_TYPE_META = {
    'contract': {
        'label': 'договоров',
        'list_title': 'Шаблоны договоров',
        'new_title': 'Новый шаблон договора',
    },
    'invoice': {
        'label': 'счетов',
        'list_title': 'Шаблоны счетов',
        'new_title': 'Новый шаблон счета',
    },
    'act': {
        'label': 'актов',
        'list_title': 'Шаблоны актов',
        'new_title': 'Новый шаблон акта',
    },
}


def our_entity_list(request):
    return render(request, 'documents/our_entity_list.html', {
        'entities': OurLegalEntity.objects.all(),
        'page_title': 'Наши реквизиты',
    })


def our_entity_create(request):
    if request.method == 'POST':
        form = OurLegalEntityForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Реквизиты исполнителя сохранены.')
            return redirect('documents_our_entity_list')
    else:
        form = OurLegalEntityForm()
    return render(request, 'documents/our_entity_form.html', {
        'form': form, 'page_title': 'Новые реквизиты исполнителя', 'action': 'Создать',
    })


def our_entity_edit(request, pk):
    entity = get_object_or_404(OurLegalEntity, pk=pk)
    if request.method == 'POST':
        form = OurLegalEntityForm(request.POST, instance=entity)
        if form.is_valid():
            form.save()
            messages.success(request, 'Реквизиты обновлены.')
            return redirect('documents_our_entity_list')
    else:
        form = OurLegalEntityForm(instance=entity)
    return render(request, 'documents/our_entity_form.html', {
        'form': form, 'entity': entity,
        'page_title': f'Редактирование: {entity.name}', 'action': 'Сохранить',
    })


def document_template_hub(request):
    return render(request, 'documents/template_hub.html', {
        'page_title': 'Шаблоны документов',
        'contract_templates_count': ContractTemplate.objects.filter(document_type='contract').count(),
        'invoice_templates_count': ContractTemplate.objects.filter(document_type='invoice').count(),
        'act_templates_count': ContractTemplate.objects.filter(document_type='act').count(),
        'generated_contracts_count': GeneratedContract.objects.count(),
        'invoices_count': Invoice.objects.count(),
        'shipping_acts_count': ShippingDocument.objects.count(),
        'non_return_acts_count': NonReturnAct.objects.count(),
    })


def _document_template_list(request, document_type):
    meta = DOC_TYPE_META[document_type]
    qs = ContractTemplate.objects.filter(document_type=document_type)
    q = request.GET.get('q', '')
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(slug__icontains=q))
    return render(request, 'documents/template_list.html', {
        'templates': qs, 'q': q,
        'page_title': meta['list_title'],
        'document_type': document_type,
    })


def _document_template_create(request, document_type):
    meta = DOC_TYPE_META[document_type]
    if request.method == 'POST':
        form = ContractTemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.document_type = document_type
            template.save()
            messages.success(request, 'Шаблон сохранён.')
            return redirect(f'documents_{document_type}_template_list')
    else:
        form = ContractTemplateForm()
    return render(request, 'documents/template_form.html', {
        'form': form, 'page_title': meta['new_title'], 'action': 'Создать',
        'document_type': document_type,
    })


def _document_template_edit(request, pk, document_type):
    tpl = get_object_or_404(ContractTemplate, pk=pk, document_type=document_type)
    if request.method == 'POST':
        form = ContractTemplateForm(request.POST, instance=tpl)
        if form.is_valid():
            template = form.save(commit=False)
            template.document_type = document_type
            template.save()
            messages.success(request, 'Шаблон обновлён.')
            return redirect(f'documents_{document_type}_template_list')
    else:
        form = ContractTemplateForm(instance=tpl)
    return render(request, 'documents/template_form.html', {
        'form': form, 'template': tpl,
        'page_title': f'Шаблон: {tpl.name}', 'action': 'Сохранить',
        'document_type': document_type,
    })


def contract_template_list(request):
    return _document_template_list(request, 'contract')


def contract_template_create(request):
    return _document_template_create(request, 'contract')


def contract_template_edit(request, pk):
    return _document_template_edit(request, pk, 'contract')


def invoice_template_list(request):
    return _document_template_list(request, 'invoice')


def invoice_template_create(request):
    return _document_template_create(request, 'invoice')


def invoice_template_edit(request, pk):
    return _document_template_edit(request, pk, 'invoice')


def act_template_list(request):
    return _document_template_list(request, 'act')


def act_template_create(request):
    return _document_template_create(request, 'act')


def act_template_edit(request, pk):
    return _document_template_edit(request, pk, 'act')


def generated_contract_list(request):
    qs = GeneratedContract.objects.select_related('client', 'our_entity', 'template', 'deal')
    client_id = request.GET.get('client')
    if client_id:
        qs = qs.filter(client_id=client_id)
    return render(request, 'documents/contract_list.html', {
        'contracts': qs[:200],
        'filter_client_id': client_id,
        'page_title': 'Договоры',
    })


def generated_contract_create(request):
    initial = {}
    if request.GET.get('client'):
        try:
            initial['client'] = int(request.GET['client'])
        except ValueError:
            pass
    if request.GET.get('deal'):
        try:
            deal_id = int(request.GET['deal'])
            initial['deal'] = deal_id
            deal_obj = Deal.objects.filter(pk=deal_id).select_related('our_entity').first()
            if deal_obj and deal_obj.our_entity_id:
                initial['our_entity'] = deal_obj.our_entity_id
        except ValueError:
            pass
    default_entity = OurLegalEntity.objects.filter(is_default=True).first()
    if default_entity:
        initial.setdefault('our_entity', default_entity.pk)

    if request.method == 'POST':
        form = GeneratedContractForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            if obj.deal_id and obj.deal and obj.deal.our_entity_id:
                obj.our_entity = obj.deal.our_entity
            ctx = build_contract_context(
                our_entity=obj.our_entity,
                client=obj.client,
                deal=obj.deal,
                contract_number=obj.number,
                contract_date=obj.contract_date,
            )
            try:
                obj.rendered_html = render_contract_html(obj.template.body, ctx)
            except ContractRenderError as exc:
                messages.error(request, f'Ошибка в шаблоне: {exc}')
                return render(request, 'documents/contract_form.html', {
                    'form': form, 'page_title': 'Новый договор', 'action': 'Сформировать',
                })
            obj.save()
            messages.success(request, f'Договор №{obj.number} сформирован.')
            return redirect('documents_contract_detail', pk=obj.pk)
    else:
        form = GeneratedContractForm(initial=initial)
    return render(request, 'documents/contract_form.html', {
        'form': form, 'page_title': 'Новый договор', 'action': 'Сформировать',
    })


def generated_contract_detail(request, pk):
    contract = get_object_or_404(
        GeneratedContract.objects.select_related('client', 'our_entity', 'template', 'deal'),
        pk=pk,
    )
    return render(request, 'documents/contract_detail.html', {
        'contract': contract, 'page_title': f'Договор №{contract.number}',
    })


def generated_contract_print(request, pk):
    contract = get_object_or_404(GeneratedContract, pk=pk)
    return render(request, 'documents/contract_print.html', {
        'contract': contract,
    })
