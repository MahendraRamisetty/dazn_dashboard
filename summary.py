import matplotlib.pyplot as plt
import io
import base64
import pandas as pd
import matplotlib.pyplot as plt
import base64
import squarify
import numpy as np


def aggregate_matchday(data):
    if 'Matchday' not in data.columns or 'URL' not in data.columns:
        return pd.DataFrame()

    data['Matchday'] = data['Matchday'].astype(str).str.strip().str.title()
    numeric_extraction = data['Matchday'].str.extract(r'(\d+)$')
    if numeric_extraction.isnull().all().item():
        return pd.DataFrame()

    matchday_summary = data.groupby('Matchday').agg(total_urls=('URL', 'count')).reset_index()
    matchday_summary['Matchday_num'] = matchday_summary['Matchday'].str.extract(r'(\d+)').astype(float)

    if matchday_summary['Matchday_num'].isnull().all():
        return pd.DataFrame()

    matchday_summary = matchday_summary.sort_values(by='Matchday_num', ascending=True).drop(columns='Matchday_num')
    return matchday_summary

def create_matchday_line_plot(matchday_data):
    """Generates Matchday Trends Line Plot."""
    if matchday_data.empty:
        print("⚠️ No Matchday data. Graph will not be created.")
        return None

    print("📊 Generating Matchday Line Plot with Data:", matchday_data)

    fig, ax = plt.subplots(figsize=(12, 6), facecolor='#f9f9f9')

    ax.plot(matchday_data['Matchday'], matchday_data['total_urls'], marker='o', markersize=8,
            color='#ff6b6b', linewidth=2.5, label='Total URLs')

    for i, row in matchday_data.iterrows():
        ax.annotate(f"{int(row['total_urls'])}", xy=(i, row['total_urls']),
                    xytext=(0, 15), textcoords='offset points', ha='center',
                    fontsize=9, color='#4a90e2', fontweight='bold')

    ax.set_xticks(range(len(matchday_data)))
    ax.set_xticklabels(matchday_data['Matchday'], rotation=45, ha='right', fontsize=10)

    max_value = matchday_data['total_urls'].max()
    ax.set_ylim(0, max_value * 1.2 if max_value > 0 else 10)

    ax.set_title("Matchday Identification and Removal Trends", fontsize=14, fontweight='bold', pad=20)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.set_facecolor('#f0f7ff')
    ax.legend(facecolor='#f2f2f2', fontsize=8, loc='upper left', bbox_to_anchor=(1, 1))

    plt.tight_layout()
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)

    base64_string = base64.b64encode(img.getvalue()).decode()
    print("✅ Base64 Graph Generated:", base64_string[:50])  # ✅ Debug: Print first 50 chars
    plt.close(fig)

    return base64_string



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


def generate_top_10_piracy_sources_graph(summary_data):
    """Generate a bar chart for the top 10 sources of piracy."""
    # Check if the column 'Source of Piracy' exists
    if 'Source of Piracy' in summary_data.columns:
        piracy_counts = summary_data['Source of Piracy'].value_counts().nlargest(10)

        if not piracy_counts.empty:
            # Creating the bar chart
            fig, ax = plt.subplots(figsize=(12, 6), facecolor='#f8f9fa')
            x = np.arange(len(piracy_counts.index))

            bars = ax.bar(piracy_counts.index, piracy_counts.values, color='#4a90e2', edgecolor='black', linewidth=0.7)

            ax.set_title("Top 10 Sources of Piracy", fontsize=16, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels(piracy_counts.index, rotation=45, ha='right', fontsize=10)

            # Add annotations on top of bars
            for bar in bars:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02 * max(piracy_counts.values),
                        f'{int(bar.get_height())}', ha='center', va='bottom', fontsize=10, color='black')

            ax.grid(axis='y', linestyle='--', alpha=0.7)
            ax.set_facecolor('#f5f5f5')  # Light gray background inside the plot area
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)

            # Save the figure to a base64-encoded image
            img = io.BytesIO()
            plt.tight_layout()
            plt.savefig(img, format='png')
            img.seek(0)
            plt.close(fig)
    
    return base64.b64encode(img.getvalue()).decode()

def generate_top_10_search_treemap(summary_data):
    """Generate a treemap for the top 10 most frequent search strings."""
    

    search_counts = summary_data['SearchString'].value_counts().nlargest(10)

    if search_counts.empty:
        print("⚠️ Warning: No search strings available for treemap. Returning placeholder.")
        return None  # ✅ Ensures a return value if there's no data

    labels = [f"{keyword}\n{count}" for keyword, count in zip(search_counts.index, search_counts.values)]
    sizes = search_counts.values

    # Create the treemap
    fig, ax = plt.subplots(figsize=(12, 6), facecolor='#f8f9fa')
    squarify.plot(sizes=sizes, label=labels, color=plt.cm.tab10.colors, alpha=0.7, ax=ax)

    ax.set_title("Top 10 Search Keywords", fontsize=16, fontweight='bold')
    ax.set_xticks([])
    ax.set_yticks([])
    ax.axis('off')

    # Convert the plot to base64
    img = io.BytesIO()  # ✅ Always initialized
    plt.tight_layout()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close(fig)

    return base64.b64encode(img.getvalue()).decode()


def generate_top_10_domains_bar_chart(summary_data):
    """Generate a bar chart for the top 10 domain names based on occurrences, highlighting delisted (Approved/Removed) cases."""

    if 'DomainName' in summary_data.columns and 'Status' in summary_data.columns:
        # Count occurrences of each domain
        domain_counts = summary_data['DomainName'].value_counts().nlargest(10)

        # Count only the "Approved" or "Removed" cases (Delisted)
        delisted_counts = (
            summary_data[summary_data['Status'].isin(['Approved', 'Removed'])]
            .groupby('DomainName')['Status']
            .count()
            .reindex(domain_counts.index, fill_value=0)
        )

        if not domain_counts.empty:
            fig, ax = plt.subplots(figsize=(12, 6), facecolor='#f8f9fa')
            x = np.arange(len(domain_counts.index))
            bar_width = 0.4

            # Bar Chart
            bars1 = ax.bar(x - bar_width / 2, domain_counts.values, width=bar_width, label='Identified', color='#ff6b6b', edgecolor='black', linewidth=0.7)
            bars2 = ax.bar(x + bar_width / 2, delisted_counts.values, width=bar_width, label='Delisted (Approved/Removed)', color='#4a90e2', edgecolor='black', linewidth=0.7)

            # Chart labels
            ax.set_title("Top 10 Domains - Identified vs Delisted", fontsize=16, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels(domain_counts.index, rotation=45, ha='right', fontsize=10)
            # Add value annotations
            for bar in bars1:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2, f'{int(bar.get_height())}', ha='center', va='bottom', fontsize=10, color='black')
            for bar in bars2:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2, f'{int(bar.get_height())}', ha='center', va='bottom', fontsize=10, color='black')

            ax.grid(axis='y', linestyle='--', alpha=0.7)
            ax.set_facecolor('#f5f5f5')  # Light gray background inside the plot area
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.legend()

            # Convert the plot to base64
            img = io.BytesIO()
            plt.tight_layout()
            plt.savefig(img, format='png')
            img.seek(0)
            plt.close(fig)
    
    return base64.b64encode(img.getvalue()).decode()








