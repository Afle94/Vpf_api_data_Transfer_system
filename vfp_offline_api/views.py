from django.db import transaction
from django.db.models import Count, Max, Q, Sum
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models.functions import TruncMonth
from rest_framework import status, viewsets
from rest_framework.response import Response
from vfp_offline_api.models import Spsales
from vfp_offline_api.forms import RegisterForm, SpsalesForm
from vfp_offline_api.Seriealizers import SpsalesSerializer
from django.shortcuts import render



def get_sales_summary():
    return Spsales.objects.aggregate(
        total_records=Count('id'),
        total_amount=Sum('Amount'),
        total_net_amount=Sum('Net_Amount'),
        latest_transaction=Max('Trandate'),
    )


def percentile(values, percent):
    if not values:
        return 0
    index = (len(values) - 1) * percent
    lower = int(index)
    upper = min(lower + 1, len(values) - 1)
    if lower == upper:
        return values[lower]
    return values[lower] + ((values[upper] - values[lower]) * (index - lower))


def get_analytics_context():
    summary = get_sales_summary()
    vtype_stats = list(
        Spsales.objects.values('Vtype')
        .annotate(total=Count('id'), amount=Sum('Net_Amount'))
        .order_by('-total')[:8]
    )
    top_accounts = list(
        Spsales.objects.exclude(Acno__isnull=True)
        .exclude(Acno='')
        .values('Acno')
        .annotate(total=Count('id'), amount=Sum('Net_Amount'))
        .order_by('-amount')[:10]
    )
    monthly_stats = list(
        Spsales.objects.exclude(Trandate__isnull=True)
        .annotate(month=TruncMonth('Trandate'))
        .values('month')
        .annotate(total=Count('id'), amount=Sum('Net_Amount'))
        .order_by('month')[:12]
    )
    max_vtype_total = max([item['total'] for item in vtype_stats], default=1)
    max_account_amount = max([item['amount'] or 0 for item in top_accounts], default=1)
    max_month_amount = max([item['amount'] or 0 for item in monthly_stats], default=1)
    for item in vtype_stats:
        item['percent'] = int((item['total'] / max_vtype_total) * 100) if max_vtype_total else 0
    for item in top_accounts:
        item['percent'] = int(((item['amount'] or 0) / max_account_amount) * 100) if max_account_amount else 0
    for item in monthly_stats:
        item['percent'] = int(((item['amount'] or 0) / max_month_amount) * 100) if max_month_amount else 0

    chart_points = []
    if monthly_stats:
        count = len(monthly_stats)
        for index, item in enumerate(monthly_stats):
            x = 40 + (index * (620 / max(count - 1, 1)))
            value = item['amount'] or 0
            y = 240 - ((value / max_month_amount) * 180 if max_month_amount else 0)
            chart_points.append({'x': round(x, 2), 'y': round(y, 2), 'item': item})
    chart_polyline = ' '.join([f"{point['x']},{point['y']}" for point in chart_points])
    area_polygon = f"40,240 {chart_polyline} 660,240" if chart_polyline else ''

    amount_values = sorted([
        float(value)
        for value in Spsales.objects.exclude(Net_Amount__isnull=True)
        .values_list('Net_Amount', flat=True)
    ])
    histogram_bins = []
    box_plot = None
    if amount_values:
        min_value = amount_values[0]
        max_value = amount_values[-1]
        bin_count = 8
        bin_size = (max_value - min_value) / bin_count if max_value != min_value else 1
        raw_bins = []
        for index in range(bin_count):
            start = min_value + (index * bin_size)
            end = start + bin_size
            count = len([
                value for value in amount_values
                if (start <= value < end) or (index == bin_count - 1 and value <= end)
            ])
            raw_bins.append({'start': start, 'end': end, 'count': count})
        max_bin_count = max([item['count'] for item in raw_bins], default=1)
        for index, item in enumerate(raw_bins):
            height = (item['count'] / max_bin_count) * 180 if max_bin_count else 0
            histogram_bins.append({
                'x': 46 + (index * 76),
                'y': 230 - height,
                'height': height,
                'count': item['count'],
                'label': f"{item['start']:.0f} - {item['end']:.0f}",
            })

        q1 = percentile(amount_values, 0.25)
        median = percentile(amount_values, 0.5)
        q3 = percentile(amount_values, 0.75)

        def box_x(value):
            spread = max_value - min_value
            if spread == 0:
                return 350
            return 60 + (((value - min_value) / spread) * 580)

        box_plot = {
            'min': min_value,
            'q1': q1,
            'median': median,
            'q3': q3,
            'max': max_value,
            'min_x': box_x(min_value),
            'q1_x': box_x(q1),
            'median_x': box_x(median),
            'q3_x': box_x(q3),
            'max_x': box_x(max_value),
            'box_width': max(box_x(q3) - box_x(q1), 2),
        }

    pie_stats = []
    total_vtype_records = sum([item['total'] for item in vtype_stats]) or 1
    offset = 0
    for item in vtype_stats[:6]:
        percent = (item['total'] / total_vtype_records) * 100
        pie_stats.append({
            'label': item['Vtype'] or 'Blank',
            'count': item['total'],
            'percent': round(percent, 2),
            'offset': round(-offset, 2),
        })
        offset += percent

    scatter_rows = list(
        Spsales.objects.exclude(Amount__isnull=True)
        .exclude(Net_Amount__isnull=True)
        .order_by('-id')
        .values('Voucher_no', 'Amount', 'Net_Amount')[:80]
    )
    scatter_points = []
    if scatter_rows:
        amounts = [float(row['Amount']) for row in scatter_rows]
        net_amounts = [float(row['Net_Amount']) for row in scatter_rows]
        min_amount, max_amount = min(amounts), max(amounts)
        min_net, max_net = min(net_amounts), max(net_amounts)
        for row in scatter_rows:
            amount = float(row['Amount'])
            net_amount = float(row['Net_Amount'])
            x = 45 + (((amount - min_amount) / (max_amount - min_amount)) * 600 if max_amount != min_amount else 300)
            y = 235 - (((net_amount - min_net) / (max_net - min_net)) * 185 if max_net != min_net else 95)
            scatter_points.append({
                'x': round(x, 2),
                'y': round(y, 2),
                'voucher': row['Voucher_no'] or '-',
                'amount': amount,
                'net_amount': net_amount,
            })

    return {
        'summary': summary,
        'vtype_stats': vtype_stats,
        'top_accounts': top_accounts,
        'monthly_stats': monthly_stats,
        'chart_points': chart_points,
        'chart_polyline': chart_polyline,
        'area_polygon': area_polygon,
        'histogram_bins': histogram_bins,
        'box_plot': box_plot,
        'pie_stats': pie_stats,
        'scatter_points': scatter_points,
    }


