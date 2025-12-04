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

# Professional Color Scheme
NAVY_BLUE = colors.HexColor('#1a3a52')
GOLD = colors.HexColor('#d4af37')
LIGHT_GRAY = colors.HexColor('#f8f9fa')
DARK_GRAY = colors.HexColor('#6c757d')
ACCENT_BLUE = colors.HexColor('#2E86AB')
SUCCESS_GREEN = colors.HexColor('#28a745')
WARNING_YELLOW = colors.HexColor('#ffc107')
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

class NumberedCanvas(canvas.Canvas):
    """Custom canvas for headers and footers"""
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []
        self.ticker = kwargs.get('ticker', '')
        self.company_name = kwargs.get('company_name', '')

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, page_count):
        """Draw header and footer on each page"""
        page_num = self._pageNumber
        
        # Skip header/footer on cover page (page 1)
        if page_num == 1:
            return
            
        # Header
        self.saveState()
        self.setStrokeColor(NAVY_BLUE)
        self.setLineWidth(2)
        self.line(0.5*inch, letter[1] - 0.4*inch, letter[0] - 0.5*inch, letter[1] - 0.4*inch)
        
        # Header text
        self.setFont('Helvetica', 9)
        self.setFillColor(DARK_GRAY)
        self.drawString(0.5*inch, letter[1] - 0.35*inch, self.ticker)
        self.drawCentredString(letter[0]/2, letter[1] - 0.35*inch, "Investment Analysis Report")
        self.drawRightString(letter[0] - 0.5*inch, letter[1] - 0.35*inch, f"Page {page_num - 1} of {page_count - 1}")
        
        # Footer
        self.setLineWidth(1)
        self.line(0.5*inch, 0.5*inch, letter[0] - 0.5*inch, 0.5*inch)
        
        self.setFont('Helvetica', 7)
        self.setFillColor(DARK_GRAY)
        self.drawString(0.5*inch, 0.35*inch, f"Generated: {datetime.now().strftime('%B %d, %Y')}")
        self.drawCentredString(letter[0]/2, 0.35*inch, "For informational purposes only. Not investment advice.")
        
        self.restoreState()

