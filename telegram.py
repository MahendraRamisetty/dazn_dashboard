import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from matplotlib.backends.backend_pdf import PdfPages
import io
from datetime import datetime
import plotly.express as px
import pandas as pd
import plotly.io as pio
import base64
import io

# ✅ Function to calculate Telegram summary
def calculate_telegram_summary(data):
    """Calculate key metrics for Telegram data summary."""
    summary = {
        "total_properties": data['propertyname'].nunique(),
        "total_fixtures": data['fixtures'].nunique(),
        "total_infringements": data['URL'].nunique(),
        "total_telegram_channels": data['DomainName'].nunique(),
        "suspended_channels": data[data['ChannelStatus'].isin(['Suspended'])]['URL'].nunique(),
        "views_incurred": pd.to_numeric(data['views'], errors='coerce').sum(),
        "total_subscribers": pd.to_numeric(data['channelsubscribers'], errors='coerce').sum(),
        "impacted_subscribers": pd.to_numeric(
            data[data['Status'].isin(['Approved', 'Removed'])]['channelsubscribers'], errors='coerce'
        ).sum(),
    }
    
    approved_removed_count = data[data['Status'].isin(['Approved', 'Removed'])]['URL'].nunique()
    summary["removal_percentage"] = (
        (approved_removed_count / summary["total_infringements"]) * 100 if summary["total_infringements"] > 0 else 0
    )

    return summary


# ✅ Function to generate top 5 properties based on total URLs
def get_top_telegram_properties(data):

    telegram = data[data['SheetName'] == 'telegram']  # Use lowercase

    """Retrieve top 5 Telegram properties based on infringements."""
    summary = (
        telegram.groupby(['propertyname', 'URL'])
        .agg(removal_flag=('Status', lambda x: any(x.isin(['Approved', 'Removed']))))
        .reset_index()
        .groupby('propertyname')
        .agg(total_urls=('URL', 'count'), removal_count=('removal_flag', 'sum'))
        .reset_index()
        .sort_values(by='total_urls', ascending=False)
    )
    
    return summary.nlargest(5, 'total_urls')[['propertyname', 'total_urls', 'removal_count']]

# Function to create a grouped bar chart for the top 5 property
def create_top_property_bar_chart(top_fixtures):
    fig, ax = plt.subplots(figsize=(8, 5), facecolor='#f2f2f2')
    x = np.arange(len(top_fixtures['propertyname']))
    bar_width = 0.3

    bar1 = ax.bar(x - bar_width / 2, top_fixtures['total_urls'], width=bar_width, label='Total URLs', color='#ff6b6b')
    bar2 = ax.bar(x + bar_width / 2, top_fixtures['removal_count'], width=bar_width, label='Removal Count', color='#4a90e2')

    ax.set_title("Top 5 properties Identification and Removal", fontsize=12, fontweight='bold', pad=20)
    ax.set_ylim(0, max(top_fixtures['total_urls'].max(), top_fixtures['removal_count'].max()) * 1.15)
    ax.set_ylabel('Value', fontsize=10, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(top_fixtures['propertyname'], rotation=45, ha='right')
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.legend(facecolor='#f2f2f2', fontsize=8, loc='upper right')
    
    for bar in bar1:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 10, int(bar.get_height()), ha='center', va='bottom', fontsize=8)
    for bar in bar2:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 10, int(bar.get_height()), ha='center', va='bottom', fontsize=8)

    ax.set_facecolor('#e6e6e6')

  

    ax.legend(facecolor='#f2f2f2', fontsize=8, loc='upper left', bbox_to_anchor=(1, 1))
    plt.tight_layout()
    
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close(fig)
    return base64.b64encode(img.getvalue()).decode()



# ✅ Function to generate Telegram monthly trends
def telegram_monthly_totals(data):
    """Aggregate data to generate monthly summary for Telegram."""
    telegram_data = data[data['SheetName'] == 'telegram']
    telegram_data['Identification Timestamp'] = pd.to_datetime(telegram_data['Identification Timestamp'])
    telegram_data['Month'] = telegram_data['Identification Timestamp'].dt.to_period('M')

    summary = (
        telegram_data.groupby('Month')
        .agg(total_urls=('URL', 'count'), removal_count=('Status', lambda x: x.isin(['Approved', 'Removed']).sum()))
        .reset_index()
        .sort_values(by='total_urls', ascending=False)
    )

    summary['Month'] = summary['Month'].dt.to_timestamp()
    
    return summary


