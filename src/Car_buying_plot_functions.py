import pandas as pd
import plotly.express as px
import numpy as np
import plotly.graph_objects as go

def price_vs_age_plot_scatter(df_filtered, brand_name, model_name):
    """
    Generate a scatter plot of vehicle price vs. vehicle age for a specific brand/model,
    with marker color representing percentage deviation from predicted price,
    and marker size representing horsepower. Includes dynamic legend for HP.
    Clicking points enables redirection via Dash clickData.
    """
    required_columns = {
        'model', 'brand', 'vehicle_age', 'price', 'power_HP',
        'predicted_price', 'URL', 'fuel'
    }
    if not required_columns.issubset(df_filtered.columns):
        raise ValueError(f"Input DataFrame must include: {required_columns}")

    # Compute % deviation
    if 'pct_diff' not in df_filtered.columns or df_filtered['pct_diff'].isna().all():
        df_filtered['pct_diff'] = (
            (df_filtered['predicted_price'] - df_filtered['price']) / df_filtered['predicted_price']
        ) * 100

    df_sub = df_filtered[df_filtered['model'] == model_name]

    if df_sub.empty:
        return go.Figure().update_layout(title="No listings found for selected model")

    abs_max = max(abs(df_sub['pct_diff'].min()), abs(df_sub['pct_diff'].max()))
    vmin, vmax = -abs_max, abs_max

    symbol_map = {
        fuel: i for i, fuel in enumerate(df_sub['fuel'].unique())
    }

    fig = go.Figure()

    for fuel, fuel_df in df_sub.groupby('fuel'):
        fig.add_trace(go.Scatter(
            x=fuel_df['vehicle_age'],
            y=fuel_df['price'],
            mode='markers',
            name=fuel,
            customdata=np.stack([
                fuel_df['URL'], fuel_df['fuel'], fuel_df['price'],
                fuel_df['predicted_price'], fuel_df['pct_diff']
            ], axis=-1),
            marker=dict(
                size=fuel_df['power_HP'],
                sizemode='area',
                sizeref=2.*max(fuel_df['power_HP'])/(12.**2),
                sizemin=2,
                color=fuel_df['pct_diff'],
                colorscale='RdBu',
                cmin=vmin,
                cmax=vmax,
                colorbar=dict(
                    title="Deviation from predicted price",
                    title_side="right",
                    title_font=dict(size=14),
                    tickvals=[vmin, 0, vmax],
                    ticktext=[f"{int(vmin)}%", "0%", f"{int(vmax)}%"],
                    lenmode="pixels",
                    len=450,
                    thickness=18
                ),
                line=dict(color='black', width=1),
                symbol=symbol_map[fuel]
            ),
            hovertemplate=(
                "Age: %{x} months<br>"
                "Price: €%{customdata[2]:,.0f}<br>"
                "Predicted: €%{customdata[3]:,.0f}<br>"
                "Deviation: %{customdata[4]:.1f}%<br>"
                "Fuel: %{customdata[1]}<br>"
                "Power: %{marker.size} HP<br>"
                "<extra></extra>"
            )
        ))

    fig.update_layout(
    template='plotly_white',
    title=dict(
        text=f"Vehicles for sale: {brand_name} {model_name}",
        x=0,
        xanchor='left',
        pad=dict(t=10),
        font=dict(size=16)
    ),
    margin=dict(t=60, l=50, r=20, b=80),
    xaxis=dict(
        title='Vehicle Age (months)',
        showline=True, linecolor='gray', linewidth=1, mirror=True, showgrid=True
    ),
    yaxis=dict(
        title='Price (€)',
        showline=True, linecolor='gray', linewidth=1, mirror=True, showgrid=True
    ),
    legend=dict(
    title=dict(
        text='<b>Fuel type</b>',
        font=dict(size=12),
        side='top'  # This keeps it visually above the legend entries
    ),
    x=1,
    y=1,
    xanchor='right',
    yanchor='top',
    bgcolor='rgba(255,255,255,0.7)',
    bordercolor='gray',
    borderwidth=1,
    font=dict(size=12)
)

)


    return fig






# def deviation_histogram_colored(df_filtered):
#     """
#     Create a vertical histogram showing the distribution of percentage deviation (pct_diff)
#     using a pre-filtered DataFrame for a specific car model. Bars are color-coded by bin center.
#     """
#     required_columns = {'price', 'predicted_price'}
#     if not required_columns.issubset(df_filtered.columns):
#         raise ValueError(f"DataFrame must include columns: {required_columns}")

#     # Calculate pct_diff if not present
#     if 'pct_diff' not in df_filtered.columns or df_filtered['pct_diff'].isna().all():
#         df_filtered['pct_diff'] = (
#             (df_filtered['predicted_price'] - df_filtered['price']) / df_filtered['price']
#         ) * 100

#     if df_filtered.empty:
#         return go.Figure().update_layout(template="plotly_white")

#     values = df_filtered['pct_diff'].dropna().values
#     counts, bin_edges = np.histogram(values, bins=100)
#     counts_pct = counts / counts.sum() * 100
#     bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])

