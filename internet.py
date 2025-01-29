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
    aggregate_matchday,
    get_social_media_platform_data,
    create_social_media_platform_bar_chart,
    create_matchday_line_plot,
    get_monthly_totals,
    create_monthly_totals_line_plot,
    create_bar_chart
)





def generate_internet_graphs(summary_data):
    print("summary dataa..", summary_data)
    graphs = []
    # Graph 1: Sheet-wise Identification & Delisted
    if 'SheetName' in summary_data.columns and 'URL' in summary_data.columns:
        graphs.append(create_bar_chart(summary_data))

    # Graph 2: Monthly Identification & Removal Trends
    monthly_data = get_monthly_totals(summary_data)
    if not monthly_data.empty:
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
    matchday_summary = aggregate_matchday(summary_data)
    if not matchday_summary.empty:
        print("📊 Matchday Summary Ready for Graph Generation!", matchday_summary)  

        matchday_graph = create_matchday_line_plot(matchday_summary)

        if matchday_graph:
            print("✅ Matchday Graph Successfully Generated!")  
            graphs.append(matchday_graph)
        else:
            print("⚠️ Matchday Graph is Empty! Check Data or Rendering")
    else:
        print("⚠️ Matchday Summary is Empty! No Graph Generated.")



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
