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
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import numpy as np
from .summary import (
    aggregate_matchday_data,
    create_enhanced_matchday_line_plot,
    get_social_media_platform_data,
    create_social_media_platform_bar_chart,
    get_monthly_totals,
    create_monthly_totals_line_plot,
    create_bar_chart
)
# ✅ Import all required functions from telegram.py
from .telegram import (
    calculate_telegram_summary, 
    get_top_telegram_properties, 
    telegram_monthly_totals, 
    create_telegram_top_fixtures_bar_chart, 
    create_telegram_channel_type_pie_chart,
    get_telegram_platform_data, 
    get_telegram_top_fixtures, 
    telegram_domains_by_subscribers, 
    create_treemap_chart_telegram, 
    create_enhanced_matchday_line_plot, 
    aggregate_matchday_data, 
    telegram_monthly_totals_line_plot,
    top_fixtures_donut_chart,
    top_fixtures_graph_donut_chart,
    create_channel_type_pie_chart,
    create_top_property_bar_chart,
)



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

import pandas as pd
from openpyxl import load_workbook

def read_excel_in_chunks(file_path, sheet_names=None, chunk_size=1000):
    """Read multiple Excel sheets in chunks using openpyxl."""
    
    # ✅ Load workbook and check available sheets
    workbook = load_workbook(file_path, read_only=True)
    print("📌 Available Sheets in the Workbook:", workbook.sheetnames)

    # ✅ If sheet_names is None, read all sheets
    sheets_to_read = sheet_names if sheet_names else workbook.sheetnames

    for sheet in sheets_to_read:
        if sheet not in workbook.sheetnames:
            print(f"⚠️ Warning: Sheet '{sheet}' not found in the workbook. Skipping...")
            continue  # Skip missing sheets

        worksheet = workbook[sheet]

        # ✅ Ensure headers exist
        try:
            headers = [cell.value for cell in next(worksheet.iter_rows(max_row=1))]
        except StopIteration:
            print(f"⚠️ Warning: Sheet '{sheet}' is empty. Skipping...")
            continue

        # ✅ Handle missing headers (replace None with generic names)
        headers = [str(h).strip() if h is not None else f"Column_{i}" for i, h in enumerate(headers)]
        headers.append('SheetName')  # Add SheetName column to track source sheet
        
        chunk = []
        for i, row in enumerate(worksheet.iter_rows(min_row=2, values_only=True), start=1):
            row_data = list(row) + [sheet]  # Append SheetName to row
            chunk.append(dict(zip(headers, row_data)))
            
            if i % chunk_size == 0:
                df_chunk = pd.DataFrame(chunk)
                
                # ✅ Ensure column exists before applying transformation
                if not df_chunk.empty and 'Identification Timestamp' in df_chunk.columns:
                    df_chunk['Identification Timestamp'] = pd.to_datetime(df_chunk['Identification Timestamp'], errors='coerce')

                yield df_chunk
                chunk = []

        if chunk:  # Yield remaining rows
            df_chunk = pd.DataFrame(chunk)
            
            # ✅ Ensure column exists before applying transformation
            if not df_chunk.empty and 'Identification Timestamp' in df_chunk.columns:
                df_chunk['Identification Timestamp'] = pd.to_datetime(df_chunk['Identification Timestamp'], errors='coerce')

            yield df_chunk

