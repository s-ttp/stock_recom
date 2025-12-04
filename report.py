import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import ai_analysis

def generate_charts(ticker, price_history, insider_data, ai_prediction=None):
    """
    Generates professional charts for the report.
    Returns a dictionary of BytesIO objects containing the chart images.
    """
    charts = {}
    
    # Set professional style
    plt.style.use('seaborn-v0_8-darkgrid')
    
    # 1. 5-Year Price History Chart
    if price_history is not None and not price_history.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(price_history.index, price_history['Close'], 
                label='Close Price', color='#2E86AB', linewidth=2)
        ax.fill_between(price_history.index, price_history['Close'], 
                        alpha=0.3, color='#2E86AB')
        ax.set_title(f"{ticker} 5-Year Price History", fontsize=16, fontweight='bold')
        ax.set_xlabel("Date", fontsize=12)
        ax.set_ylabel("Price ($)", fontsize=12)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.legend(fontsize=10)
        plt.tight_layout()
        
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        charts['price_chart'] = buf
        plt.close()
    
    # 2. 5-Year Price Prediction Chart
    if ai_prediction and price_history is not None and not price_history.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        
        # Historical data
        ax.plot(price_history.index, price_history['Close'], 
                label='Historical Price', color='#2E86AB', linewidth=2)
        
        # Prediction data
        last_date = price_history.index[0]  # Stooq returns newest first
        last_price = price_history['Close'].iloc[0]
        
        # Generate prediction dates (5 years forward)
        pred_dates = pd.date_range(start=last_date, periods=60, freq='ME')
        
        # Use AI prediction or generate simple trend
        if 'predicted_prices' in ai_prediction:
            pred_prices = ai_prediction['predicted_prices']
        else:
            # Simple linear projection based on AI growth rate
            growth_rate = ai_prediction.get('annual_growth_rate', 0.10)
            pred_prices = [last_price * ((1 + growth_rate) ** (i/12)) for i in range(60)]
        
        ax.plot(pred_dates, pred_prices, 
                label='AI Prediction', color='#06A77D', linewidth=2, linestyle='--')
        ax.fill_between(pred_dates, pred_prices, alpha=0.2, color='#06A77D')
        
        ax.axvline(x=last_date, color='red', linestyle=':', linewidth=1, alpha=0.7)
        ax.text(last_date, ax.get_ylim()[1]*0.95, 'Today', 
                rotation=90, verticalalignment='top', fontsize=9, color='red')
        
        ax.set_title(f"{ticker} 5-Year Price Prediction (AI-Powered)", 
                    fontsize=16, fontweight='bold')
        ax.set_xlabel("Date", fontsize=12)
        ax.set_ylabel("Price ($)", fontsize=12)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.legend(fontsize=10)
        plt.tight_layout()
        
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        charts['prediction_chart'] = buf
        plt.close()
    
    # 3. Insider Activity Chart
    if insider_data:
        fig, ax = plt.subplots(figsize=(7, 4))
        labels = ['Buys', 'Sells']
        values = [insider_data['buys'], insider_data['sells']]
        colors_list = ['#06A77D', '#D62828']
        
        bars = ax.bar(labels, values, color=colors_list, edgecolor='black', linewidth=1.5)
        ax.set_title(f"{ticker} Insider Activity", fontsize=14, fontweight='bold')
        ax.set_ylabel("Number of Transactions", fontsize=11)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}', ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        charts['insider_chart'] = buf
        plt.close()
        
    return charts

