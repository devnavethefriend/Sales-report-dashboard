from django.shortcuts import render
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import io, base64
import matplotlib
from datetime import datetime

# Set matplotlib to non-interactive backend
matplotlib.use('Agg')

# Load Data Function
def load_data():
    # Load the CSV dataset
    data = pd.read_csv('data/Amazon Sale Report.csv', low_memory=False)
    # Convert 'Date' to datetime and clean data
    data['Date'] = pd.to_datetime(data['Date'], format='%Y-%m-%d', errors='coerce')
    data = data.dropna(subset=['Amount'])
    data = data[data['Amount'] > 0]
    return data

# Dashboard View
def sales_dashboard(request):
    # Load and analyze data
    df = load_data()

    # Calculate insights
    total_sales = df['Amount'].sum()
    total_orders = df.shape[0]
    avg_qty_per_order = df['Qty'].mean()
    
    # Distribution insights
    order_status = df['Status'].value_counts().to_dict()
    sales_by_category = df.groupby('Category')['Amount'].sum()
    fulfilment_sales = df.groupby('Fulfilment')['Amount'].sum().to_dict()
    monthly_sales = df.groupby(df['Date'].dt.to_period('M'))['Amount'].sum()
    top_states = df['ship-state'].value_counts().head(5).to_dict()

    # Generate Matplotlib visualization for Sales by Category
    fig, ax = plt.subplots()
    sales_by_category.plot(kind='bar', ax=ax, color='skyblue')
    ax.set_title('Sales by Category')
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    category_sales_plot = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    
    # Convert monthly_sales to DataFrame for compatibility with Plotly
    monthly_sales_df = monthly_sales.reset_index()
    monthly_sales_df.columns = ['Month', 'Sales']  # Rename columns for clarity

    # Generate monthly sales line plot using Plotly
    monthly_sales_fig = px.line(
        monthly_sales_df, x='Month', y='Sales',
        title='Monthly Sales Trend',
        labels={'Month': 'Month', 'Sales': 'Sales'},
        template="plotly_dark"
    )

    # Prepare data summaries
    total_sales_formatted = f"₹{total_sales:,.2f}"
    avg_qty_per_order_formatted = f"{avg_qty_per_order:.2f}"

    # Order Status Distribution Summary
    order_status_summary = "Order status breakdown for tracking shipment and delivery."

    # Configure Plotly Category Sales Chart for better visualization
    category_sales_fig = px.bar(
        x=sales_by_category.index, y=sales_by_category.values,
        title="Sales by Category",
        labels={"x": "Category", "y": "Sales"},
        template="plotly_white"
    )
    category_sales_fig.update_layout(
        showlegend=False,
        hovermode="closest",
        xaxis_title="Category",
        yaxis_title="Sales (in millions)"
    )
    category_sales_fig.update_traces(
        hoverinfo="x+y+text",  # Corrected hoverinfo value
        text=sales_by_category.values,  # Show sales values in hover text
        marker=dict(color=px.colors.qualitative.Pastel)  # Corrected color property
    )

    # Configure Plotly Monthly Sales Chart for better visualization
    monthly_sales_fig = go.Figure()
    monthly_sales_fig.add_trace(go.Scatter(
        x=monthly_sales.index.astype(str),
        y=monthly_sales.values,
        mode='lines+markers',
        line=dict(color='royalblue'),
        name='Monthly Sales'
    ))
    monthly_sales_fig.update_layout(
        title="Monthly Sales Trend",
        xaxis_title="Month",
        yaxis_title="Sales",
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=0, r=0, t=30, b=0)
    )

    # Prepare context with data, visualizations, and summaries
    context = {
        "total_sales": total_sales_formatted,
        "total_orders": total_orders,
        "avg_qty_per_order": avg_qty_per_order_formatted,
        "order_status": order_status,
        "order_status_summary": order_status_summary,
        "fulfilment_sales": fulfilment_sales,
        "top_states": top_states,
        "category_sales_plot": category_sales_plot,  # Matplotlib plot as a base64 image
        "category_sales_fig": category_sales_fig.to_html(full_html=False),  # Plotly HTML for interactive chart
        "monthly_sales_fig": monthly_sales_fig.to_html(full_html=False),  # Plotly HTML for monthly trend
    }

    # Render the template with context
    return render(request, 'dashboard/sales_dashboard.html', context)
