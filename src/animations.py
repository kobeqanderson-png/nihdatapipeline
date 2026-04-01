"""
Animation utilities for lightweight, engaging UI effects using CSS and Streamlit components.
"""

import streamlit as st


def inject_animation_css() -> None:
    """Inject CSS animations globally for fade-ins, slides, and pulse effects."""
    st.markdown(
        """
        <style>
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes slideInLeft {
            from {
                opacity: 0;
                transform: translateX(-20px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }

        @keyframes slideInRight {
            from {
                opacity: 0;
                transform: translateX(20px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }

        @keyframes pulse {
            0%, 100% {
                opacity: 1;
            }
            50% {
                opacity: 0.7;
            }
        }

        @keyframes shimmer {
            0% {
                background-position: -1000px 0;
            }
            100% {
                background-position: 1000px 0;
            }
        }

        @keyframes bounce {
            0%, 100% {
                transform: translateY(0);
            }
            50% {
                transform: translateY(-5px);
            }
        }

        @keyframes spin {
            from {
                transform: rotate(0deg);
            }
            to {
                transform: rotate(360deg);
            }
        }

        @keyframes checkmark {
            0% {
                stroke-dashoffset: 51;
            }
            100% {
                stroke-dashoffset: 0;
            }
        }

        .animate-fade-in {
            animation: fadeIn 0.6s ease-in-out;
        }

        .animate-slide-left {
            animation: slideInLeft 0.5s ease-out;
        }

        .animate-slide-right {
            animation: slideInRight 0.5s ease-out;
        }

        .animate-pulse {
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }

        .animate-bounce {
            animation: bounce 1s infinite;
        }

        .animate-spin {
            animation: spin 1s linear infinite;
        }

        .metric-card {
            animation: fadeIn 0.8s ease-out forwards;
            animation-fill-mode: both;
        }

        .metric-card:nth-child(1) { animation-delay: 0.1s; }
        .metric-card:nth-child(2) { animation-delay: 0.2s; }
        .metric-card:nth-child(3) { animation-delay: 0.3s; }
        .metric-card:nth-child(4) { animation-delay: 0.4s; }

        .page-transition {
            animation: fadeIn 0.5s ease-in-out;
        }

        .button-hover {
            transition: all 0.3s ease;
        }

        .button-hover:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3);
        }

        [data-testid="stMetricValue"] {
            font-weight: 700;
            letter-spacing: 0.05em;
        }

        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            animation: fadeIn 0.4s ease-out;
        }

        .status-success {
            background-color: rgba(34, 197, 94, 0.2);
            color: #22c55e;
            border: 1px solid #22c55e;
        }

        .status-warning {
            background-color: rgba(239, 68, 68, 0.2);
            color: #ef4444;
            border: 1px solid #ef4444;
        }

        .status-info {
            background-color: rgba(59, 130, 246, 0.2);
            color: #3b82f6;
            border: 1px solid #3b82f6;
        }

        .info-card {
            padding: 16px;
            border-radius: 8px;
            background: var(--bg-soft);
            border: 1px solid var(--border);
            animation: slideInLeft 0.6s ease-out;
        }

        .success-card {
            padding: 16px;
            border-radius: 8px;
            background: rgba(34, 197, 94, 0.1);
            border: 1px solid rgba(34, 197, 94, 0.3);
            animation: fadeIn 0.5s ease-out;
        }

        .warning-card {
            padding: 16px;
            border-radius: 8px;
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            animation: fadeIn 0.5s ease-out;
        }

        .data-row {
            animation: fadeIn 0.4s ease-out;
        }

        .chart-container {
            animation: fadeIn 0.8s ease-out;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def animated_metric(label: str, value: str, delta: str = None, icon: str = "📊") -> None:
    """Display an animated metric card."""
    html = f"""
    <div class="metric-card">
        <div style="font-size: 20px; margin-bottom: 8px;">{icon}</div>
        <div style="font-size: 12px; color: #9aa4b2; margin-bottom: 4px;">{label}</div>
        <div style="font-size: 24px; font-weight: bold; color: #22c55e;">{value}</div>
        {f'<div style="font-size: 11px; color: #15803d; margin-top: 4px;">{delta}</div>' if delta else ''}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def animated_header(title: str, subtitle: str = None, emoji: str = "") -> None:
    """Display an animated header with optional subtitle."""
    html = f"""
    <div class="page-transition" style="margin-bottom: 20px;">
        <h1 style="animation: slideInLeft 0.6s ease-out;">
            {emoji} {title}
        </h1>
        {f'<p style="color: #9aa4b2; animation: slideInLeft 0.7s ease-out 0.1s both;">{subtitle}</p>' if subtitle else ''}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def animated_success_message(message: str, icon: str = "✓") -> None:
    """Display an animated success message."""
    html = f"""
    <div class="success-card">
        <span style="font-size: 18px; margin-right: 10px;">{icon}</span>
        <span style="font-weight: 500;">{message}</span>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def animated_info_message(message: str, icon: str = "ℹ️") -> None:
    """Display an animated info message."""
    html = f"""
    <div class="info-card">
        <span style="font-size: 16px; margin-right: 10px;">{icon}</span>
        <span>{message}</span>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def animated_warning_message(message: str, icon: str = "⚠️") -> None:
    """Display an animated warning message."""
    html = f"""
    <div class="warning-card">
        <span style="font-size: 16px; margin-right: 10px;">{icon}</span>
        <span>{message}</span>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def animated_progress_steps(
    current_step: int,
    total_steps: int,
    steps: list,
    display_from_step: int = 1,
    show_leading_connector: bool = False,
) -> None:
    """Display animated progress through steps."""
    html = "<div style='margin: 20px 0;'>"

    display_from_step = max(1, int(display_from_step))
    display_from_index = min(display_from_step - 1, len(steps))

    if show_leading_connector and display_from_step > 1:
        previous_step = display_from_step - 1
        leading_color = "rgba(255, 133, 123, 0.5)" if previous_step < current_step else "rgba(140, 150, 173, 0.2)"
        html += f"""
        <div style="height: 16px; width: 2px; background: {leading_color}; margin-left: 15px; margin-bottom: 8px;"></div>
        """
    
    for i, step_name in enumerate(steps[display_from_index:], start=display_from_index):
        step_num = i + 1
        if step_num < current_step:
            status = "✓"
            color = "#ff857b"
            opacity = "1"
        elif step_num == current_step:
            status = "●"
            color = "#ff857b"
            opacity = "1"
        else:
            status = str(step_num)
            color = "#8c96ad"
            opacity = "0.5"
        
        html += f"""
        <div style="display: flex; align-items: center; margin-bottom: 12px; opacity: {opacity}; animation: fadeIn 0.5s ease-out;">
            <div style="
                width: 32px; 
                height: 32px; 
                border-radius: 50%; 
                background: rgba(255, 106, 95, 0.12); 
                border: 2px solid {color};
                display: flex; 
                align-items: center; 
                justify-content: center; 
                font-weight: bold;
                color: {color};
                margin-right: 12px;
            ">{status}</div>
            <span style="color: #d1d5db; font-weight: 500;">{step_name}</span>
        </div>
        """
        
        if i < len(steps) - 1:
            html += f"""
            <div style="height: 16px; width: 2px; background: {'rgba(255, 133, 123, 0.5)' if step_num < current_step else 'rgba(140, 150, 173, 0.2)'}; margin-left: 15px; margin-bottom: 8px;"></div>
            """
    
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def animated_stat_row(stat_name: str, stat_value: str, comparison: str = None, color: str = "#22c55e") -> None:
    """Display an animated statistics row."""
    html = f"""
    <div class="data-row" style="
        padding: 12px;
        background: rgba(34, 197, 94, 0.05);
        border-left: 3px solid {color};
        border-radius: 4px;
        margin-bottom: 8px;
        animation: slideInLeft 0.5s ease-out;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="color: #d1d5db; font-weight: 500;">{stat_name}</span>
            <div style="text-align: right;">
                <div style="color: {color}; font-size: 16px; font-weight: bold;">{stat_value}</div>
                {f'<div style="font-size: 12px; color: #9aa4b2;">{comparison}</div>' if comparison else ''}
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def animated_loading_spinner(message: str = "Processing...", duration: float = 0.5) -> None:
    """Display animated loading spinner with message."""
    html = f"""
    <div style="text-align: center; padding: 20px;">
        <div class="animate-spin" style="
            display: inline-block;
            width: 40px;
            height: 40px;
            border: 3px solid rgba(34, 197, 94, 0.2);
            border-top: 3px solid #22c55e;
            border-radius: 50%;
            margin-bottom: 12px;
        "></div>
        <p style="color: #9aa4b2; margin-top: 12px;">{message}</p>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def animated_completion_badge(text: str = "Complete") -> None:
    """Display an animated completion badge."""
    html = f"""
    <div style="
        display: inline-block;
        padding: 8px 16px;
        background: rgba(34, 197, 94, 0.2);
        border: 1px solid #22c55e;
        border-radius: 20px;
        animation: bounce 1s ease-in-out;
    ">
        <span style="color: #22c55e; font-weight: 600; font-size: 14px;">✓ {text}</span>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def animated_divider() -> None:
    """Display an animated divider line."""
    st.markdown(
        """
        <div style="
            height: 1px;
            background: linear-gradient(90deg, transparent, #30363d, transparent);
            margin: 24px 0;
            animation: fadeIn 0.8s ease-out;
        "></div>
        """,
        unsafe_allow_html=True,
    )


def create_metric_grid(metrics: list) -> None:
    """Create animated grid of metric cards.
    
    Args:
        metrics: List of dicts with keys:
                 - label (str): Metric label
                 - value (str): Metric value
                 - icon (str): Icon emoji
                 - delta (str, optional): Delta/change text
    """
    cols = st.columns(len(metrics))
    for col, metric in zip(cols, metrics):
        with col:
            html = f"""
            <div class="metric-card" style="
                padding: 16px;
                background: var(--bg-soft);
                border: 1px solid var(--border);
                border-radius: 8px;
                text-align: center;
            ">
                <div style="font-size: 28px; margin-bottom: 8px;">{metric.get('icon', '📊')}</div>
                <div style="font-size: 12px; color: #9aa4b2; margin-bottom: 8px;">{metric['label']}</div>
                <div style="font-size: 20px; font-weight: bold; color: #22c55e;">{metric['value']}</div>
                {f'<div style="font-size: 11px; color: #15803d; margin-top: 8px;">{metric["delta"]}</div>' if metric.get('delta') else ''}
            </div>
            """
            st.markdown(html, unsafe_allow_html=True)
