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
        headers.append("SheetName")  # Add SheetName column
        chunk = []
        for i, row in enumerate(worksheet.iter_rows(min_row=2, values_only=True), start=1):
            row_data = list(row) + [sheet]  # Append SheetName to row
            chunk.append(dict(zip(headers, row_data)))
            
            if i % chunk_size == 0:
                df_chunk = pd.DataFrame(chunk)
                if 'Identification Timestamp' in df_chunk.columns:
                    df_chunk['Identification Timestamp'] = pd.to_datetime(df_chunk['Identification Timestamp'], errors='coerce')
                yield df_chunk
                chunk = []

        if chunk:
            df_chunk = pd.DataFrame(chunk)
            if 'Identification Timestamp' in df_chunk.columns:
                df_chunk['Identification Timestamp'] = pd.to_datetime(df_chunk['Identification Timestamp'], errors='coerce')
            yield df_chunk


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

def aggregate_matchday_data(data):
    """Aggregates data to calculate total URLs and sorts Matchday properly."""
    if 'Matchday' not in data.columns:
        return pd.DataFrame()  # Return empty dataframe if Matchday column doesn't exist

    data['Matchday'] = data['Matchday'].astype(str).str.strip().str.title()  # Normalize formatting
    matchday_summary = data.groupby('Matchday').agg(total_urls=('URL', 'count')).reset_index()
    matchday_summary['Matchday_num'] = matchday_summary['Matchday'].str.extract(r'(\d+)$').astype(float)
    matchday_summary = matchday_summary.sort_values(by='Matchday_num', ascending=True).drop(columns='Matchday_num')
    return matchday_summary