def generate_summary_graphs(summary_data):
    print("summary dataa..", summary_data)
    graphs = []
    # Graph 1: Sheet-wise Identification & Delisted
    if 'SheetName' in summary_data.columns and 'URL' in summary_data.columns:
        print("Generating Sheet-wise Identification & Delisted Graph...")  # Debugging
        graphs.append(create_bar_chart(summary_data))
    else:
        print("not Generating Sheet-wise Identification & Delisted Graph...")  # Debugging


    # Graph 2: Monthly Identification & Removal Trends
    monthly_data = get_monthly_totals(summary_data)
    if not monthly_data.empty:
        print("Generating Monthly Trends Graph...")
        graph2 = create_monthly_totals_line_plot(monthly_data)
        if graph2:
            graphs.append(graph2)

    # Graph 3: Social Media Platform Analysis
    social_media_data = get_social_media_platform_data(summary_data)
    if not social_media_data.empty:
        graph_social_media = create_social_media_platform_bar_chart(social_media_data)
        if graph_social_media:
            graphs.append(graph_social_media)

    #graph4
    matchday_data = aggregate_matchday_data(summary_data)
    if not matchday_data.empty:
        match_day =  create_enhanced_matchday_line_plot(matchday_data)
        graphs.append(match_day)
        print("matchday output")


    # Graph 5: Top 5 Properties - Infringements and Removals
    if 'propertyname' in summary_data.columns and 'Status' in summary_data.columns and 'URL' in summary_data.columns:
        top_properties = summary_data.groupby('propertyname')['URL'].count().nlargest(5)
        removals = (
            summary_data[summary_data['Status'] == 'Approved']
            .groupby('propertyname')['URL']
            .count()
            .reindex(top_properties.index, fill_value=0)
        )
        fig, ax = plt.subplots(figsize=(10, 6), facecolor='#f8f9fa')
        x = np.arange(len(top_properties))
        bar_width = 0.3
        bar1 = ax.bar(x - bar_width / 2, top_properties, width=bar_width, label='Infringements', color='#ff6b6b', edgecolor='black', linewidth=0.7)
        bar2= ax.bar(x + bar_width / 2, removals, width=bar_width, label='Removals', color='#4a90e2', edgecolor='black', linewidth=0.7)

        ax.set_title('Top 5 Properties - Identification & Removals', fontsize=16)
        ax.set_xticks(x)

            # Adjust Y-axis limits to prevent overlap at top and bottom
        min_ylim = 1 if removals.min() > 0 else 0.5
        max_ylim = ax.get_ylim()[1] * 1.3  # Increased space above the highest bar
        ax.set_ylim(min_ylim, max_ylim)

         # Adding annotations
        for bar in bar1:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02 * max(top_properties), 
                    f'{int(bar.get_height())}', ha='center', va='bottom', fontsize=10, color='#ff6b6b')
        for bar in bar2:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02 * max(removals), 
                    f'{int(bar.get_height())}', ha='center', va='bottom', fontsize=10, color='#4a90e2')

        ax.set_xticklabels(top_properties.index, rotation=45, ha='right')
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        ax.set_facecolor('#f5f5f5')  # Light gray background inside the plot area
        ax.set_ylabel('Count')
        ax.legend()
        img = io.BytesIO()
        plt.tight_layout()
        plt.savefig(img, format='png')
        img.seek(0)
        graphs.append(base64.b64encode(img.getvalue()).decode())
        plt.close(fig)

    # Graph 3: Top 5 Fixtures - Identification & Removals
    fixture_summary = summary_data.groupby(['fixtures', 'URL']).agg(
        removal_flag=('Status', lambda x: any(x.isin(['Approved', 'Removed'])))
    ).reset_index()

    fixture_summary = fixture_summary.groupby('fixtures').agg(
        total_urls=('URL', 'count'),
        removal_count=('removal_flag', 'sum')
    ).reset_index().sort_values(by='total_urls', ascending=False)

    top_fixtures = fixture_summary.nlargest(5, 'total_urls')[['fixtures', 'total_urls', 'removal_count']]
    
    if not top_fixtures.empty:
        fig, ax = plt.subplots(figsize=(12, 6), facecolor='#f8f9fa')
        x = np.arange(len(top_fixtures['fixtures']))
        bar_width = 0.3
         # Improved bar colors
        bar1 = ax.bar(x - bar_width / 2, top_fixtures['total_urls'], width=bar_width, label='Total URLs', color='#ff6b6b', edgecolor='black', linewidth=0.7)
        bar2 = ax.bar(x + bar_width / 2, top_fixtures['removal_count'], width=bar_width, label='Removal Count', color='#4a90e2', edgecolor='black', linewidth=0.7)

        ax.set_title("Top 5 Fixtures - Identification & Removal", fontsize=14, fontweight='bold')
        ax.set_ylabel('Count', fontsize=12, fontweight='bold')

        # Enhanced title and labels 
        ax.set_xticks(x)
        ax.set_xticklabels(top_fixtures['fixtures'], rotation=45, ha='right', fontsize=10)


        ax.grid(axis='y', linestyle='--', alpha=0.7)
        ax.set_facecolor('#f5f5f5')  # Light gray background inside the plot area
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        # Adding annotations
        for bar in bar1:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02 * max(top_fixtures['total_urls']), 
                    f'{int(bar.get_height())}', ha='center', va='bottom', fontsize=10, color='#ff6b6b')
        for bar in bar2:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02 * max(top_fixtures['removal_count']), 
                    f'{int(bar.get_height())}', ha='center', va='bottom', fontsize=10, color='#4a90e2')

        # Legend customization
        ax.legend(loc='upper right', fontsize=10, facecolor='white', edgecolor='black')

        plt.tight_layout()
        img = io.BytesIO()
        plt.tight_layout()
        plt.savefig(img, format='png')
        img.seek(0)
        graphs.append(base64.b64encode(img.getvalue()).decode())
        plt.close(fig)


    #graph 4 sheet wise data
    
    return graphs