# ✅ Function to create a bar chart for Telegram top 5 fixtures
def create_telegram_top_fixtures_bar_chart(data):
    """Generate a bar chart for top 5 Telegram fixtures by number of infringements."""
    telegram_data = data[data['SheetName'] == 'telegram']
    
    summary = (
        telegram_data.groupby(['fixtures', 'URL'])
        .agg(removal_flag=('Status', lambda x: any(x.isin(['Approved', 'Removed']))))
        .reset_index()
        .groupby('fixtures')
        .agg(total_urls=('URL', 'count'))
        .reset_index()
        .sort_values(by='total_urls', ascending=False)
    )
    
    top_fixtures = summary.nlargest(5, 'total_urls')

    fig = px.bar(
        top_fixtures,
        y='fixtures',
        x='total_urls',
        orientation='h',
        title="Top 5 Telegram Fixtures – Number of Infringements",
        text='total_urls'
    )

    fig.update_traces(marker_color='#4a90e2', textposition='outside')
    fig.update_layout(
        plot_bgcolor='#f9f9f9',
        xaxis=dict(gridcolor='rgba(0, 0, 0, 0.2)', gridwidth=1, showline=False),
        yaxis=dict(title=None, categoryorder='total ascending'),
        title=dict(font=dict(size=18, color='#333'), x=0.5, xanchor='center'),
        margin=dict(l=100, r=40, t=80, b=40),
    )

    return fig


# ✅ Function to generate a pie chart for Telegram channel types
def create_telegram_channel_type_pie_chart(data):
    """Generate a pie chart for Telegram channel types."""
    telegram_data = data[data['SheetName'] == 'Telegram']
    valid_channel_types = ['Public', 'Private']
    filtered_data = telegram_data[telegram_data['ChannelType'].isin(valid_channel_types)]
    
    summary = filtered_data['ChannelType'].value_counts().reset_index()
    summary.columns = ['ChannelType', 'count']

    fig = px.pie(
        summary,
        names='ChannelType',
        values='count',
        title="Telegram Channel - Type Distribution",
        hole=0.4,
    )
    
    fig.update_traces(textinfo='label+percent')
    fig.update_layout(margin=dict(l=40, r=40, t=80, b=40), plot_bgcolor='#f9f9f9')

    return fig

#fucntio to get telegram summary
def get_telegram_platform_data(data):

    platform = data[data['SheetName'] == 'Telegram']
    # Calculate total URLs, count of 'Removed' and 'Approved' statuses for each DomainName
    Telegram_summary = platform.groupby('DomainName').agg(
        total_urls=('URL', 'count'),
        removed_count=('Status', lambda x: x.isin(['Approved', 'Removed']).sum()),
    ).reset_index().sort_values(by='total_urls', ascending=False)
    
    return Telegram_summary



def get_telegram_top_fixtures(data):
    """Retrieve top 5 Telegram fixtures based on total URLs."""

    # ✅ Aggregate fixture data
    fixture_summary = (
        data.groupby(['fixtures', 'URL'])
        .agg(removal_flag=('Status', lambda x: any(x.str.lower().isin(['approved', 'removed']))))
        .reset_index()
        .groupby('fixtures')
        .agg(total_urls=('URL', 'count'))
        .reset_index()
        .sort_values(by='total_urls', ascending=False)
    )

    if fixture_summary.empty:
        print("🚨 Warning: Fixture summary returned empty! Check column names and values.")
    
    return fixture_summary.nlargest(5, 'total_urls')[['fixtures', 'total_urls']]

