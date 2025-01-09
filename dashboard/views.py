from django.shortcuts import render, redirect
from .forms import UploadFileForm
from .models import UploadedFile
import pandas as pd
import urllib.parse
from openpyxl import load_workbook
from django.core.paginator import Paginator
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for Matplotlib
import matplotlib.pyplot as plt
import io
import base64


def home(request):
    """Home page for file upload."""
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.save()
            file_path = uploaded_file.file.path
            encoded_file_path = urllib.parse.quote(file_path)
            return redirect('dashboard', file_path=encoded_file_path)
    else:
        form = UploadFileForm()
    return render(request, 'dashboard/home.html', {'form': form})


def read_excel_in_chunks(file_path, sheet_name=None, chunk_size=1000):
    """Read an Excel sheet in chunks using openpyxl."""
    workbook = load_workbook(file_path, read_only=True)
    sheets = workbook.sheetnames if sheet_name is None else [sheet_name]
    for sheet in sheets:
        worksheet = workbook[sheet]
        headers = [cell.value for cell in next(worksheet.iter_rows(max_row=1))]
        chunk = []
        for i, row in enumerate(worksheet.iter_rows(min_row=2, values_only=True), start=1):
            chunk.append(dict(zip(headers, row)))
            if i % chunk_size == 0:
                yield pd.DataFrame(chunk)
                chunk = []
        if chunk:
            yield pd.DataFrame(chunk)


def generate_graph(data, column_name, graph_type):
    """Generate graphs dynamically based on the data."""
    fig, ax = plt.subplots(figsize=(8, 4))
    img = io.BytesIO()

    if column_name in data.columns:
        if graph_type == 'bar':
            data_counts = data[column_name].value_counts()
            data_counts.plot(kind='bar', ax=ax, color="skyblue")
            ax.set_title(f"Bar Chart of {column_name}")
        elif graph_type == 'pie':
            data_counts = data[column_name].value_counts()
            data_counts.plot(kind='pie', ax=ax, autopct='%1.1f%%', startangle=90)
            ax.set_title(f"Pie Chart of {column_name}")
        elif graph_type == 'line':
            data[column_name].plot(ax=ax)
            ax.set_title(f"Line Chart of {column_name}")

    plt.tight_layout()
    plt.savefig(img, format='png')
    img.seek(0)
    graph_url = base64.b64encode(img.getvalue()).decode()
    plt.close(fig)
    return f"data:image/png;base64,{graph_url}"


def dashboard(request, file_path):
    """Dashboard view to display data."""
    decoded_file_path = urllib.parse.unquote(file_path)

    buttons = ['Summary', 'Enforcement_Sheet_Infringing', 'Enforcement_Sheet_Source', 
               'telegram', 'SocialMediaPlatforms', 'Premium']

    button_filters = {
        'Summary': ['Property Name', 'Fixtures'],
        'Enforcement_Sheet_Infringing': ['URL', 'Domain Name'],
        'Enforcement_Sheet_Source': ['Source Type', 'Date'],
        'Telegram': ['Message Type', 'User ID'],
        'SocialMediaPlatforms': ['Platform', 'Engagement'],
        'Premium': ['Subscription Type', 'Duration']
    }

    selected_button = request.GET.get('button', 'Summary')
    applied_filters = {
        key: request.GET.get(key, '') for key in button_filters.get(selected_button, [])
    }
    chunk_size = 1000
    graph = None
    unique_values = {}
    widgets = {}

    workbook = load_workbook(decoded_file_path, read_only=True)
    sheet_names = workbook.sheetnames

    all_chunks = []
    for chunk in read_excel_in_chunks(decoded_file_path, sheet_name=selected_button if selected_button != 'Summary' else None, chunk_size=chunk_size):
        for column, value in applied_filters.items():
            if value:
                if column in chunk.columns:
                    chunk = chunk[chunk[column] == value]
        if not chunk.empty:
            all_chunks.append(chunk)

    summary_data = pd.concat(all_chunks, ignore_index=True) if all_chunks else pd.DataFrame()

    if not summary_data.empty:
        if selected_button == 'Summary':
            widgets = {
                'Total Sheets': len(sheet_names),
                'Total Rows': len(summary_data),
                'Total Columns': len(summary_data.columns),
            }
            graph = generate_graph(summary_data, 'propertyname', 'bar')
        elif selected_button == 'Enforcement_Sheet_Infringing':
            widgets = {
                'Total URLs': summary_data['URL'].nunique() if 'URL' in summary_data.columns else 0,
                'Total Domains': summary_data['Domain Name'].nunique() if 'Domain Name' in summary_data.columns else 0,
            }
            graph = generate_graph(summary_data, 'propertyname', 'pie')
        elif selected_button == 'Enforcement_Sheet_Source':
            widgets = {
                'Total Sources': summary_data['Source Type'].nunique() if 'Source Type' in summary_data.columns else 0,
                'Earliest Date': summary_data['Date'].min() if 'Date' in summary_data.columns else 'N/A',
                'Latest Date': summary_data['Date'].max() if 'Date' in summary_data.columns else 'N/A',
            }
            graph = generate_graph(summary_data, 'Source Type', 'bar')
        elif selected_button == 'Telegram':
            widgets = {
                'Message Types': summary_data['Message Type'].nunique() if 'Message Type' in summary_data.columns else 0,
                'Active Users': summary_data['User ID'].nunique() if 'User ID' in summary_data.columns else 0,
            }
            graph = generate_graph(summary_data, 'propertyname', 'line')
        elif selected_button == 'Premium':
            widgets = {
                'Subscription Types': summary_data['Subscription Type'].nunique() if 'Subscription Type' in summary_data.columns else 0,
                'Average Duration': summary_data['Duration'].mean() if 'Duration' in summary_data.columns else 0,
            }
            graph = generate_graph(summary_data, 'propertyname', 'bar')

    paginator = Paginator(summary_data.values.tolist(), 200)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    paginated_data = pd.DataFrame(page_obj.object_list, columns=summary_data.columns) if not summary_data.empty else None

    return render(request, 'dashboard/dashboard.html', {
        'buttons': buttons,
        'selected_button': selected_button,
        'filters': button_filters.get(selected_button, []),
        'applied_filters': applied_filters,
        'unique_values': unique_values,
        'paginated_data': paginated_data,
        'page_obj': page_obj,
        'widgets': widgets,
        'graph': graph,
    })
