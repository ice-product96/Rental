from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from .models import Client
from .forms import ClientForm


def client_list(request):
    qs = Client.objects.all()
    q = request.GET.get('q', '')
    client_type = request.GET.get('type', '')
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(phone__icontains=q) |
                       Q(inn__icontains=q) | Q(email__icontains=q))
    if client_type:
        qs = qs.filter(client_type=client_type)
    return render(request, 'clients/list.html', {
        'clients': qs, 'q': q, 'client_type': client_type,
        'page_title': 'Клиенты',
    })


def client_detail(request, pk):
    client = get_object_or_404(Client, pk=pk)
    deals = client.deals.select_related().order_by('-created_at')
    return render(request, 'clients/detail.html', {
        'client': client, 'deals': deals,
        'page_title': f'Клиент: {client.name}',
    })


def client_create(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save()
            messages.success(request, f'Клиент «{client.name}» создан.')
            return redirect('client_detail', pk=client.pk)
    else:
        form = ClientForm(initial={'client_type': request.GET.get('type', 'individual')})
    return render(request, 'clients/form.html', {
        'form': form, 'page_title': 'Новый клиент', 'action': 'Создать',
    })


def client_edit(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, 'Данные клиента обновлены.')
            return redirect('client_detail', pk=client.pk)
    else:
        form = ClientForm(instance=client)
    return render(request, 'clients/form.html', {
        'form': form, 'client': client,
        'page_title': f'Редактирование: {client.name}', 'action': 'Сохранить',
    })


def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        name = client.name
        client.delete()
        messages.success(request, f'Клиент «{name}» удалён.')
        return redirect('client_list')
    return render(request, 'clients/confirm_delete.html', {
        'client': client, 'page_title': f'Удаление: {client.name}',
    })