def login_view(request):
    error = ''
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        error = 'Invalid username or password.'

    return render(request, 'vfp_offline_api/login.html', {'error': error})


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'vfp_offline_api/register.html', {'form': form})


@login_required
def dashboard_view(request):
    summary = get_sales_summary()
    records = Spsales.objects.order_by('-id')
    query = request.GET.get('q', '').strip()
    vtype = request.GET.get('vtype', '').strip()

    if query:
        records = records.filter(
            Q(Voucher_no__icontains=query)
            | Q(Vtype__icontains=query)
            | Q(invoice_no__icontains=query)
            | Q(Acno__icontains=query)
            | Q(Mobile_no__icontains=query)
        )
    if vtype:
        records = records.filter(Vtype=vtype)

    paginator = Paginator(records, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    vtypes = Spsales.objects.exclude(Vtype='').order_by('Vtype').values_list('Vtype', flat=True).distinct()
    return render(
        request,
        'vfp_offline_api/dashboard.html',
        {
            'summary': summary,
            'page_obj': page_obj,
            'records': page_obj.object_list,
            'query': query,
            'selected_vtype': vtype,
            'vtypes': vtypes,
        },
    )


@login_required
def analytics_view(request):
    return render(request, 'vfp_offline_api/analytics.html', get_analytics_context())


@login_required
def sales_edit_view(request, pk):
    record = get_object_or_404(Spsales, pk=pk)
    if request.method == 'POST':
        form = SpsalesForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            return redirect('records')
    else:
        form = SpsalesForm(instance=record)
    return render(request, 'vfp_offline_api/sales_form.html', {'form': form, 'record': record})


@login_required
def sales_delete_view(request, pk):
    record = get_object_or_404(Spsales, pk=pk)
    if request.method == 'POST':
        record.delete()
        return redirect('records')
    return redirect('records')


@login_required
def sales_bulk_delete_view(request):
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_ids')
        delete_scope = request.POST.get('delete_scope')
        if delete_scope == 'filtered':
            records = Spsales.objects.all()
            query = request.POST.get('q', '').strip()
            vtype = request.POST.get('vtype', '').strip()
            if query:
                records = records.filter(
                    Q(Voucher_no__icontains=query)
                    | Q(Vtype__icontains=query)
                    | Q(invoice_no__icontains=query)
                    | Q(Acno__icontains=query)
                    | Q(Mobile_no__icontains=query)
                )
            if vtype:
                records = records.filter(Vtype=vtype)
            records.delete()
        elif selected_ids:
            Spsales.objects.filter(id__in=selected_ids).delete()
    return redirect('records')


def logout_view(request):
    logout(request)
    return redirect('login')


def error_page_view(request, exception=None, status_code=404):
    is_debug = settings.DEBUG
    page_title = 'Page Not Found' if status_code == 404 else 'Something Went Wrong'
    message = 'The page you are looking for is not available or has been moved.'
    if request.path.startswith('/admin/'):
        page_title = 'Admin Area Disabled'
        message = 'The Django admin area is not available on this deployment.'
    elif request.path.startswith('/spsales/'):
        page_title = 'Public API Page Disabled'
        message = 'This endpoint is not available as a public browser page. Use the application dashboard instead.'
    elif request.path.startswith('/api/') and status_code == 404:
        page_title = 'API Endpoint Not Found'
        message = 'The requested API endpoint does not exist.'
    elif status_code >= 500:
        page_title = 'Something Went Wrong'
        message = 'We could not complete this request right now.'
    mode_label = 'Development Mode' if is_debug else 'Production Mode'
    mode_message = (
        'This is a clean app error page. Technical details are hidden from the browser view.'
        if is_debug
        else 'Technical details are hidden to keep this application secure on cloud hosting.'
    )
    return render(
        request,
        'vfp_offline_api/error.html',
        {
            'status_code': status_code,
            'page_title': page_title,
            'message': message,
            'mode_label': mode_label,
            'mode_message': mode_message,
            'path': request.path,
        },
        status=status_code,
    )


def not_found_view(request, unmatched_path=None, exception=None):
    return error_page_view(request, exception=exception, status_code=404)


def server_error_view(request):
    return error_page_view(request, status_code=500)


class SpsalesViewSet(viewsets.ModelViewSet):
    queryset = Spsales.objects.all()
    serializer_class = SpsalesSerializer

    def create(self, request, *args, **kwargs):
        many = isinstance(request.data, list)
        serializer = self.get_serializer(data=request.data, many=many)
        serializer.is_valid(raise_exception=True)
        if many:
            result = self.bulk_upsert(serializer.validated_data)
            return Response(
                {
                    'message': 'Records saved successfully',
                    **result,
                },
                status=status.HTTP_201_CREATED,
            )
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def bulk_upsert(self, rows):
        rows_by_voucher = {}
        rows_without_voucher = []
        for row in rows:
            voucher_no = row.get('Voucher_no')
            if voucher_no:
                rows_by_voucher[voucher_no] = row
            else:
                rows_without_voucher.append(row)

        unique_rows = list(rows_by_voucher.values()) + rows_without_voucher
        voucher_numbers = [
            row['Voucher_no']
            for row in unique_rows
            if row.get('Voucher_no')
        ]
        existing = Spsales.objects.in_bulk(voucher_numbers, field_name='Voucher_no')
        fields_to_update = [
            'Vtype',
            'invoice_no',
            'Acno',
            'Trandate',
            'Recdate',
            'Amount',
            'Net_Amount',
            'Mobile_no',
        ]
        to_create = []
        to_update = []

        for row in unique_rows:
            voucher_no = row.get('Voucher_no')
            if voucher_no and voucher_no in existing:
                obj = existing[voucher_no]
                for field in fields_to_update:
                    setattr(obj, field, row.get(field))
                to_update.append(obj)
            else:
                to_create.append(Spsales(**row))

        with transaction.atomic():
            if to_create:
                Spsales.objects.bulk_create(to_create, batch_size=500)
            if to_update:
                Spsales.objects.bulk_update(to_update, fields_to_update, batch_size=500)

        return {
            'count': len(rows),
            'saved': len(unique_rows),
            'skipped_duplicates': len(rows) - len(unique_rows),
            'created': len(to_create),
            'updated': len(to_update),
        }
    
    