def create_cover_page(story, report_data, styles):
    """Creates a professional cover page"""
    ticker = report_data['ticker']
    company_name = report_data.get('company_name', ticker)
    subtitle = report_data.get('subtitle', 'Investment Opportunity')
    total_score = report_data.get('total_score', 0)
    
    # Determine recommendation
    if total_score > 12:
        recommendation = "BUY"
        rec_color = SUCCESS_GREEN
    elif total_score > 8:
        recommendation = "HOLD"
        rec_color = WARNING_YELLOW
    else:
        recommendation = "WATCH"
        rec_color = DARK_GRAY
    
    # Spacer from top
    story.append(Spacer(1, 1.5*inch))
    
    # Report Type
    report_type_style = ParagraphStyle(
        'ReportType',
        parent=styles['Normal'],
        fontSize=12,
        textColor=DARK_GRAY,
        alignment=TA_CENTER,
        spaceAfter=20,
        letterSpacing=2
    )
    story.append(Paragraph("EQUITY RESEARCH", report_type_style))
    
    # Decorative line
    story.append(Spacer(1, 0.5*inch))
    
    # Company Name and Ticker Combined
    company_style = ParagraphStyle(
        'CompanyName',
        parent=styles['Title'],
        fontSize=32,
        textColor=NAVY_BLUE,
        alignment=TA_CENTER,
        spaceAfter=20,
        fontName='Helvetica-Bold',
        leading=40
    )
    story.append(Paragraph(f"{company_name} ({ticker})", company_style))
    
    # Subtitle/Tagline (AI Summary)
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=16,
        textColor=ACCENT_BLUE,
        alignment=TA_CENTER,
        spaceAfter=40,
        fontName='Helvetica-Oblique',
        leading=20
    )
    story.append(Paragraph(subtitle, subtitle_style))
    
    # Recommendation Badge
    badge_data = [[recommendation]]
    badge_table = Table(badge_data, colWidths=[2.5*inch])
    badge_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), rec_color),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 28),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ('ROUNDEDCORNERS', [10, 10, 10, 10])
    ]))
    story.append(badge_table)
    
    story.append(Spacer(1, 0.5*inch))
    
    # Key Metrics Box
    price = report_data['price_data']['Current_Price']
    smart_money = report_data.get('smart_money_score', 0)
    
    metrics_data = [
        ["Current Price", f"${price:.2f}"],
        ["Smart Money Score", f"{smart_money}/10"],
        ["Report Date", datetime.now().strftime('%B %d, %Y')]
    ]
    
    metrics_table = Table(metrics_data, colWidths=[2*inch, 2*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
        ('TEXTCOLOR', (0, 0), (-1, -1), NAVY_BLUE),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6'))
    ]))
    story.append(metrics_table)
    
    # Page break after cover
    story.append(PageBreak())

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
    # Custom document template with headers/footers
    doc = SimpleDocTemplate(
        filename, 
        pagesize=letter,
        topMargin=0.75*inch, 
        bottomMargin=0.75*inch,
        leftMargin=0.5*inch,
        rightMargin=0.5*inch
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    ticker = report_data['ticker']
    company_name = report_data.get('company_name', ticker)
    price_data = report_data['price_data']
    superinvestor = report_data['superinvestor']
    insider = report_data['insider']
    ai_data = report_data.get('ai_analysis', {})
    news_items = report_data.get('news', [])
    total_score = report_data.get('total_score', 0)
    
    # Create cover page first - REMOVED per user request
    # create_cover_page(story, report_data, styles)
    
    # Custom Styles with Professional Colors
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=32,
        textColor=NAVY_BLUE,
        spaceAfter=30,
        alignment=1,  # Center
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=NAVY_BLUE,
        spaceBefore=20,
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=ACCENT_BLUE,
        spaceBefore=10,
        spaceAfter=8,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#333333'),
        spaceBefore=6,
        spaceAfter=6
    )
    
    # Report Header
    report_type_style = ParagraphStyle(
        'ReportType',
        parent=styles['Normal'],
        fontSize=12,
        textColor=DARK_GRAY,
        alignment=TA_CENTER,
        spaceAfter=20,
        letterSpacing=2
    )
    story.append(Paragraph("EQUITY RESEARCH", report_type_style))
    
    # Company Name and Ticker Combined
    company_name = report_data.get('company_name', ticker)
    company_style = ParagraphStyle(
        'CompanyName',
        parent=styles['Title'],
        fontSize=32,
        textColor=NAVY_BLUE,
        alignment=TA_CENTER,
        spaceAfter=20,
        fontName='Helvetica-Bold',
        leading=40
    )
    story.append(Paragraph(f"{company_name} ({ticker})", company_style))
    
    # Subtitle/Tagline (AI Summary)
    subtitle = report_data.get('subtitle', 'Value Investment Opportunity')
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=16,
        textColor=ACCENT_BLUE,
        alignment=TA_CENTER,
        spaceAfter=40,
        fontName='Helvetica-Oblique',
        leading=20
    )
    story.append(Paragraph(subtitle, subtitle_style))
    
    # Executive Summary Box (Enhanced)
    story.append(Paragraph("1. Executive Summary", heading_style))
    
    # Use format_billions for Market Cap
    mc = report_data['price_data'].get('Market_Cap')
    mc_str = format_billions(mc)
    
    # Calculate Down from High %
    down_from_high = "N/A"
    high_val = "N/A"
    if report_data['price_data'].get('52_Week_High') and report_data['price_data']['52_Week_High'] != 'N/A':
        high = float(report_data['price_data']['52_Week_High'])
        current = float(report_data['price_data']['Current_Price'])
        pct_down = ((high - current) / high) * 100
        down_from_high = f"{pct_down:.1f}%"
        high_val = f"${high:.2f}"
        
    # Enhanced Executive Summary with professional styling
    summary_data = [
        ["Metric", "Value", "Metric", "Value"],
        ["Current Price", f"${report_data['price_data']['Current_Price']:.2f}", "52-Week High", high_val],
        ["Market Cap", mc_str, "Drop from High", down_from_high],
        ["Smart Money Score", f"{report_data['smart_money_score']}/10", "Total Score", f"{total_score:.1f}/20"]
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 1.5*inch, 2*inch, 1.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('BACKGROUND', (0, 1), (-1, -1), LIGHT_GRAY),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY])
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 15))
    
    summary_text = f"""
    <b>Investment Recommendation:</b> {'BUY' if total_score > 12 else 'HOLD' if total_score > 8 else 'WATCH'}<br/>
    <b>Key Thesis:</b> {report_data['ticker']} is trading {down_from_high} below its 52-week high. 
    {'Strong' if total_score > 12 else 'Moderate' if total_score > 8 else 'Weak'} insider/superinvestor activity 
    and {'positive' if ai_data.get('management', {}).get('score', 0) > 6 else 'mixed'} management quality 
    signals suggest {'compelling' if total_score > 12 else 'reasonable' if total_score > 8 else 'limited'} 
    upside potential.
    """
    
    summary_table_text = Table([[Paragraph(summary_text, styles['Normal'])]], colWidths=[6.5*inch])
    summary_table_text.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F0F4F8')),
        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#2E86AB')),
        ('PADDING', (0, 0), (-1, -1), 15),
    ]))
    story.append(summary_table_text)
    story.append(Spacer(1, 20))
    
    # Page Break
    story.append(PageBreak())
    
    # 2. Valuation Metrics
    story.append(Paragraph("2. Valuation Metrics", heading_style))
    
    # Key Valuation Metrics Table
    story.append(Paragraph("Key Valuation Metrics", subheading_style))
    metrics = report_data.get('financial_metrics', {})
    
    val_metrics_data = [
        ["Metric", "Value", "Metric", "Value"],
        ["P/E Ratio", f"{metrics.get('PERatio', 'N/A')}", "Forward P/E", f"{metrics.get('forwardPE', 'N/A')}"],
        ["PEG Ratio", f"{metrics.get('PEGRatio', 'N/A')}", "Price/Sales", f"{metrics.get('PriceToSalesRatioTTM', 'N/A')}"],
        ["Price/Book", f"{metrics.get('PriceToBookRatio', 'N/A')}", "EV/EBITDA", f"{metrics.get('EVToEBITDA', 'N/A')}"],
        ["Dividend Yield", f"{metrics.get('DividendYield', 'N/A')}", "Beta", f"{metrics.get('Beta', 'N/A')}"]
    ]
    
    val_metrics_table = Table(val_metrics_data, colWidths=[2*inch, 1.5*inch, 2*inch, 1.5*inch])
    val_metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY])
    ]))
    story.append(val_metrics_table)
    story.append(Spacer(1, 20))
    
    # 5-Year Price Chart
    if 'price_chart' in charts:
        story.append(Image(charts['price_chart'], width=6*inch, height=3*inch))
        story.append(Spacer(1, 20))

    # 5-Year P/E Ratio Chart
    if 'pe_chart' in charts:
        story.append(Image(charts['pe_chart'], width=6*inch, height=3*inch))
        story.append(Spacer(1, 20))
    
    # Page Break
    story.append(PageBreak())
    
    # 3. Smart Money Analysis
    story.append(Paragraph("3. Smart Money Analysis", heading_style))
    
    si = report_data.get('superinvestor', {})
    ins = report_data.get('insider', {})
    
    # Superinvestor details
    buyers_list = si.get('buyers', [])
    sellers_list = si.get('sellers', [])
    
    if buyers_list:
        buyers_text = ", ".join(buyers_list)
    else:
        buyers_text = "None"
    
    if sellers_list:
        sellers_text = ", ".join(sellers_list)
    else:
        sellers_text = "None"
    
    sm_data = [
        ["Category", "Activity", "Details"],
        ["Superinvestors", f"Buys: {si.get('buys', 0)} | Sells: {si.get('sells', 0)}", 
         f"Total Activity: {si.get('total_activity', 0)}"],
        ["Buyers", "", buyers_text],
        ["Sellers", "", sellers_text],
        ["Insiders", f"Buys: {ins.get('buys', 0)} | Sells: {ins.get('sells', 0)}", 
         f"Net Value: ${ins.get('net_value', 0):,.0f}"]
    ]
    
    t2 = Table(sm_data, colWidths=[1.5*inch, 2*inch, 3.5*inch])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY_BLUE),
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
    
    # 4. Income Statement Analysis
    story.append(Paragraph("4. Income Statement Analysis", heading_style))
    
    q_financials = report_data.get('quarterly_financials', [])
    if q_financials:
        q_data = [["Quarter Ending", "Revenue ($M)", "Net Income ($M)", "EPS ($)"]]
        for q in q_financials:
            eps_value = q.get('reportedEPS')
            # Display actual EPS value (including zero and negatives), only show N/A if truly missing
            if eps_value is not None:
                eps_display = f"{eps_value:.2f}"
            else:
                eps_display = "N/A"
            
            q_data.append([
                q['fiscalDateEnding'],
                format_billions(q['totalRevenue']).replace('$', ''), # Remove $ since header has ($B)
                format_billions(q['netIncome']).replace('$', ''),
                eps_display
            ])
            
        t3 = Table(q_data, colWidths=[1.8*inch, 1.8*inch, 1.8*inch, 1.6*inch])
        t3.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), NAVY_BLUE),
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
    
    # AI Analysis for Income Statement
    story.append(Spacer(1, 10))
    story.append(Paragraph("Income Statement Summary", subheading_style))
    is_summary = ai_data.get('financial_statement_analysis', 'Analysis not available.')
    story.append(Paragraph(is_summary, styles['Normal']))
        
    story.append(Spacer(1, 20))

    # 5. Balance Sheet Analysis
    story.append(Paragraph("5. Balance Sheet Analysis", heading_style))
    
    # Balance Sheet Data
    balance_sheet = report_data.get('balance_sheet_data', {})
    if balance_sheet:
        # Summary Table - Key Financial Position Metrics
        story.append(Paragraph("Financial Position Summary", subheading_style))
        
        # Calculate derived metrics
        total_assets = balance_sheet.get('Total Assets', 0)
        total_liabilities = balance_sheet.get('Total Liabilities', 0)
        total_equity = balance_sheet.get('Total Equity', 0)
        cash = balance_sheet.get('Cash And Cash Equivalents', 0)
        total_debt = balance_sheet.get('Total Debt', 0)
        working_capital = balance_sheet.get('Working Capital', 0)
        
        # Net Debt = Total Debt - Cash
        net_debt = total_debt - cash
        
        # Debt-to-Equity Ratio
        debt_to_equity = (total_debt / total_equity) if total_equity != 0 else 0
        
        # Equity Ratio = Total Equity / Total Assets
        equity_ratio = (total_equity / total_assets * 100) if total_assets != 0 else 0
        
        summary_data = [
            ["Metric", "Value ($B)", "Metric", "Value"],
            ["Total Assets", format_billions(total_assets).replace('$', ''), "Total Equity", format_billions(total_equity).replace('$', '')],
            ["Total Liabilities", format_billions(total_liabilities).replace('$', ''), "Equity Ratio", f"{equity_ratio:.1f}%"],
            ["Cash & Equivalents", format_billions(cash).replace('$', ''), "Total Debt", format_billions(total_debt).replace('$', '')],
            ["Net Debt Position", format_billions(net_debt).replace('$', ''), "Debt-to-Equity", f"{debt_to_equity:.2f}"],
            ["Working Capital", format_billions(working_capital).replace('$', ''), "Date", balance_sheet.get('Date', 'N/A')]
        ]
        
        summary_table = Table(summary_data, colWidths=[2.2*inch, 1.3*inch, 2.2*inch, 1.3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), NAVY_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 1), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY])
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 15))
        
        # Key Insights Box
        net_debt_status = "Net Cash Position" if net_debt < 0 else "Net Debt Position"
        leverage_status = "Low" if debt_to_equity < 0.5 else "Moderate" if debt_to_equity < 1.5 else "High"
        
        insights_text = f"""
        <b>Cash & Debt Position:</b> {net_debt_status} of {format_billions(abs(net_debt))}. 
        The company maintains a <b>{leverage_status}</b> leverage profile with a debt-to-equity ratio of {debt_to_equity:.2f}.<br/>
        <b>Capital Structure:</b> Equity represents {equity_ratio:.1f}% of total assets, 
        with working capital of {format_billions(working_capital)}.
        """
        
        insights_table = Table([[Paragraph(insights_text, styles['Normal'])]], colWidths=[6.5*inch])
        insights_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F0F4F8')),
            ('BOX', (0, 0), (-1, -1), 1, ACCENT_BLUE),
            ('PADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(insights_table)
        story.append(Spacer(1, 12))
    
    # AI Analysis of Balance Sheet
    story.append(Paragraph("Balance Sheet Quality Assessment", subheading_style))
    bs_summary = ai_data.get('balance_sheet_analysis', 'Analysis not available.')
    story.append(Paragraph(bs_summary, styles['Normal']))
    
    story.append(Spacer(1, 20))

    # 6. Cash Flow Analysis
    story.append(Paragraph("6. Cash Flow Analysis", heading_style))
    
    # Cash Flow Data
    cash_flow = report_data.get('cash_flow_data', {})
    if cash_flow:
        # Summary Table - Key Cash Flow Metrics
        story.append(Paragraph("Cash Flow Summary", subheading_style))
        
        # Extract values
        operating_cf = cash_flow.get('Operating Cash Flow', 0)
        investing_cf = cash_flow.get('Investing Cash Flow', 0)
        financing_cf = cash_flow.get('Financing Cash Flow', 0)
        capex = cash_flow.get('Capital Expenditure', cash_flow.get('Capital Expenditures', 0))
        free_cf = cash_flow.get('Free Cash Flow', 0)
        dividends = cash_flow.get('Dividends Paid', 0)
        
        # Calculate FCF if not provided
        if free_cf == 0 and operating_cf != 0:
            free_cf = operating_cf - abs(capex)
        
        # Calculate FCF Margin (FCF / Operating CF)
        fcf_margin = (free_cf / operating_cf * 100) if operating_cf != 0 else 0
        
        summary_data = [
            ["Metric", "Value ($B)", "Metric", "Value ($B)"],
            ["Operating Cash Flow", format_billions(operating_cf).replace('$', ''), "Free Cash Flow", format_billions(free_cf).replace('$', '')],
            ["Investing Cash Flow", format_billions(investing_cf).replace('$', ''), "FCF Margin", f"{fcf_margin:.1f}%"],
            ["Financing Cash Flow", format_billions(financing_cf).replace('$', ''), "Capital Expenditures", format_billions(abs(capex)).replace('$', '')],
            ["Dividends Paid", format_billions(abs(dividends)).replace('$', ''), "Date", cash_flow.get('Date', 'N/A')]
        ]
        
        summary_table = Table(summary_data, colWidths=[2.2*inch, 1.3*inch, 2.2*inch, 1.3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), NAVY_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 1), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY])
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 15))
        
        # Key Insights Box
        fcf_status = "Positive" if free_cf > 0 else "Negative"
        fcf_color = "green" if free_cf > 0 else "red"
        cash_generation = "Strong" if fcf_margin > 20 else "Moderate" if fcf_margin > 10 else "Weak"
        
        insights_text = f"""
        <b>Free Cash Flow:</b> <font color='{fcf_color}'>{fcf_status} FCF of {format_billions(abs(free_cf))}</font> 
        representing a {cash_generation.lower()} cash generation profile with {fcf_margin:.1f}% FCF margin.<br/>
        <b>Capital Allocation:</b> Operating activities generated {format_billions(operating_cf)}, 
        with {format_billions(abs(capex))} invested in capital expenditures 
        and {format_billions(abs(dividends))} returned to shareholders via dividends.
        """
        
        insights_table = Table([[Paragraph(insights_text, styles['Normal'])]], colWidths=[6.5*inch])
        insights_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F0F4F8')),
            ('BOX', (0, 0), (-1, -1), 1, ACCENT_BLUE),
            ('PADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(insights_table)
        story.append(Spacer(1, 12))
    
    # AI Analysis of Cash Flow
    story.append(Paragraph("Cash Flow Quality Assessment", subheading_style))
    cf_summary = ai_data.get('cash_flow_analysis', 'Analysis not available.')
    story.append(Paragraph(cf_summary, styles['Normal']))
    
    story.append(Spacer(1, 20))
    
    # 7. Analyst and AI-Powered 5-Year Price Forecasts
    story.append(Paragraph("7. Analyst and AI-Powered 5-Year Price Forecasts", heading_style))
    
    # Analyst Forecasts
    metrics = report_data.get('financial_metrics', {})
    target_price = metrics.get('targetMeanPrice')
    current_price = report_data.get('price_data', {}).get('Current_Price')
    
    if target_price and current_price:
        upside_pct = ((target_price - current_price) / current_price) * 100
        upside_str = f"+{upside_pct:.1f}%" if upside_pct > 0 else f"{upside_pct:.1f}%"
        color = "green" if upside_pct > 0 else "red"
        
        analyst_text = f"""
        <b>Analyst Consensus Target:</b> ${target_price:.2f} 
        (Implied Upside: <font color='{color}'>{upside_str}</font>)
        """
        story.append(Paragraph(analyst_text, styles['Normal']))
        story.append(Spacer(1, 12))
    else:
        story.append(Paragraph("Analyst consensus target unavailable.", styles['Normal']))
        story.append(Spacer(1, 12))
    
    # AI Prediction Chart
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
    
    # Page Break
    story.append(PageBreak())
    
    story.append(Spacer(1, 20))
    
    # 8. AI Analysis & Business Outlook
    story.append(Paragraph("8. AI Analysis & Business Outlook", heading_style))
    
    mgmt = ai_data.get('management', {})
    story.append(Paragraph(f"<b>Management Quality:</b> {mgmt.get('score', 'N/A')}/10", subheading_style))
    story.append(Paragraph(f"{mgmt.get('analysis', 'Analysis unavailable')}", styles['Normal']))
    story.append(Spacer(1, 12))
    
    sust = ai_data.get('sustainability', {})
    story.append(Paragraph(f"<b>Business Sustainability:</b> {sust.get('score', 'N/A')}/10", subheading_style))
    story.append(Paragraph(f"{sust.get('analysis', 'Analysis unavailable')}", styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Business Outlook
    story.append(Paragraph("<b>Business Outlook & Durability</b>", subheading_style))
    story.append(Paragraph(ai_data.get('outlook', 'Analysis unavailable'), styles['Normal']))
    
    story.append(Spacer(1, 20))
    
    # 9. Five Key Investment Reasons
    story.append(Paragraph("9. Five Key Investment Reasons", heading_style))
    
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
    
    story.append(Spacer(1, 20))
    
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
    
    # Build PDF with custom canvas for headers/footers
    def create_canvas(*args, **kwargs):
        kwargs['ticker'] = ticker
        kwargs['company_name'] = company_name
        return NumberedCanvas(*args, **kwargs)
    
    doc.build(story, canvasmaker=create_canvas)
    print(f"Professional PDF Report generated: {filename}")

def generate_report(stock_data, news_items, filename="investment_thesis.md"):
    pass