# ✅ Function to create enhanced Matchday graph
def create_enhanced_matchday_line_plot(matchday_data):
    """Generates Matchday Trends Line Plot."""
    if matchday_data.empty:
        return None

    fig, ax = plt.subplots(figsize=(12, 6), facecolor='#f9f9f9')
    ax.plot(matchday_data['Matchday'], matchday_data['total_urls'], marker='o', markersize=8,
            color='#ff6b6b', linewidth=2.5, label='Total URLs')

    for i, row in matchday_data.iterrows():
        ax.annotate(f"{int(row['total_urls'])}", xy=(i, row['total_urls']),
                    xytext=(0, 15), textcoords='offset points', ha='center',
                    fontsize=9, color='#4a90e2', fontweight='bold')

    ax.set_title("Matchday Identification and Removal Trends", fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(range(len(matchday_data['Matchday'])))
    ax.set_xticklabels(matchday_data['Matchday'], rotation=45, ha='right', fontsize=10)
    ax.set_ylim(0, matchday_data['total_urls'].max() * 1.2)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.set_facecolor('#f0f7ff')
    ax.legend(facecolor='#f2f2f2', fontsize=8, loc='upper left', bbox_to_anchor=(1, 1))

    plt.tight_layout()
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close(fig)

    return base64.b64encode(img.getvalue()).decode()


def get_social_media_platform_data(data):
    """Extract data specific to SocialMediaPlatforms sheet."""
    if 'SheetName' not in data.columns:
        return pd.DataFrame()

    social_media_data = data[data['SheetName'] == 'SocialMediaPlatforms']
    if social_media_data.empty:
        return pd.DataFrame()

    domain_summary = social_media_data.groupby('DomainName').agg(
        total_urls=('URL', 'count'),
        removed_count=('Status', lambda x: x.isin(['Approved', 'Removed']).sum()),
    ).reset_index().sort_values(by='total_urls', ascending=False)

    return domain_summary


# ✅ Generate Social Media Platform Bar Chart
def create_social_media_platform_bar_chart(domain_data):
    """Generate bar chart for social media platforms"""
    if domain_data.empty:
        return None

    fig, ax = plt.subplots(figsize=(12, 6), facecolor='#f8f9fa')
    x = np.arange(len(domain_data['DomainName']))
    bar_width = 0.3

    bar1 = ax.bar(x - bar_width / 2, domain_data['total_urls'], width=bar_width, color='#ff6b6b', label='Total URLs')
    bar2 = ax.bar(x + bar_width / 2, domain_data['removed_count'], width=bar_width, color='#4a90e2', label='Delisting Count')

    # Calculate highlights
    total_feeds_removed = (domain_data['removed_count'].sum() / domain_data['total_urls'].sum()) * 100
    top_platform = domain_data.loc[domain_data['removed_count'].idxmax()]
    # Title with highlights included
    highlight_text = (
        f"Highlights:\n"
        f"• {total_feeds_removed:.1f}% of pirate feeds removed\n"
        f"• Top Platform: {top_platform['DomainName']} ({top_platform['removed_count']}/{top_platform['total_urls']}) removed"
    )
    title_text = f"Platform-wise Analysis for Social Media\n{highlight_text}"
    ax.set_title(title_text, fontsize=14, fontweight='bold', pad=30, loc='center')
    ax.set_xlabel('')  # If you don’t want a label, provide an empty string

    # Y-axis setup
    ax.set_ylabel('Count (Log Scale)', fontsize=12, fontweight='bold', labelpad=10)
    ax.set_yscale('log')  # Applying logarithmic scale to y-axis
    max_value = max(domain_data['total_urls'].max(), domain_data['removed_count'].max())
    ax.set_ylim(1, max_value * 2)  # Add 100% padding above the highest value for much more height

    # X-axis setup
    ax.set_xticks(x)
    ax.set_xticklabels(domain_data['DomainName'], rotation=30, ha='right', fontsize=10)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
        # Add bar labels for better visibility
    for bar in bar1:
        height = bar.get_height()
        offset = 1.2  # Constant small offset for better positioning
        ax.text(
            bar.get_x() + bar.get_width() / 2, 
            height + offset,  # Offset value adjusted for log scale
            f'{int(height)}', 
            ha='center', 
            va='bottom', 
            fontsize=10, 
            color='#ff6b6b'
        )

    for bar in bar2:
        height = bar.get_height()
        offset = 1.2  # Same constant offset for the second group
        ax.text(
            bar.get_x() + bar.get_width() / 2, 
            height + offset,  # Offset value adjusted for log scale
            f'{int(height)}', 
            ha='center', 
            va='bottom', 
            fontsize=10, 
            color='#4a90e2'
        )

    ax.legend(loc='upper right', fontsize=10, facecolor='white', edgecolor='black')
    plt.subplots_adjust(top=0.85, bottom=0.2)


    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close(fig)

    return base64.b64encode(img.getvalue()).decode()


def get_monthly_totals(data):
    """Aggregate data by month while handling 'dd/mm/yyyy HH:MM' format."""
    
    # Convert 'Identification Timestamp' to datetime, ensuring the correct format
    if 'Identification Timestamp' not in data.columns:
        print("Error: 'Identification Timestamp' column is missing!")
        return pd.DataFrame()
    
    
    # Extract Year-Month for grouping
    data['Month'] = data['Identification Timestamp'].dt.to_period('M')

    # Aggregate Total URLs and Removal Counts
    monthly_summary = (
        data.groupby('Month')
        .agg(
            total_urls=('URL', 'count'),
            removal_count=('Status', lambda x: x.isin(['Approved', 'Removed']).sum())
        )
        .reset_index()
    )

    # Convert 'Month' back to Timestamp for easy plotting
    monthly_summary['Month'] = monthly_summary['Month'].dt.to_timestamp()

    return monthly_summary

def create_monthly_totals_line_plot(monthly_data):
    """Generate a line plot for Monthly Identification and Removal Trends with clearer values."""
    if monthly_data.empty:
        print("Error: No monthly data available!")
        return None

    # Convert 'Month' column to datetime format
    monthly_data['Month'] = pd.to_datetime(monthly_data['Month'])

    fig, ax = plt.subplots(figsize=(14, 7), facecolor='#f9f9f9')  # Increased figure size

    # Plot Total URLs and Removal Counts
    ax.plot(monthly_data['Month'], monthly_data['total_urls'], marker='o', linestyle='-', linewidth=2.5, markersize=10, color='#ff6b6b', label='Total URLs')
    ax.plot(monthly_data['Month'], monthly_data['removal_count'], marker='D', linestyle='-', linewidth=2.5, markersize=10, color='#4a90e2', label='Removal Count')

    # Adjust Y-axis limits
    max_y_value = max(monthly_data['total_urls'].max(), monthly_data['removal_count'].max())
    ax.set_ylim(0, max_y_value * 1.3)  # Add more padding above the highest value

    # Format X-axis labels to display every 2nd or 3rd month
    ax.set_xticks(monthly_data['Month'][::2])  # Show every alternate month
    ax.set_xticklabels(monthly_data['Month'][::2].dt.strftime('%b %Y'), rotation=45, ha='right', fontsize=12)

    # Add Annotations with larger font size and better positioning
    for i, row in monthly_data.iterrows():
        if i % 2 == 0:  # Annotate every second point
            ax.annotate(f"{row['total_urls']}", xy=(row['Month'], row['total_urls']), 
                        xytext=(0, 12), textcoords='offset points', ha='center', 
                        fontsize=10, color='#ff6b6b', fontweight='bold')

            ax.annotate(f"{row['removal_count']}", xy=(row['Month'], row['removal_count']), 
                        xytext=(0, 12), textcoords='offset points', ha='center', 
                        fontsize=10, color='#4a90e2', fontweight='bold')

    # Set Title and Labels
    ax.set_title("Monthly Identification and Removal Trends", fontsize=16, fontweight='bold', pad=20)
  
    # Add Gridlines and adjust grid styling
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.set_facecolor('#f0f7ff')

    # Add Legend
    ax.legend(facecolor='#f2f2f2', fontsize=12, loc='upper left', bbox_to_anchor=(1, 1))

    plt.tight_layout()

    # Convert plot to Base64 image for Django rendering
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close(fig)

    return base64.b64encode(img.getvalue()).decode()


#sheet wise data graohf for summary 

def create_bar_chart(data):
    """Generate sheet-wise identification & delisted bar chart"""
    sheet_summary = data.groupby('SheetName').agg(
        total_urls=('URL', 'nunique'),
        removal_count=('Status', lambda x: x.isin(['Approved', 'Removed']).sum())
    ).reset_index().sort_values(by='total_urls', ascending=False)
    # Add line breaks for long titles

    #dynamic_title = f"Sheet wise identification & Delisted for {propertyname}\nFixtures: {fixture_display}"

    fig, ax = plt.subplots(figsize=(12, 6), facecolor='#f2f2f2')
    x = np.arange(len(sheet_summary['SheetName']))
    bar_width = 0.3

    # Bar plots
    bar1 = ax.bar(x - bar_width / 2, sheet_summary['total_urls'], width=bar_width, color='#ff6b6b', label='Total URLs')
    bar2 = ax.bar(x + bar_width / 2, sheet_summary['removal_count'], width=bar_width, color='#4a90e2', label='Removal Count')

    ax.set_title("Sheet-wise Identification & Delisted", fontsize=12, fontweight='bold', pad=30)
    ax.set_yscale('log')

    # Adjust Y-axis limits to prevent overlap at top and bottom
    min_ylim = 1 if sheet_summary['removal_count'].min() > 0 else 0.5
    max_ylim = ax.get_ylim()[1] * 1.3  # Increased space above the highest bar
    ax.set_ylim(min_ylim, max_ylim)


    for bar in bar1:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height + (0.15 * height if height > 0 else 0.5), 
                f'{int(height)}', ha='center', va='bottom', fontsize=8)

    for bar in bar2:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height + (0.15 * height if height > 0 else 0.5), 
                f'{int(height)}', ha='center', va='bottom', fontsize=8)
    ax.set_facecolor('#e6e6e6')
    ax.set_ylabel('Value (log scale)', fontsize=10, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(sheet_summary['SheetName'], rotation=30, ha='right')
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    ax.legend(facecolor='#f2f2f2', fontsize=8, loc='upper left', bbox_to_anchor=(1, 1))
    plt.tight_layout()
    
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close(fig)
    
    return base64.b64encode(img.getvalue()).decode()



import numpy as np


def generate_summary_graphs(summary_data):
    print("summary dataa..", summary_data)
    graphs = []
    # Graph 1: Sheet-wise Identification & Delisted
    if 'SheetName' in summary_data.columns and 'URL' in summary_data.columns:
        print("Generating Sheet-wise Identification & Delisted Graph...")  # Debugging
        graphs.append(create_bar_chart(summary_data))
    else:
        print("not Generating Sheet-wise Identification & Delisted Graph...")  # Debugging


    # ✅ Graph 2: Monthly Identification & Removal Trends
    monthly_data = get_monthly_totals(summary_data)
    if not monthly_data.empty:
        print("Generating Monthly Trends Graph...")
        graph2 = create_monthly_totals_line_plot(monthly_data)
        if graph2:
            graphs.append(graph2)

    # ✅ Graph 2: Social Media Platform Analysis
    social_media_data = get_social_media_platform_data(summary_data)
    if not social_media_data.empty:
        graph_social_media = create_social_media_platform_bar_chart(social_media_data)
        if graph_social_media:
            graphs.append(graph_social_media)

    if 'Matchday' in summary_data.columns and 'URL' in summary_data.columns:
        matchday_data = aggregate_matchday_data(summary_data)
        if not matchday_data.empty:
            graphs.append(create_enhanced_matchday_line_plot(matchday_data))


    # Graph 1: Top 5 Properties - Infringements and Removals
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


def dashboard(request, file_path):
    """Dashboard view to display data."""
    decoded_file_path = urllib.parse.unquote(file_path)

    buttons = ['Summary', 'Enforcement_Sheet_Infringing', 'Enforcement_Sheet_Source', 
               'Telegram', 'SocialMediaPlatforms', 'Premium']

    button_filters = {
        'Summary': ['propertyname', 'fixtures',],
        'Enforcement_Sheet_Infringing': ['propertyname', 'fixtures'],
        'Enforcement_Sheet_Source': ['Source Type', 'Date'],
        'Telegram': ['Message Type', 'User ID'],
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
    for chunk in read_excel_in_chunks(decoded_file_path, sheet_name=selected_button if selected_button != 'Summary' else None, chunk_size=chunk_size):
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

            # Apply date range filter
            if selected_button == 'Summary' and start_date and end_date:
                if 'Identification Timestamp' in chunk.columns:
                    chunk['Identification Timestamp'] = pd.to_datetime(chunk['Identification Timestamp'], errors='coerce')
                    chunk = chunk[(chunk['Identification Timestamp'] >= pd.to_datetime(start_date)) & 
                                  (chunk['Identification Timestamp'] <= pd.to_datetime(end_date))]

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
                '% Removal': (summary_data.loc[summary_data['Status'].isin(['Approved', 'Removed']), 'URL'].nunique() /
                                       summary_data['URL'].nunique() * 100) if summary_data['URL'].nunique() > 0 else 0,
            }
            graph_urls.extend(generate_summary_graphs(summary_data))
        elif selected_button == 'Enforcement_Sheet_Infringing':
            widgets = {
                'Total URLs': summary_data['URL'].nunique() if 'URL' in summary_data.columns else 0,
                'Total Domains': summary_data['Domain Name'].nunique() if 'Domain Name' in summary_data.columns else 0,
            }
            graph_urls.append(generate_graph(summary_data, 'URL', 'bar'))
            graph_urls.append(generate_graph(summary_data, 'Domain Name', 'line'))
        elif selected_button == 'Enforcement_Sheet_Source':
            widgets = {
                'Total Sources': summary_data['Source Type'].nunique() if 'Source Type' in summary_data.columns else 0,
                'Earliest Date': summary_data['Date'].min() if 'Date' in summary_data.columns else 'N/A',
                'Latest Date': summary_data['Date'].max() if 'Date' in summary_data.columns else 'N/A',
            }
            graph_urls.append(generate_graph(summary_data, 'Source Type', 'bar'))
            graph_urls.append(generate_graph(summary_data, 'Date', 'line'))
        elif selected_button == 'Telegram':
            widgets = {
                'Message Types': summary_data['Message Type'].nunique() if 'Message Type' in summary_data.columns else 0,
                'Active Users': summary_data['User ID'].nunique() if 'User ID' in summary_data.columns else 0,
            }
            graph_urls.append(generate_graph(summary_data, 'Message Type', 'bar'))
            graph_urls.append(generate_graph(summary_data, 'User ID', 'line'))
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
