import plotly.io as pio
import matplotlib.pyplot as plt
import io
import base64
import pandas as pd
import matplotlib.pyplot as plt
import base64
import plotly.express as px
import squarify
import numpy as np
import plotly.graph_objects as go
import base64
import io



# ✅ Function to generate top 5 properties based on total URLs
def Mobile_properties_data(data):

    """Retrieve top 5 Telegram properties based on infringements."""
    summary = (
        data.groupby(['Platform', 'URL'])
        .agg(removal_flag=('Status', lambda x: any(x.isin(['Approved', 'Removed']))))
        .reset_index()
        .groupby('Platform')
        .agg(total_urls=('URL', 'count'), removal_count=('removal_flag', 'sum'))
        .reset_index()
        .sort_values(by='total_urls', ascending=False)
    )
    
    return summary.nlargest(5, 'total_urls')[['Platform', 'total_urls', 'removal_count']]


def MobileApp_bar_chart(top_fixtures):
    """Generate an interactive grouped bar chart with hover tooltips."""
    
    fig = go.Figure()

    # Add Total URLs bar with hover tooltips
    fig.add_trace(go.Bar(
        x=top_fixtures['Platform'],
        y=top_fixtures['total_urls'],
        name='Total URLs',
        marker_color='#ff6b6b',
        text=[f"Total URLs: {val}" for val in top_fixtures['total_urls']],  # Custom hover text
        hoverinfo="text+y"  # Display text and Y-value on hover
    ))

    # Add Removal Count bar with hover tooltips
    fig.add_trace(go.Bar(
        x=top_fixtures['Platform'],
        y=top_fixtures['removal_count'],
        name='Removal Count',
        marker_color='#4a90e2',
        text=[f"Removal Count: {val}" for val in top_fixtures['removal_count']],  # Custom hover text
        hoverinfo="text+y"  # Display text and Y-value on hover
    ))

    # Update layout
    fig.update_layout(
        title="Top 5 App Stores - Identification & Removal",
        yaxis_title="Count",
        barmode='group',  # Grouped bars instead of stacked
        template='plotly_white',  # Use a clean template
        hovermode="x unified",  # Shows values for both bars when hovering
        legend=dict(
            x=1, y=1, bgcolor='rgba(255,255,255,0.5)', bordercolor='Black', borderwidth=1
        )
    )

    # Convert Plotly figure to base64 image
    img_bytes = fig.to_image(format="png")
    img_base64 = base64.b64encode(img_bytes).decode()

    return img_base64  # Return base64-encoded image for Django rendering





def mobile_monthly_totals(data):
    # Filter data for the specified sheet

    
    # Ensure 'Identification Timestamp' is in datetime format
    data['Identification Timestamp'] = pd.to_datetime(data['Identification Timestamp'])
    
    # Extract the month from the timestamp
    data['Month'] = data['Identification Timestamp'].dt.to_period('M')
    
    # Group and aggregate the data
    monthly_summary = data.groupby('Month').agg(
        total_urls=('URL', 'count'),
        removal_count=('Status', lambda x: x.isin(['Approved', 'Removed']).sum())
    ).reset_index().sort_values(by='total_urls', ascending=False)
    
    # Convert 'Month' back to a timestamp
    monthly_summary['Month'] = monthly_summary['Month'].dt.to_timestamp()
    
    return monthly_summary