#  Function to generate Telegram graph summary
def generate_telegram_summary_graphs(summary_data):
    """Generate all Telegram-related summary graphs."""
    graphs = []
    print("coloumns listt---",summary_data.columns.tolist())
     # Graph 1: Monthly Identification & Removal Trends
    fixture_data = get_telegram_top_fixtures(summary_data)

    print("fixture_data-----",fixture_data)
    if not fixture_data.empty:
        print("Generating Monthly Trends Graph...")
        graph2 =  create_telegram_top_fixtures_bar_chart(fixture_data)
        if graph2:
            graphs.append(graph2)
    #GRAPH2 : TREE GRAPH TOP10 
    top_10_channels =  create_treemap_chart_telegram(telegram_domains_by_subscribers(summary_data))
    graphs.append(top_10_channels)
    #graph3 : top_property_bar_chart
    top_property_bar_chart= create_top_property_bar_chart(get_top_telegram_properties(summary_data))
    graphs.append(top_property_bar_chart)
    #graph4 : 
    channel_type = create_channel_type_pie_chart(summary_data)
    graphs.append(channel_type)
    #graph 5
    Top_veiws =  top_fixtures_graph_donut_chart(top_fixtures_donut_chart(summary_data))
    graphs.append(Top_veiws)
    #graph6
    telegram_montly = telegram_monthly_totals_line_plot(telegram_monthly_totals(summary_data))
    graphs.append(telegram_montly)

    return graphs