#     vmin = df_filtered['pct_diff'].min()
#     vmax = df_filtered['pct_diff'].max()

#     fig = go.Figure(go.Bar(
#         x=counts_pct,
#         y=bin_centers,
#         orientation='h',
#         marker=dict(
#             color=bin_centers,
#             colorscale='RdBu',
#             cmin=vmin,
#             cmax=vmax,
#             line=dict(color='black', width=1)
#         ),
#         width=(bin_edges[1] - bin_edges[0]) * 0.9,
#         hovertemplate='%{y:.1f}% deviation<br>%{x:.1f}% of listings<extra></extra>'
#     ))

#     fig.update_layout(
#         template='plotly_white',
#         margin=dict(l=0, r=0, t=180, b=0),  # ⬅ increased top margin to shift plot downward
#         showlegend=False,
#         xaxis=dict(
#             showticklabels=False,
#             showgrid=False,
#             zeroline=False
#         ),
#         yaxis=dict(
#             showticklabels=False,
#             showgrid=False,
#             zeroline=False
#         )
#     )

#     return fig



def custom_boxplot_no_whiskers(df_filtered, selected_model):
    """
    Generate clean whiskerless boxplots with uniform gray x-tick labels rotated -45 degrees.
    All boxplots use Q1–Q3, with mean as the horizontal line. Selected model is just shown
    like all others for minimal visual clutter.
    """
    required_columns = {'model', 'price', 'brand'}
    if not required_columns.issubset(df_filtered.columns):
        raise ValueError(f"DataFrame must include columns: {required_columns}")

    model_means = df_filtered.groupby("model")["price"].mean().sort_values()
    ordered_models = model_means.index.tolist()

    selected_prices = df_filtered[df_filtered["model"] == selected_model]["price"]
    selected_q1 = selected_prices.quantile(0.25)
    selected_q3 = selected_prices.quantile(0.75)

    fig = go.Figure()
    all_q1, all_q3 = [], []

    tick_labels = ordered_models  # All models shown uniformly

    for i, model in enumerate(ordered_models):
        data = df_filtered[df_filtered['model'] == model]['price']
        brand = df_filtered[df_filtered['model'] == model]['brand'].mode().values[0]

        if len(data) < 2:
            continue

        q1 = data.quantile(0.25)
        q3 = data.quantile(0.75)
        mean = data.mean()
        all_q1.append(q1)
        all_q3.append(q3)

        def fmt(val): return f"{val / 1000:.1f}k"

        hovertext = (
            f"<b>Brand:</b> {brand}<br>"
            f"<b>Model:</b> {model}<br>"
            f"<b>Approx. Price Range:</b> {fmt(q1)} – {fmt(q3)} EUR<br>"
            f"<b>Avg. Price:</b> {fmt(mean)} EUR"
        )

        if model == selected_model:
            edge_color = "black"
            edge_width = 3
        elif q1 < selected_q3 and q3 > selected_q1:
            edge_color = "orange"
            edge_width = 1
        elif q1 < selected_q3:
            edge_color = "green"
            edge_width = 1
        elif q3 > selected_q1:
            edge_color = "red"
            edge_width = 1
        else:
            edge_color = "lightgray"
            edge_width = 1

        # Box (Q1 to Q3)
        fig.add_trace(go.Scatter(
            x=[i - 0.2, i + 0.2, i + 0.2, i - 0.2, i - 0.2],
            y=[q1, q1, q3, q3, q1],
            fill='toself',
            fillcolor='rgba(0,0,0,0)',
            line=dict(color=edge_color, width=edge_width),
            mode='lines',
            text=hovertext,
            hoverinfo='text',
            showlegend=False
        ))

        # Mean line
        fig.add_trace(go.Scatter(
            x=[i - 0.2, i + 0.2],
            y=[mean, mean],
            mode='lines',
            line=dict(color=edge_color, width=edge_width),
            hoverinfo='skip',
            showlegend=False
        ))

    # Set fixed y-axis range
    if all_q1 and all_q3:
        y_min = min(all_q1)
        y_max = max(all_q3)
        padding = (y_max - y_min) * 0.05
        y_range = [y_min - padding, y_max + padding]
    else:
        y_range = [0, 1]

    # Layout
    fig.update_layout(
        template="plotly_white",
        title="Comparison with similar car models for sale",
        #height=600,
        yaxis_title="Price (€)",
        xaxis_title=None,
        margin=dict(l=50, r=20, t=60, b=100),
        xaxis=dict(
        tickmode='array',
        tickvals=list(range(len(tick_labels))),
        ticktext=tick_labels,
        tickangle=-45,
        showgrid=False,
        zeroline=False,
        tickfont=dict(color="black", size=11),
        showline=True,             
        linecolor="gray",           
        linewidth=1,
        mirror=True                 
    ),
    yaxis=dict(
        showgrid=True,
        range=y_range,
        showline=True,              
        linecolor="gray",          
        linewidth=1,
        mirror=True                 
    ),

        
    )

    return fig