def mobile_monthly_totals_line_plot(monthly_data):
    """Generate an interactive line chart for monthly total URLs and removal counts with improved label positioning."""

    # Convert 'Month' column to datetime if it's not already
    monthly_data['Month'] = pd.to_datetime(monthly_data['Month'])

    # Group data by month and sum total URLs and removal counts
    monthly_data = monthly_data.resample('M', on='Month').sum()

    # Format month labels for better readability
    monthly_data.index = monthly_data.index.strftime('%b %Y')

    fig, ax = plt.subplots(figsize=(12, 6), facecolor='#f9f9f9')

    # Plot total URLs and removal counts
    ax.plot(monthly_data.index, monthly_data['total_urls'], marker='o', color='#ff6b6b', linewidth=2.5,
            markersize=8, label='Total URLs')
    ax.plot(monthly_data.index, monthly_data['removal_count'], marker='D', color='#4a90e2', linewidth=2.5,
            markersize=8, label='Removal Count')

    # Adjust y-limits to add padding above the highest value
    max_y_value = max(monthly_data['total_urls'].max(), monthly_data['removal_count'].max())
    ax.set_ylim(0, max_y_value * 1.3)  # Add 30% padding above the highest value

    # Add data point labels with dynamic positioning to avoid overlap
    for i, (month, row) in enumerate(monthly_data.iterrows()):
        # Adjust position dynamically based on value to avoid collisions
        offset_urls = 20 if row['total_urls'] >= row['removal_count'] else -20
        offset_removal = -20 if row['total_urls'] >= row['removal_count'] else 20

        ax.annotate(f"{int(row['total_urls'])}",
                    xy=(i, row['total_urls']), 
                    xytext=(0, offset_urls),  
                    textcoords='offset points',
                    ha='center', fontsize=9, color='#ff6b6b', fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.3", edgecolor='#ff6b6b', facecolor='white'))

        ax.annotate(f"{int(row['removal_count'])}",
                    xy=(i, row['removal_count']),
                    xytext=(0, offset_removal),  
                    textcoords='offset points',
                    ha='center', fontsize=9, color='#4a90e2', fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.3", edgecolor='#4a90e2', facecolor='white'))

    # Title and axis labels
    ax.set_title("Overall Piracy Identification and Removal", fontsize=12, fontweight='bold', pad=20)
    ax.set_xlabel("Month", fontsize=10)
    ax.set_ylabel("Count", fontsize=10)

    # Set custom x-tick labels
    ax.set_xticks(range(len(monthly_data.index)))
    ax.set_xticklabels(monthly_data.index, rotation=45, ha='right', fontsize=10)

    # Add gridlines and background
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.set_facecolor('#e6e6e6')

    # Add legend
    ax.legend(facecolor='#f2f2f2', fontsize=9, loc='upper left', bbox_to_anchor=(1, 1))

    plt.tight_layout()
    
    # Convert the plot to a base64 encoded string for rendering in Django
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close(fig)

    return base64.b64encode(img.getvalue()).decode()





def Mobile_top_apps_by_downloads(data):
    """
    Retrieve the top 5 mobile apps based on the highest number of downloads.
    """
    # Ensure 'AppDownloads' column is numeric
    data['AppDownloads'] = pd.to_numeric(data['AppDownloads'], errors='coerce')

    # Aggregate and sort the data to get top 5 apps based on downloads
    top_apps = (
        data.groupby('DomainName')
        .agg(total_downloads=('AppDownloads', 'sum'))
        .reset_index()
        .sort_values(by='total_downloads', ascending=False)
        .head(5)
    )

    if top_apps.empty:
        print("Warning: No data found in the AppDownloads column or incorrect column names.")
    
    return top_apps[['DomainName', 'total_downloads']]

def create_mobile_top_apps_bar_chart(top_apps):
    """
    Generate a Base64-encoded bar chart for top 5 mobile apps based on downloads.
    """
    # Sort by total downloads in ascending order for better visualization
    top_apps = top_apps.sort_values(by='total_downloads', ascending=True)

    max_value = top_apps['total_downloads'].max()
    buffer = max_value * 0.2  # 20% buffer for extended x-axis
    x_axis_limit = max_value + buffer

    # Create the horizontal bar chart
    fig = px.bar(
        top_apps,
        y='DomainName',
        x='total_downloads',
        orientation='h',
        title="Top 5 Mobile Apps - Basis No of Downloads",
        text='total_downloads'
    )

    # Customize the chart
    fig.update_traces(marker_color='#4a90e2', textposition='outside')
    fig.update_layout(
        plot_bgcolor='#f9f9f9',
        xaxis=dict(
            gridcolor='rgba(0, 0, 0, 0.2)',
            showline=False,
            range=[0, x_axis_limit],
            title="No of Downloads",
        ),
        yaxis=dict(
            title=None,
            categoryorder='total ascending'
        ),
        title=dict(
            font=dict(size=18, color='#333'),
            x=0.5,
            xanchor='center'
        ),
        margin=dict(l=100, r=40, t=80, b=40),
    )

    # Convert Plotly figure to PNG bytes
    img_bytes = pio.to_image(fig, format="png")

    # Convert image to Base64
    base64_string = base64.b64encode(img_bytes).decode()

    return base64_string

def mobile_aggregate_matchday(data):
    if 'Matchday' not in data.columns or 'URL' not in data.columns:
        return pd.DataFrame()

    # ✅ Standardize the Matchday column
    data['Matchday'] = data['Matchday'].astype(str).str.strip().str.title()
    
    # ✅ Extract numerical part from Matchday column
    data['Matchday_num'] = pd.to_numeric(data['Matchday'].str.extract(r'(\d+)$')[0], errors='coerce')

    print("Matchday Counts:\n", data['Matchday'].value_counts())

    # ✅ Check if numeric extraction was successful
    if data['Matchday_num'].isnull().all():
        return pd.DataFrame()
    
    # ✅ Aggregate data correctly by summing up occurrences
    matchday_summary = data.groupby(['Matchday', 'Matchday_num']).agg(total_urls=('URL', 'count')).reset_index()

    matchday_summary = matchday_summary.sort_values(by='Matchday_num', ascending=True).drop(columns='Matchday_num')

    print("Aggregated Data:\n", matchday_summary)

    # ✅ Sort data by total_urls (High to Low) for graph order
    matchday_summary = matchday_summary.sort_values(by='total_urls', ascending=False)

    return matchday_summary



def mobile_create_matchday_line_plot(matchday_data):
    """Generates Corrected Matchday Trends Line Plot in Numerical Order."""
    if matchday_data.empty:
        print("⚠️ No Matchday data. Graph will not be created.")
        return None

    # ✅ Debugging Step: Print the matchday data to verify values before plotting
    print("Matchday Data for Plot:\n", matchday_data)

    fig, ax = plt.subplots(figsize=(12, 6), facecolor='#f9f9f9')

    # ✅ Extract and Sort Matchday Numerically
    matchday_data['Matchday_num'] = matchday_data['Matchday'].str.extract(r'(\d+)$')[0].astype(int)
    matchday_data = matchday_data.sort_values(by='Matchday_num', ascending=True).drop(columns='Matchday_num')

    # ✅ Plot total URLs in correct matchday order
    ax.plot(matchday_data['Matchday'], matchday_data['total_urls'], marker='o', markersize=8,
            color='#ff6b6b', linewidth=2.5, label='Total URLs')

    # ✅ Fix incorrect xy coordinates in annotations
    for i, row in matchday_data.iterrows():
        ax.annotate(f"{int(row['total_urls'])}", 
                    xy=(row['Matchday'], row['total_urls']),  # Correct X value
                    xytext=(0, 10),  # Offset to avoid overlap
                    textcoords='offset points', 
                    ha='center', fontsize=10, 
                    color='#4a90e2', fontweight='bold')

    # ✅ Ensure correct x-axis ordering
    ax.set_xticks(range(len(matchday_data)))
    ax.set_xticklabels(matchday_data['Matchday'], rotation=45, ha='right', fontsize=10)

    max_value = matchday_data['total_urls'].max()
    ax.set_ylim(0, max_value * 1.3 if max_value > 0 else 10)

    ax.set_title("Matchday Identification and Removal Trends", fontsize=14, fontweight='bold', pad=20)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.set_facecolor('#f0f7ff')
    ax.legend(facecolor='#f2f2f2', fontsize=10, loc='upper left', bbox_to_anchor=(1, 1))

    plt.tight_layout()

    # Convert plot to base64 for rendering in web apps
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)

    base64_string = base64.b64encode(img.getvalue()).decode()
    plt.close(fig)
    return base64_string