def generate_pe_chart(price_data, earnings_data):
    """Generates a 5-year P/E ratio trend chart."""
    try:
        # Process Price Data (Monthly)
        prices = pd.DataFrame(price_data)
        if prices.empty:
            return None
            
        prices['Date'] = pd.to_datetime(prices['Date'])
        prices = prices.set_index('Date').sort_index()
        
        # Process Earnings Data (Quarterly)
        eps = pd.DataFrame(earnings_data)
        if eps.empty:
            return None
            
        eps['fiscalDateEnding'] = pd.to_datetime(eps['fiscalDateEnding'])
        eps['reportedEPS'] = pd.to_numeric(eps['reportedEPS'], errors='coerce')
        eps = eps.set_index('fiscalDateEnding').sort_index()
        
        # Calculate TTM EPS for each price date
        pe_ratios = []
        dates = []
        
        for date, row in prices.iterrows():
            # Get last 4 quarters of EPS before this date
            past_earnings = eps[eps.index <= date].tail(4)
            if len(past_earnings) < 4:
                continue
                
            ttm_eps = past_earnings['reportedEPS'].sum()
            
            if ttm_eps > 0:
                pe = row['Close'] / ttm_eps
                # Filter outliers
                if 0 < pe < 100: 
                    pe_ratios.append(pe)
                    dates.append(date)
        
        if not pe_ratios:
            return None
            
        plt.figure(figsize=(10, 4))
        plt.plot(dates, pe_ratios, color='#2E86AB', linewidth=2)
        plt.title('5-Year P/E Ratio Trend', fontsize=12, fontweight='bold')
        plt.ylabel('P/E Ratio')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        plt.close()
        buf.seek(0)
        return buf
    except Exception as e:
        print(f"Error generating P/E chart: {e}")
        return None

def format_billions(val):
    """Formats a value in Billions ($B)."""
    if val is None or val == 'N/A':
        return "N/A"
    try:
        numeric_val = float(val)
        return f"${numeric_val / 1_000_000_000:,.1f}B"
    except (ValueError, TypeError):
        return str(val)