def create_telegram_top_fixtures_bar_chart(top_fixtures):
    """Generate a Base64-encoded bar chart for top 5 Telegram fixtures based on infringements."""

    # ✅ Sorting Data
    top_fixtures = top_fixtures.sort_values(by='total_urls', ascending=True)
    max_value = top_fixtures['total_urls'].max()
    buffer = max_value * 0.2  # 20% buffer for extended x-axis
    x_axis_limit = max_value + buffer
    
    # ✅ Create the Plot
    fig = px.bar(
        top_fixtures,
        y='fixtures',
        x='total_urls',
        orientation='h',
        title="Top 5 Telegram Fixtures – Basis No. of Infringements",
        text='total_urls',
    )
    
    # ✅ Customization
    fig.update_traces(marker_color='#4a90e2', textposition='outside')
    fig.update_layout(
        plot_bgcolor='#f9f9f9',
        xaxis=dict(
            gridcolor='rgba(0, 0, 0, 0.2)',
            gridwidth=1,
            showline=False,
            range=[0, x_axis_limit]
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
    
    # ✅ Convert Plotly figure to PNG bytes
    img_bytes = pio.to_image(fig, format="png")

    # Convert image to Base64
    base64_string = base64.b64encode(img_bytes).decode()

    return base64_string



def telegram_domains_by_subscribers(data, selected_fixture=None):
    # Filter data for the "Telegram" sheet
    
    # Apply fixture filtering if a specific fixture is selected
    if selected_fixture:
        data = data['fixtures'] == selected_fixture
    
    # Convert 'channelsubscribers' to numeric, forcing errors to NaN
    data['channelsubscribers'] = pd.to_numeric(data['channelsubscribers'], errors='coerce')
    
    # Fill NaN values with 0
    data['channelsubscribers'].fillna(0, inplace=True)
    
    # Group by 'DomainName' and sum the 'channelsubscribers'
    domain_summary = data.groupby('DomainName').agg(
        total_subscribers=('channelsubscribers', 'sum')
    ).reset_index()
    
    # Sort by total subscribers and select the top 10
    top_10_domains = domain_summary.nlargest(10, 'total_subscribers')
    
    return top_10_domains



def create_treemap_chart_telegram(top_10_data):
    
    fig = px.treemap(
        top_10_data,
        path=['DomainName'],  # Use 'DomainName' as labels
        values='total_subscribers',  # Size of rectangles
        title="Top 10 Telegram Channels - Based on Subscribers",
    )
    
    # Customize the chart with a vibrant color scale
    fig.update_traces(
        marker=dict(colorscale='Viridis'),
        textinfo='label+value',  # Use a vibrant colorscale and display value with label
    )
    
    # Adjust layout for better appearance
    fig.update_layout(
        margin=dict(l=50, r=50, t=70, b=50),
        title=dict(font=dict(size=24), x=0.5, xanchor='center'),
        height=450  # Adjust height for visibility
    )

    # Convert Plotly figure to PNG image
    img_bytes = pio.to_image(fig, format="png")

    # Convert image to Base64
    base64_string = base64.b64encode(img_bytes).decode()

    return base64_string



## trends grapgh for both sumamry and telgram 


def aggregate_matchday_data(data):

    """
    Aggregates data to calculate total URLs and sorts Matchday properly
    in ascending numerical order (e.g., Matchday 1, Matchday 2, ..., Matchday 11).

    """

    # Normalize Matchday column
    data['Matchday'] = data['Matchday'].str.strip().str.title()  # Remove extra spaces, normalize capitalization

    # Aggregate data
    matchday_summary = data.groupby('Matchday').agg(
        total_urls=('URL', 'count')
    ).reset_index()

    # Extract numerical part from Matchday and sort by it
    
    matchday_summary['Matchday_num'] = matchday_summary['Matchday'].str.extract(r'(\d+)$').astype(int)
    matchday_summary = matchday_summary.sort_values(by='Matchday_num', ascending=True)  # Sort in ascending order

    # Drop the temporary Matchday_num column
    matchday_summary = matchday_summary.drop(columns='Matchday_num')

    # Reset index after sorting to ensure correct indexing
    matchday_summary = matchday_summary.reset_index(drop=True)

    print(matchday_summary)

    return matchday_summary




def create_enhanced_matchday_line_plot(matchday_data):
     
    # Ensure 'Matchday' is sorted in ascending numeric order
    matchday_data['Matchday_num'] = matchday_data['Matchday'].str.extract(r'(\d+)$').astype(int)
    matchday_data = matchday_data.sort_values(by='Matchday_num', ascending=True).drop(columns='Matchday_num')

    # Create the figure and axis
    fig, ax = plt.subplots(figsize=(12, 6), facecolor='#f9f9f9')

    # Plot lines with markers
    ax.plot(matchday_data['Matchday'], matchday_data['total_urls'], marker='o', markersize=8,
            color='#ff6b6b', linewidth=2.5, label='Total URLs')

    # Annotate data points outside the graph
    for i, row in matchday_data.iterrows():
        # Position the labels outside the graph layout
        ax.annotate(f"{int(row['total_urls'])}",
                    xy=(i, row['total_urls']),  # Data point position
                    xytext=(0, 15),  # Offset (x=0, y=15)
                    textcoords='offset points',
                    ha='center', fontsize=9, color='#4a90e2', fontweight='bold')

    # Title and labels
    ax.set_title("Matchday Identification and Removal Trends", fontsize=14, fontweight='bold', pad=20)


    # Customize x-ticks and rotate labels
    ax.set_xticks(range(len(matchday_data['Matchday'])))
    ax.set_xticklabels(matchday_data['Matchday'], rotation=45, ha='right', fontsize=10)

    # Adjust y-limits to add padding above the highest value
    max_y_value = matchday_data['total_urls'].max()
    ax.set_ylim(0, max_y_value * 1.2)  # Add 20% padding above the highest value

    # Grid and background styling
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.set_facecolor('#f0f7ff')

    # Legend
    ax.legend(facecolor='#f2f2f2', fontsize=8, loc='upper left', bbox_to_anchor=(1, 1))

    # Ensure the layout is adjusted to accommodate the labels
    plt.tight_layout()
    return fig



#mothly grapgh for telegram page 
#Function to get monthly totals

def telegram_monthly_totals(data):
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


def telegram_monthly_totals_line_plot(monthly_data):
    # Convert 'Month' column to datetime if it's not already
    monthly_data['Month'] = pd.to_datetime(monthly_data['Month'])

    # Group data by month and sum total URLs and removal counts
    monthly_data = monthly_data.resample('M', on='Month').sum()
    monthly_data.index = monthly_data.index.strftime('%b %Y')  # Format to show "Month Year"

    fig, ax = plt.subplots(figsize=(12, 6), facecolor='#f9f9f9')

    # Plotting total URLs and removal counts with enhancements
    ax.plot(monthly_data.index, monthly_data['total_urls'], marker='o', color='#ff6b6b', linewidth=2.5,
            markersize=8, label='Total URLs')
    ax.plot(monthly_data.index, monthly_data['removal_count'], marker='D', color='#4a90e2', linewidth=2.5,
            markersize=8, label='Removal Count')

    # Adjust y-limits to add padding above the highest value
    max_y_value = max(monthly_data['total_urls'].max(), monthly_data['removal_count'].max())
    ax.set_ylim(0, max_y_value * 1.2)  # Add 20% padding above the highest value

    # Add data point labels with adjusted positions and styling for readability
    for i, (month, row) in enumerate(monthly_data.iterrows()):
        ax.annotate(f"{int(row['total_urls'])}",
                    xy=(i, row['total_urls']),  # Data point position
                    xytext=(0, 10),  # Offset (x=0, y=10)
                    textcoords='offset points',
                    ha='center', fontsize=9, color='#ff6b6b', fontweight='bold')
        ax.annotate(f"{int(row['removal_count'])}",
                    xy=(i, row['removal_count']),  # Data point position
                    xytext=(0, 10),  # Offset (x=0, y=10)
                    textcoords='offset points',
                    ha='center', fontsize=9, color='#4a90e2', fontweight='bold')

    # Enhanced title and axis labels
    ax.set_title("Overall piracy Identification and Removal", fontsize=10, fontweight='bold', pad=20)
    ax.set_xlabel('Month', fontsize=12, fontweight='bold')
    ax.set_ylabel('Count', fontsize=12, fontweight='bold')

    # Set custom x-tick labels to show every month and rotate for clarity
    ax.set_xticks(range(len(monthly_data.index)))
    ax.set_xticklabels(monthly_data.index, rotation=45, ha='right', fontsize=10)

    # Add gridlines and background gradient for a cleaner look
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.set_facecolor('#e6e6e6')

    # Add legend with updated font size
    ax.legend(facecolor='#f2f2f2', fontsize=8, loc='upper left', bbox_to_anchor=(1, 1))

    # Ensure the layout is adjusted to accommodate the labels\

    plt.tight_layout()
    
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close(fig)
    return base64.b64encode(img.getvalue()).decode()
 




# Function to get top 5 fixtures based on summed "views" in the "Telegram" sheet
def top_fixtures_donut_chart(data):
    # Filter data for the "Telegram" sheet only
    
    # Convert "views" column to numeric and drop invalid rows
    data['views'] = pd.to_numeric(data['views'], errors='coerce')
    data =  data.dropna(subset=['views'])
    
    # Group by 'fixtures' and sum the 'views'
    fixture_summary = data.groupby('fixtures', as_index=False)['views'].sum()
    
    # Sort fixtures by summed "views" in descending order
    fixture_summary = fixture_summary.sort_values(by='views', ascending=False)
    
    # Select top 5 fixtures
    return fixture_summary.nlargest(5, 'views')[['fixtures', 'views']]


# Function to create a donut chart for the top 5 fixtures based on views
def top_fixtures_graph_donut_chart(top_fixtures):
    # Sort data by views in descending order (optional for visual consistency)
    top_fixtures = top_fixtures.sort_values(by='views', ascending=False)
    
    # Create the donut chart
    fig = px.pie(
        top_fixtures,
        names='fixtures',  # Labels for the chart
        values='views',  # Values to determine the size of the slices
        title="Top 5 Fixtures – Based on Views",
        hole=0.4,  # Creates a donut chart
    )
    
    # Customize the chart
    fig.update_traces(
        textinfo='label+percent',  # Display label and percentage on slices
        marker=dict(line=dict(color='#000000', width=2)),  # Black border for better contrast
    )
    
    fig.update_layout(
        title=dict(
            text="Top 5 fixtures – Basis Number of Views",
            font=dict(size=18, color='#333'),
            x=0.5,  # Center the title
            xanchor='center'
        ),
        margin=dict(l=40, r=150, t=80, b=40),  # Adjust margins to make space for the legend
        plot_bgcolor='#f9f9f9',  # Light gray background color
    )
    
    img_bytes = pio.to_image(fig, format="png")

    # Convert image to Base64
    base64_string = base64.b64encode(img_bytes).decode()

    return base64_string


def create_channel_type_pie_chart(data):
    # Filter data for the "Telegram" sheet only
    
    # Retain only valid values in the "channeltype" column (e.g., "Public" or "Private")
    valid_channel_types = ['Public', 'Private']
    filtered_data = data[data['ChannelType'].isin(valid_channel_types)]
    
    # Group by 'channeltype' and count occurrences
    channeltype_summary = filtered_data['ChannelType'].value_counts().reset_index()
    channeltype_summary.columns = ['ChannelType', 'count']

    # Create the pie chart
    fig = px.pie(
        channeltype_summary,
        names='ChannelType',  # Values for the pie slices
        values='count',  # Size of each slice
        title="Telegram Channel - Type of Channel",
        hole=0.4,  # Donut chart style
    )
    
    # Customize the chart
    fig.update_traces(
        textinfo='label+percent',  # Display label and percentage
        marker=dict(line=dict(color='#000000', width=1.5))  # Add borders around slices
    )
    
    fig.update_layout(
        title=dict(
            text="Telegram Channel - Type of Channel",
            font=dict(size=18, color='#333'),
            x=0.5,  # Center the title
            xanchor='center'
        ),
        legend=dict(
            orientation="v",  # Vertical legend
            y=0.5,
            x=1.1,  # Place legend on the right side
            title="ChannelType",
        ),
        margin=dict(l=40, r=40, t=80, b=40),  # Adjust margins for spacing
        plot_bgcolor='#f9f9f9',  # Light gray background color
    )
        # ✅ Convert Plotly figure to PNG bytes
    img_bytes = pio.to_image(fig, format="png")

    # Convert image to Base64
    base64_string = base64.b64encode(img_bytes).decode()

    return base64_string