def dashboard(request, file_path):
    """Dashboard view to display data."""
    decoded_file_path = urllib.parse.unquote(file_path)

    buttons = ['Summary', 'internet', 'telegram', 'SocialMediaPlatforms', 'Premium', 'Send Mail']

    button_filters = {
        'Summary': ['propertyname', 'fixtures'],
        'internet': ['propertyname', 'fixtures'],
        'telegram': ['propertyname', 'fixtures'],
        'SocialMediaPlatforms': ['Platform', 'Engagement'],
        'Premium': ['Subscription Type', 'Duration']
    }
    
    selected_button = request.GET.get('button', 'Summary')
    applied_filters = {
        key: request.GET.get(key, '') for key in button_filters.get(selected_button, [])
    }

    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    chunk_size = 1000
    graph_urls = []
    unique_values = {}
    widgets = {}

    workbook = load_workbook(decoded_file_path, read_only=True)
    sheet_names = workbook.sheetnames
    all_chunks = []
    for chunk in read_excel_in_chunks(decoded_file_path, sheet_names=[selected_button] if selected_button != 'Summary' else None, chunk_size=chunk_size):
        if not chunk.empty:
            for column in button_filters.get(selected_button, []):
                if column in chunk.columns:
                    if column not in unique_values:
                        unique_values[column] = set()
                    unique_values[column].update(chunk[column].dropna().unique())

            # Apply filters
            for column, value in applied_filters.items():           
                if value and column in chunk.columns:
                    chunk = chunk[chunk[column] == value]

            if start_date and end_date and 'Identification Timestamp' in chunk.columns:
                chunk['Identification Timestamp'] = pd.to_datetime(chunk['Identification Timestamp'], errors='coerce')
                chunk = chunk[(chunk['Identification Timestamp'] >= pd.to_datetime(start_date)) & 
                              (chunk['Identification Timestamp'] <= pd.to_datetime(end_date))]

            if not chunk.empty:
                all_chunks.append(chunk)

            if not chunk.empty:
                all_chunks.append(chunk)

    unique_values = {key: list(value) for key, value in unique_values.items()}
    summary_data = pd.concat(all_chunks, ignore_index=True) if all_chunks else pd.DataFrame()

    if not summary_data.empty:
        if selected_button == 'Summary':
            widgets = {
                'Total Properties': summary_data['propertyname'].nunique(),
                'Total Fixtures': summary_data['fixtures'].nunique(),
                'Total Infringements': summary_data['URL'].nunique(),
                'No.of Websites/channels': summary_data['DomainName'].nunique() ,
                '% Removal': round((summary_data.loc[summary_data['Status'].isin(['Approved', 'Removed']), 'URL'].nunique() /summary_data['URL'].nunique() * 100) if summary_data['URL'].nunique() > 0 else 0,3),
                'No.Of Websites/Channels/Suspended': summary_data.loc[summary_data['Status'].isin(['Approved', 'Removed']), 'DomainName'].nunique(),
            }
            graph_urls.extend(generate_summary_graphs(summary_data))
        elif selected_button == 'internet':
           
            # ✅ Compute Widgets
            widgets = {
                'Total Properties': summary_data['propertyname'].nunique() if 'propertyname' in summary_data.columns else "⚠️ Not Found",
                'Total Fixtures': summary_data['fixtures'].nunique() if 'fixtures' in summary_data.columns else "⚠️ Not Found",
                'Total Infringements': summary_data['url'].nunique() if 'url' in summary_data.columns else "⚠️ Not Found",
                'No.of Websites/channels': summary_data['domainname'].nunique() if 'domainname' in summary_data.columns else "⚠️ Not Found",
                '% Removal': round(
                    (summary_data.loc[summary_data['status'].isin(['Approved', 'Removed']), 'url'].nunique() /
                    summary_data['url'].nunique() * 100) if 'status' in summary_data.columns and summary_data['url'].nunique() > 0 else 0, 3
                ),
                'No.Of Websites/Channels Suspended': summary_data.loc[summary_data['status'].isin(['Approved', 'Removed']), 'domainname'].nunique()
            }

            print("🚀 Debug: Internet Widgets ->", widgets)


        elif selected_button == 'telegram':
            telegram_data = summary_data[summary_data['SheetName'] == 'telegram'] 

            print("get telegram data",telegram_data)
            telegram_data['views'] = pd.to_numeric(telegram_data['views'], errors='coerce')
            telegram_data['channelsubscribers'] = pd.to_numeric(telegram_data['channelsubscribers'], errors='coerce')
            approved_removed_filter = telegram_data[telegram_data['Status'].isin(['Approved', 'Removed'])]['URL'].nunique()
            total_infringements_telegram = telegram_data['URL'].nunique()
            print("---total_infringements_telegram",total_infringements_telegram)
            widgets = {
                'Total Properties': telegram_data['propertyname'].nunique(),
                'Total Fixtures': telegram_data['fixtures'].nunique(),
                'Total Infringements': telegram_data['URL'].nunique(),
                'Total Channels': telegram_data['DomainName'].nunique(),
                '% Removal': (approved_removed_filter / total_infringements_telegram) * 100 if total_infringements_telegram > 0 else 0,
                'Total Views': telegram_data['views'].fillna(0).sum(),
                'Channels Suspended': telegram_data[telegram_data['ChannelStatus'].isin(['Suspended'])]['URL'].nunique(),
                'Total Subscribers': telegram_data['channelsubscribers'].fillna(0).sum(),
                'Impacted Subscribers': telegram_data[telegram_data['Status'].isin(['Approved', 'Removed'])]['channelsubscribers'].fillna(0).sum(),
            }
            graph_urls.extend(generate_telegram_summary_graphs(telegram_data))
            
        elif selected_button == 'Premium':
            widgets = {
                'Subscription Types': summary_data['Subscription Type'].nunique() if 'Subscription Type' in summary_data.columns else 0,
                'Average Duration': summary_data['Duration'].mean() if 'Duration' in summary_data.columns else 0,
            }
            graph_urls.append(generate_graph(summary_data, 'Subscription Type', 'pie'))
            graph_urls.append(generate_graph(summary_data, 'Duration', 'bar'))

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
        'graphs': graph_urls,
        'start_date': start_date,
        'end_date': end_date,
    })
