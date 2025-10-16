import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any, Optional
import re


class FinancialCharts:
    """
    Generate financial visualizations from research data.
    """
    
    @staticmethod
    def extract_financial_metrics(tasks_completed: List[Dict]) -> Dict[str, Any]:
        """Extract financial metrics from completed tasks."""
        metrics = {
            'revenues': [],
            'margins': [],
            'ratios': [],
            'trends': []
        }
        
        for task in tasks_completed:
            data = task.get('data', {})
            result = task.get('result', '')
            
            # Extract revenue data
            if 'income_statement' in data:
                income_data = data['income_statement']
                if isinstance(income_data, list):
                    for period in income_data:
                        if 'revenue' in period and 'period' in period:
                            metrics['revenues'].append({
                                'period': period['period'],
                                'revenue': period['revenue'],
                                'company': data.get('company_profile', {}).get('symbol', 'Unknown')
                            })
            
            # Extract margin/ratio data from text results
            margin_pattern = r'(\w+)\s+(?:margin|ratio)[:\s]+(\d+\.?\d*)%?'
            margins = re.findall(margin_pattern, result, re.IGNORECASE)
            for metric_name, value in margins:
                metrics['margins'].append({
                    'metric': metric_name.title(),
                    'value': float(value)
                })
        
        return metrics
    
    @staticmethod
    def create_revenue_trend_chart(metrics: Dict[str, Any]) -> Optional[go.Figure]:
        """Create a revenue trend line chart."""
        if not metrics.get('revenues'):
            return None
        
        revenues = metrics['revenues']
        
        # Group by company
        companies = {}
        for item in revenues:
            company = item.get('company', 'Unknown')
            if company not in companies:
                companies[company] = {'periods': [], 'values': []}
            companies[company]['periods'].append(item.get('period', ''))
            companies[company]['values'].append(item.get('revenue', 0))
        
        fig = go.Figure()
        
        for company, data in companies.items():
            fig.add_trace(go.Scatter(
                x=data['periods'],
                y=data['values'],
                mode='lines+markers',
                name=company,
                line=dict(width=3),
                marker=dict(size=8)
            ))
        
        fig.update_layout(
            title="Revenue Trend Analysis",
            xaxis_title="Period",
            yaxis_title="Revenue ($)",
            hovermode='x unified',
            template='plotly_white',
            height=400
        )
        
        return fig
    
    @staticmethod
    def create_margin_comparison_chart(metrics: Dict[str, Any]) -> Optional[go.Figure]:
        """Create a bar chart comparing financial margins."""
        if not metrics.get('margins'):
            return None
        
        margins = metrics['margins']
        metric_names = [m['metric'] for m in margins]
        values = [m['value'] for m in margins]
        
        fig = go.Figure(data=[
            go.Bar(
                x=metric_names,
                y=values,
                marker_color='steelblue',
                text=values,
                texttemplate='%{text:.1f}%',
                textposition='outside'
            )
        ])
        
        fig.update_layout(
            title="Financial Margins Comparison",
            xaxis_title="Metric",
            yaxis_title="Percentage (%)",
            template='plotly_white',
            height=400,
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def create_ratio_gauge(ratio_value: float, ratio_name: str, max_value: float = 100) -> go.Figure:
        """Create a gauge chart for a financial ratio."""
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=ratio_value,
            title={'text': ratio_name},
            delta={'reference': max_value * 0.5},
            gauge={
                'axis': {'range': [None, max_value]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, max_value * 0.33], 'color': "lightgray"},
                    {'range': [max_value * 0.33, max_value * 0.66], 'color': "gray"},
                    {'range': [max_value * 0.66, max_value], 'color': "darkgray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': max_value * 0.9
                }
            }
        ))
        
        fig.update_layout(
            height=300,
            template='plotly_white'
        )
        
        return fig
    
    @staticmethod
    def create_comparison_bar_chart(data: Dict[str, float], title: str = "Comparison") -> go.Figure:
        """Create a simple comparison bar chart."""
        companies = list(data.keys())
        values = list(data.values())
        
        fig = go.Figure(data=[
            go.Bar(
                x=companies,
                y=values,
                marker_color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'][:len(companies)],
                text=values,
                texttemplate='%{text:.2f}',
                textposition='outside'
            )
        ])
        
        fig.update_layout(
            title=title,
            xaxis_title="Company",
            yaxis_title="Value",
            template='plotly_white',
            height=400,
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def analyze_and_create_charts(tasks_completed: List[Dict]) -> List[go.Figure]:
        """Automatically analyze tasks and create relevant charts."""
        charts = []
        
        metrics = FinancialCharts.extract_financial_metrics(tasks_completed)
        
        # Create revenue trend chart if data available
        revenue_chart = FinancialCharts.create_revenue_trend_chart(metrics)
        if revenue_chart:
            charts.append(revenue_chart)
        
        # Create margin comparison chart if data available
        margin_chart = FinancialCharts.create_margin_comparison_chart(metrics)
        if margin_chart:
            charts.append(margin_chart)
        
        return charts