def create_pdf_report(filename, report_data, charts):
    """
    Generates a professional PDF report with enhanced design.
    """
    doc = SimpleDocTemplate(filename, pagesize=letter,
                           topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    story = []
    
    ticker = report_data['ticker']
    price_data = report_data['price_data']
    superinvestor = report_data['superinvestor']
    insider = report_data['insider']
    ai_data = report_data.get('ai_analysis', {})
    news_items = report_data.get('news', [])
    total_score = report_data.get('total_score', 0)
    
    # Custom Styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=28,
        textColor=colors.HexColor('#1A1A2E'),
        spaceAfter=30,
        alignment=1  # Center
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#2E86AB'),
        spaceBefore=20,
        spaceAfter=12,
        borderWidth=2,
        borderColor=colors.HexColor('#2E86AB'),
        borderPadding=5
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.HexColor('#06A77D'),
        spaceBefore=10,
        spaceAfter=8
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#1A1A2E'),
        spaceBefore=6,
        spaceAfter=6
    )
    
    # Title with Company Name and Ticker
    company_name = report_data.get('analysis_data', {}).get('Name', report_data['ticker'])
    title = Paragraph(f"Investment Thesis: {company_name} ({report_data['ticker']})", title_style)
    story.append(title)
    story.append(Spacer(1, 10))
    
    # Executive Summary Box
    story.append(Paragraph("Executive Summary", heading_style))
    
    # Use format_billions for Market Cap
    mc = report_data['price_data'].get('Market_Cap')
    mc_str = format_billions(mc)
    
    # Calculate P/E and P/S if available
    price = report_data['price_data']['Current_Price']
    # We need earnings/sales for P/E and P/S. 
    # For now, let's stick to what we have or use placeholders if missing
    
    summary_data = [
        ["Current Price", f"${price}"],
        ["52-Week Range", f"${report_data['price_data']['52_Week_Low']} - ${report_data['price_data'].get('52_Week_High', 'N/A')}"],
        ["Market Cap", mc_str],
        ["Smart Money Score", f"{report_data['smart_money_score']}/10"]
    ]
    
    summary_text = f"""
    <b>Investment Recommendation:</b> {'BUY' if total_score > 12 else 'HOLD' if total_score > 8 else 'WATCH'}<br/>
    <b>Probability Score:</b> {total_score:.1f} / 20<br/>
    <b>Current Price:</b> ${report_data['price_data']['Current_Price']}<br/>
    <b>52-Week Low:</b> ${report_data['price_data']['52_Week_Low']} (+{report_data['price_data']['Above_Low_Pct']}%)<br/>
    <b>Market Cap:</b> {mc_str} <br/>
    <br/>
    <b>Key Thesis:</b> {report_data['ticker']} is trading near its 52-week low, presenting a potential value opportunity. 
    {'Strong' if total_score > 12 else 'Moderate' if total_score > 8 else 'Weak'} insider buying activity 
    and {'positive' if ai_data.get('management', {}).get('score', 0) > 6 else 'mixed'} management quality 
    signals suggest {'compelling' if total_score > 12 else 'reasonable' if total_score > 8 else 'limited'} 
    upside potential over the next 2-3 years.
    """
    
    summary_table = Table([[Paragraph(summary_text, styles['Normal'])]], colWidths=[6.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F0F4F8')),
        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#2E86AB')),
        ('PADDING', (0, 0), (-1, -1), 15),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 20))
    
    # 1. Valuation Metrics
    story.append(Paragraph("1. Valuation Metrics", heading_style))
    
    val_data = [
        ["Metric", "Value"],
        ["Current Price", f"${report_data['price_data']['Current_Price']}"],
        ["52-Week Low", f"${report_data['price_data']['52_Week_Low']}"],
        ["Premium over Low", f"{report_data['price_data']['Above_Low_Pct']}%"],
        ["Market Cap", mc_str],
        ["Free Cash Flow", format_billions(report_data['price_data'].get('FCF'))],
        ["Debt/Equity Ratio", f"{report_data['price_data'].get('Debt_Equity', 0):.2f}" if report_data['price_data'].get('Debt_Equity') is not None else 'N/A']
    ]
    
    # Add additional financial metrics if available from report_data
    financial_data = report_data.get('financial_metrics', {})
    if financial_data:
        if financial_data.get('pe_ratio'):
            val_data.append(["P/E Ratio", f"{financial_data['pe_ratio']:.2f}"])
        if financial_data.get('pb_ratio'):
            val_data.append(["P/B Ratio", f"{financial_data['pb_ratio']:.2f}"])
        if financial_data.get('dividend_yield'):
            val_data.append(["Dividend Yield", f"{financial_data['dividend_yield']:.2f}%"])
        if financial_data.get('roe'):
            val_data.append(["ROE", f"{financial_data['roe']:.2f}%"])
        if financial_data.get('profit_margin'):
            val_data.append(["Profit Margin", f"{financial_data['profit_margin']:.2f}%"])
    
    t = Table(val_data, colWidths=[3*inch, 3*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F9FA')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#DEE2E6')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')])
    ]))
    story.append(t)
    story.append(Spacer(1, 15))
    
    # 5-Year Price Chart
    if 'price_chart' in charts:
        story.append(Image(charts['price_chart'], width=6*inch, height=3*inch))
        story.append(Spacer(1, 20))

    # 5-Year P/E Ratio Chart
    if 'pe_chart' in charts:
        story.append(Image(charts['pe_chart'], width=6*inch, height=3*inch))
        story.append(Spacer(1, 20))
    
    # 5. Analyst Price Target
    story.append(Paragraph("5. Analyst Price Target", heading_style))
    
    target = report_data['financial_metrics'].get('targetMeanPrice')
    current = report_data['price_data']['Current_Price']
    
    if target:
        upside = (target - current) / current * 100
        color = 'green' if upside > 0 else 'red'
        text = f"""
        <b>Current Price:</b> ${current:.2f}<br/>
        <b>Mean Analyst Target:</b> ${target:.2f}<br/>
        <b>Implied Upside:</b> <font color='{color}'>{upside:+.1f}%</font>
        """
        story.append(Paragraph(text, body_style))
    else:
        story.append(Paragraph("Insufficient analyst data to predict price target.", body_style))
        
    story.append(Spacer(1, 12))
    
    # Page Break
    story.append(PageBreak())
    
    # 2. Smart Money Analysis
    story.append(Paragraph("2. Smart Money Analysis", heading_style))
    
    si = report_data.get('superinvestor', {})
    ins = report_data.get('insider', {})
    
    sm_data = [
        ["Category", "Activity", "Details"],
        ["Superinvestors", f"Buys: {si.get('buys', 0)} | Sells: {si.get('sells', 0)}", 
         f"Buyers: {', '.join(si.get('buyers', [])[:3]) if si.get('buyers') else 'None'}"],
        ["Insiders", f"Buys: {ins.get('buys', 0)} | Sells: {ins.get('sells', 0)}", 
         f"Net Value: ${ins.get('net_value', 0):,.0f}"]
    ]
    
    t2 = Table(sm_data, colWidths=[1.5*inch, 2*inch, 3.5*inch])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#DEE2E6')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')])
    ]))
    story.append(t2)
    story.append(Spacer(1, 20))
    
    # 3. Quarterly Financials (Last 8 Quarters)
    story.append(Paragraph("3. Quarterly Financials (Last 8 Quarters)", heading_style))
    
    q_financials = report_data.get('quarterly_financials', [])
    if q_financials:
        q_data = [["Quarter Ending", "Revenue ($M)", "Net Income ($M)", "EPS ($)"]]
        for q in q_financials:
            q_data.append([
                q['fiscalDateEnding'],
                format_billions(q['totalRevenue']).replace('$', ''), # Remove $ since header has ($B)
                format_billions(q['netIncome']).replace('$', ''),
                f"{q['reportedEPS']:.2f}"
            ])
            
        t3 = Table(q_data, colWidths=[1.8*inch, 1.8*inch, 1.8*inch, 1.6*inch])
        t3.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')])
        ]))
        story.append(t3)
    else:
        story.append(Paragraph("Quarterly financial data not available.", styles['Normal']))
        
    story.append(Spacer(1, 20))

    # 4. AI Analysis & Business Outlook
    story.append(Paragraph("4. AI Analysis & Business Outlook", heading_style))
    
    # Management
    story.append(Paragraph("<b>Management Quality:</b>", styles['Normal']))
    story.append(Paragraph(ai_data.get('management', {}).get('analysis', 'N/A'), styles['Normal']))
    story.append(Spacer(1, 10))
    
    # Sustainability
    story.append(Paragraph("<b>Business Sustainability:</b>", styles['Normal']))
    story.append(Paragraph(ai_data.get('sustainability', {}).get('analysis', 'N/A'), styles['Normal']))
    story.append(Spacer(1, 10))
    
    # Business Outlook
    story.append(Paragraph("<b>Business Outlook & Durability:</b>", styles['Normal']))
    story.append(Paragraph(ai_data.get('outlook', 'N/A'), styles['Normal']))
    
    story.append(Spacer(1, 20))
    
    # 5. AI Price Prediction
    story.append(Paragraph("5. AI-Powered 5-Year Price Forecast", heading_style))
    
    if 'prediction_chart' in charts:
        story.append(Image(charts['prediction_chart'], width=6*inch, height=3*inch))
        story.append(Spacer(1, 10))
        
        pred_data = report_data.get('ai_prediction', {})
        pred_text = f"""
        Based on deep analysis of historical patterns, industry trends, and fundamental metrics, 
        our AI model projects a {pred_data.get('annual_growth_rate', 0.10)*100:.1f}% annual growth rate 
        over the next 5 years. Key drivers include {pred_data.get('growth_drivers', 'market expansion and operational efficiency')}.
        """
        story.append(Paragraph(pred_text, styles['Normal']))
    else:
        story.append(Paragraph("Price prediction unavailable due to insufficient data.", styles['Normal']))
    
    story.append(Spacer(1, 20))
    
    # 5. Smart Money Activity
    story.append(Paragraph("5. Smart Money Activity", heading_style))
    
    # Superinvestor
    story.append(Paragraph("Superinvestor Activity (Dataroma)", subheading_style))
    
    si_data = report_data['superinvestor']
    if si_data.get('has_superinvestor_addition'):
        names = ", ".join(si_data.get('buyers', []))
        if not names:
            names = "Multiple Funds"
        story.append(Paragraph(f"Recent Buys by: <b>{names}</b>", body_style))
    else:
        story.append(Paragraph("No recent superinvestor additions found.", body_style))
    
    story.append(Spacer(1, 10))
    
    # Insider
    story.append(Paragraph("Insider Trading (OpenInsider)", subheading_style))
    if insider:
        ins_text = f"<b>Buys:</b> {insider['buys']} | <b>Sells:</b> {insider['sells']} | <b>Net Value:</b> ${insider['net_value']:,.0f}"
        story.append(Paragraph(ins_text, styles['Normal']))
        
        signal_color = '#06A77D' if insider['net_value'] > 0 else '#D62828'
        signal_text = "Insiders are buying (Bullish)" if insider['net_value'] > 0 else "Insiders are selling"
        story.append(Paragraph(f"<font color='{signal_color}'><b>Signal:</b> {signal_text}</font>", styles['Normal']))
        
        story.append(Spacer(1, 10))
        if 'insider_chart' in charts:
            story.append(Image(charts['insider_chart'], width=4*inch, height=2.5*inch))
    else:
        story.append(Paragraph("No insider data available.", styles['Normal']))
    
    story.append(Spacer(1, 20))
    
    # 4. AI Qualitative Analysis
    story.append(Paragraph("4. AI Qualitative Analysis", heading_style))
    
    mgmt = ai_data.get('management', {})
    story.append(Paragraph(f"<b>Management Quality:</b> {mgmt.get('score', 'N/A')}/10", subheading_style))
    story.append(Paragraph(f"{mgmt.get('analysis', 'Analysis unavailable')}", styles['Normal']))
    story.append(Spacer(1, 8))
    
    sust = ai_data.get('sustainability', {})
    story.append(Paragraph(f"<b>Business Sustainability:</b> {sust.get('score', 'N/A')}/10", subheading_style))
    story.append(Paragraph(f"{sust.get('analysis', 'Analysis unavailable')}", styles['Normal']))
    
    story.append(Spacer(1, 20))
    
    # 6. Five Key Investment Reasons
    story.append(Paragraph("6. Five Key Investment Reasons", heading_style))
    
    # Generate investment reasons based on data
    reasons = []
    
    # Check for AI-generated thesis
    if report_data.get('investment_thesis'):
        reasons = report_data['investment_thesis']
    else:
        # Fallback to hardcoded logic
        # Reason 1: Valuation
        if price_data['Above_Low_Pct'] < 15:
            reasons.append(f"<b>Attractive Valuation:</b> Trading only {price_data['Above_Low_Pct']:.1f}% above its 52-week low of ${price_data['52_Week_Low']}, presenting significant upside potential from current depressed levels.")
        else:
            reasons.append(f"<b>Value Opportunity:</b> Currently priced at ${price_data['Current_Price']}, offering potential appreciation as the market recognizes the company's fundamental strengths.")
        
        # Reason 2: Smart Money Activity
        smart_money_score = report_data.get('smart_money_score', 0)
        if smart_money_score >= 7:
            reasons.append(f"<b>Strong Insider Conviction:</b> Significant insider buying activity (Smart Money Score: {smart_money_score}/10) indicates management confidence in the company's future prospects and alignment with shareholder interests.")
        elif smart_money_score >= 4:
            reasons.append(f"<b>Insider Support:</b> Notable insider and institutional buying activity suggests informed investors see value at current levels.")
        else:
            reasons.append(f"<b>Institutional Interest:</b> The stock has attracted attention from value-focused investors seeking quality companies at reasonable prices.")
        
        # Reason 3: Financial Health
        if price_data.get('Debt_Equity') and price_data['Debt_Equity'] < 0.5:
            reasons.append(f"<b>Strong Balance Sheet:</b> Low debt-to-equity ratio of {price_data['Debt_Equity']:.2f} provides financial flexibility and reduces risk during economic downturns.")
        elif price_data.get('FCF') and price_data['FCF'] > 0:
            reasons.append(f"<b>Positive Cash Generation:</b> Strong free cash flow of ${price_data['FCF']:,.0f} demonstrates the company's ability to generate cash and fund growth initiatives.")
        else:
            reasons.append(f"<b>Solid Fundamentals:</b> The company maintains a stable financial position with consistent operational performance.")
        
        # Reason 4: Management Quality
        mgmt_score = ai_data.get('management', {}).get('score', 5)
        if mgmt_score >= 7:
            reasons.append(f"<b>Proven Management Team:</b> AI analysis rates management quality at {mgmt_score}/10, highlighting effective capital allocation and strong track record of value creation.")
        else:
            reasons.append(f"<b>Experienced Leadership:</b> Management team demonstrates competence in navigating industry challenges and executing strategic initiatives.")
        
        # Reason 5: Business Quality/Growth Potential
        sust_score = ai_data.get('sustainability', {}).get('score', 5)
        pred_data = report_data.get('ai_prediction') or {}
        growth_rate = pred_data.get('annual_growth_rate', 0.10)
        
        if sust_score >= 7:
            reasons.append(f"<b>Sustainable Competitive Advantage:</b> Business sustainability score of {sust_score}/10 indicates strong competitive moat and favorable long-term industry positioning.")
        elif growth_rate > 0.12:
            reasons.append(f"<b>Growth Potential:</b> AI-powered analysis projects {growth_rate*100:.1f}% annual growth over the next 5 years, driven by {pred_data.get('growth_drivers', 'market expansion and operational improvements')}.")
        else:
            reasons.append(f"<b>Market Position:</b> Well-established market presence with opportunities for steady growth and value realization over the investment horizon.")
    
    # Display reasons as numbered list
    for i, reason in enumerate(reasons, 1):
        story.append(Paragraph(f"{i}. {reason}", styles['Normal']))
        story.append(Spacer(1, 8))
    
    story.append(Spacer(1, 20))
    
    if news_items:
        for item in news_items[:5]:
            title = item['title'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(f"• <a href='{item['link']}' color='blue'>{title}</a>", styles['Normal']))
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("No recent news found.", styles['Normal']))
    
    story.append(Spacer(1, 20))
    
    # Final Recommendation
    story.append(Paragraph("Investment Recommendation", heading_style))
    
    recommendation = "BUY" if total_score > 12 else "HOLD" if total_score > 8 else "WATCH"
    rec_color = '#06A77D' if recommendation == 'BUY' else '#F77F00' if recommendation == 'HOLD' else '#D62828'
    
    rec_text = f"""
    <font color='{rec_color}' size='18'><b>{recommendation}</b></font><br/><br/>
    <b>Probability Score: {total_score:.1f} / 20</b><br/><br/>
    Based on comprehensive quantitative and qualitative analysis, {ticker} presents a 
    {'strong' if total_score > 12 else 'moderate' if total_score > 8 else 'limited'} investment opportunity. 
    The combination of valuation metrics, insider activity, and AI-powered forecasts suggests 
    {'significant' if total_score > 12 else 'reasonable' if total_score > 8 else 'limited'} upside potential.
    """
    
    story.append(Paragraph(rec_text, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    print(f"Professional PDF Report generated: {filename}")

def generate_report(stock_data, news_items, filename="investment_thesis.md"):
    pass
