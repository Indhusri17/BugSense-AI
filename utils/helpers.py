import html

SEVERITY_COLORS = {
    "Critical": {"bg": "rgba(244, 63, 94, 0.15)", "text": "#fda4af", "border": "rgba(244, 63, 94, 0.3)"},
    "High": {"bg": "rgba(249, 115, 22, 0.15)", "text": "#fdba74", "border": "rgba(249, 115, 22, 0.3)"},
    "Medium": {"bg": "rgba(234, 179, 8, 0.15)", "text": "#fde047", "border": "rgba(234, 179, 8, 0.3)"},
    "Low": {"bg": "rgba(20, 184, 166, 0.15)", "text": "#5eead4", "border": "rgba(20, 184, 166, 0.3)"}
}

STATUS_COLORS = {
    "New": {"bg": "rgba(59, 130, 246, 0.15)", "text": "#93c5fd", "border": "rgba(59, 130, 246, 0.3)"},
    "Triaged": {"bg": "rgba(168, 85, 247, 0.15)", "text": "#d8b4fe", "border": "rgba(168, 85, 247, 0.3)"},
    "In Progress": {"bg": "rgba(245, 158, 11, 0.15)", "text": "#fcd34d", "border": "rgba(245, 158, 11, 0.3)"},
    "Resolved": {"bg": "rgba(16, 185, 129, 0.15)", "text": "#6ee7b7", "border": "rgba(16, 185, 129, 0.3)"},
    "Closed": {"bg": "rgba(100, 116, 139, 0.15)", "text": "#cbd5e1", "border": "rgba(100, 116, 139, 0.3)"}
}

def render_badge(label: str, badge_type: str = "severity") -> str:
    """Render a showcase-style pill badge with translucent dark background and colored border."""
    safe_label = html.escape(str(label))
    if badge_type == "severity":
        scheme = SEVERITY_COLORS.get(label, {"bg": "rgba(148, 163, 184, 0.15)", "text": "#cbd5e1", "border": "rgba(148, 163, 184, 0.3)"})
    else:
        scheme = STATUS_COLORS.get(label, {"bg": "rgba(148, 163, 184, 0.15)", "text": "#cbd5e1", "border": "rgba(148, 163, 184, 0.3)"})

    return (
        f'<span style="background-color: {scheme["bg"]}; '
        f'color: {scheme["text"]}; '
        f'border: 1px solid {scheme["border"]}; '
        f'border-radius: 9999px; padding: 2px 10px; font-weight: 600; '
        f'font-size: 0.75rem; display: inline-flex; align-items: center; margin-right: 4px; letter-spacing: 0.02em;">'
        f'{safe_label}'
        f'</span>'
    )

def render_metric_card(title: str, value: str | int, subtitle: str = "", delta: str = "", color: str = "#f8fafc") -> str:
    """Render a showcase dark-slate metric card."""
    return f"""
    <div style="background-color: #1e293b; border: 1px solid #334155; border-radius: 14px; padding: 18px; text-align: center; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
        <div style="color: #94a3b8; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em;">{title}</div>
        <div style="color: {color}; font-size: 2.1rem; font-weight: 800; margin: 4px 0;">{value}</div>
        {f'<div style="color: #10b981; font-size: 0.78rem; font-weight: 600;">{delta}</div>' if delta else ''}
        {f'<div style="color: #64748b; font-size: 0.72rem; margin-top: 2px;">{subtitle}</div>' if subtitle else ''}
    </div>
    """

def render_radial_meter_html(percentage: float, label: str = "Duplicate Match") -> str:
    """Render the exact animated SVG radial meter from the showcase UI."""
    pct = max(0, min(100, round(percentage)))
    if pct >= 50:
        stroke_color = "#f43f5e" # rose-500
        badge_bg = "rgba(244, 63, 94, 0.2)"
        badge_text = "#fda4af"
        badge_border = "rgba(244, 63, 94, 0.3)"
        status_text = "High Duplicate Risk"
    elif pct >= 30:
        stroke_color = "#f59e0b" # amber-500
        badge_bg = "rgba(245, 158, 11, 0.2)"
        badge_text = "#fcd34d"
        badge_border = "rgba(245, 158, 11, 0.3)"
        status_text = "Similar Past Defect"
    else:
        stroke_color = "#10b981" # emerald-500
        badge_bg = "rgba(16, 185, 129, 0.2)"
        badge_text = "#6ee7b7"
        badge_border = "rgba(16, 185, 129, 0.3)"
        status_text = "Original Ticket (Unique)"

    return f"""
    <div style="display: flex; align-items: center; gap: 16px; background: #0f172a; border: 1px solid #334155; border-radius: 12px; padding: 14px 18px;">
        <div style="position: relative; width: 68px; height: 68px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
            <svg style="width: 100%; height: 100%; transform: rotate(-90deg);" viewBox="0 0 36 36">
                <path stroke="#1e293b" stroke-width="3.5" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>
                <path stroke="{stroke_color}" stroke-dasharray="{pct}, 100" stroke-width="3.5" stroke-linecap="round" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>
            </svg>
            <div style="position: absolute; font-size: 0.82rem; font-weight: 800; color: #f8fafc;">{pct}%</div>
        </div>
        <div style="flex: 1;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
                <span style="font-size: 0.72rem; font-weight: 700; color: #94a3b8; text-transform: uppercase;">{label}</span>
                <span style="background: {badge_bg}; color: {badge_text}; border: 1px solid {badge_border}; border-radius: 9999px; padding: 1px 8px; font-size: 0.7rem; font-weight: 700;">{status_text}</span>
            </div>
            <div style="font-size: 0.88rem; font-weight: 600; color: #f8fafc;">
                {"Potential duplicate of historical ticket detected!" if pct >= 50 else ("Related defects found in knowledge base." if pct >= 30 else "No similar ticket found in corpus.")}
            </div>
        </div>
    </div>
    """
