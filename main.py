import screener
import analysis
import research
import report
import ai_analysis
import config
import time
import random
import pandas_datareader.data as web
from datetime import datetime, timedelta
import os
from recommendation_history import RecommendationHistory

def main():
    print("=== Stock Recommendation Application (Updated) ===")
    
    # Initialize recommendation history
    history = RecommendationHistory()
    history.clean_old_entries()  # Clean entries older than 1 year
    
    excluded_tickers = history.get_excluded_tickers(days=60)
    if excluded_tickers:
        print(f"\nExcluding {len(excluded_tickers)} recently recommended stocks (60-day cooldown):")
        for ticker in excluded_tickers[:5]:  # Show first 5
            info = history.get_recommendation_info(ticker)
            print(f"  - {ticker}: Last recommended {info['days_ago']} days ago")
        if len(excluded_tickers) > 5:
            print(f"  ... and {len(excluded_tickers) - 5} more")
    
    # 1. Screen Stocks (Stage 1: Fundamental Filters)
    print("\n[Phase 1] Screening Stocks (Filters: Market Cap > $1B, Net Income > 0)...")
    tickers = screener.get_all_tickers()
    # For testing speed, limit tickers if needed, but let's try full or subset
    # tickers = tickers[:20] # DEBUG: Uncomment for fast testing
    print(f"Total tickers found: {len(tickers)}")
    
    shortlist = screener.filter_stocks(tickers)
    print(f"\nShortlisted {len(shortlist)} stocks:")
    for s in shortlist:
        print(f"- {s['Ticker']}: ${s['Current_Price']} (High: ${s['52_Week_High']}, -{s['Drop_From_High_Pct']}%)")
    
    # Deduplicate shortlist
    seen_tickers = set()
    unique_shortlist = []
    for s in shortlist:
        if s['Ticker'] not in seen_tickers:
            unique_shortlist.append(s)
            seen_tickers.add(s['Ticker'])
    shortlist = unique_shortlist
    
    if not shortlist:
        print("No stocks found matching criteria.")
        return

    # 2. Analyze & Score (Stage 2 & 3)
    print("\n[Phase 2] Insider/Superinvestor Analysis & Scoring...")
    print("Strategy: Prioritizing stocks with strong smart money activity")
    
    ai = ai_analysis.AIAnalyzer()
    scored_candidates = []
    
    for stock in shortlist:
        ticker = stock['Ticker']
        print(f"Analyzing {ticker}...")
        
        try:
            # Data Fetching
            analysis_data = analysis.analyze_stock(ticker)
            context = research.get_context_for_ai(ticker)
            quarterly_financials = research.get_quarterly_financials(ticker)
            quarterly_financials = research.get_quarterly_financials(ticker)
            earnings_history = research.get_earnings_history(ticker)
            company_info = research.get_company_info(ticker)
            
            # AI Analysis
            mgmt_analysis = ai.analyze_management(ticker, context)
            sust_analysis = ai.score_sustainability(ticker, context)
            outlook_analysis = ai.analyze_outlook(ticker, context)
            
            # Generate Investment Thesis (Deep Research)
            investment_thesis = ai.generate_investment_thesis(
                ticker, 
                context, 
                company_info, 
                analysis_data['insider']
            )
            
            # NEW SCORING MODEL - Prioritize Smart Money Activity
            score = 0
            insider_score = 0
            superinvestor_score = 0
            
            # 1. PRIMARY FILTER: Insider/Superinvestor Activity (0-10 points)
            si = analysis_data['superinvestor']
            ins = analysis_data['insider']
            
            # Superinvestor scoring (0-5 points)
            # Check if superinvestor added
            if si.get('has_superinvestor_addition'):
                print(f"  Superinvestor addition found for {ticker}!")
                superinvestor_score += 3
                if si['buys'] > si['sells']:
                    superinvestor_score += 2
                elif si['buys'] > 0:
                    superinvestor_score += 1
            
            # Insider scoring (0-5 points)
            if ins:
                if ins['net_value'] > config.MIN_INSIDER_BUY_VALUE:
                    insider_score += 3  # Significant buying
                elif ins['net_value'] > 0:
                    insider_score += 2  # Net buying
                elif ins['buys'] > 0:
                    insider_score += 1  # Some buying activity
            
            smart_money_score = insider_score + superinvestor_score
            score += smart_money_score
                
            # 2. AI Qualitative Scores (0-10 points)
            score += (mgmt_analysis.get('score', 0) / 2)
            score += (sust_analysis.get('score', 0) / 2)
            
            # 3. Quantitative Bonus (0-2 points)
            if stock['Debt_Equity'] and stock['Debt_Equity'] < 0.5:
                score += 1
            if stock['Above_Low_Pct'] < 5:  # Very close to low
                score += 1
            
            scored_candidates.append({
                'ticker': ticker,
                'total_score': score,
                'smart_money_score': smart_money_score,
                'insider_score': insider_score,
                'superinvestor_score': superinvestor_score,
                'price_delta_pct': stock['Above_Low_Pct'],  # For tie-breaking
                'price_data': stock,
                'analysis_data': analysis_data,
                'quarterly_financials': quarterly_financials,
                'earnings_history': earnings_history,
                'ai_data': {
                    'management': mgmt_analysis,
                    'sustainability': sust_analysis,
                    'outlook': outlook_analysis
                },
                'financial_metrics': company_info,
                'investment_thesis': investment_thesis
            })
            
        except Exception as e:
            print(f"Error analyzing {ticker}: {e}")
            continue
    
    if not scored_candidates:
        print("No candidates after analysis.")
        return
    
    # Filter out recently recommended stocks
    original_count = len(scored_candidates)
    scored_candidates = [
        c for c in scored_candidates 
        if c['ticker'] not in excluded_tickers
    ]
    
    filtered_count = original_count - len(scored_candidates)
    if filtered_count > 0:
        print(f"\nFiltered out {filtered_count} recently recommended stock(s)")
    
    if not scored_candidates:
        print("\nNo new candidates available. All qualifying stocks were recently recommended.")
        print("Please wait for the 60-day cooldown period or expand your screening criteria.")
        return
    
    # UPDATED SORTING LOGIC:
    # 1. Primary: Sort by smart money score (insider + superinvestor)
    # 2. Secondary: Sort by total score
    # 3. Tie-breaker: Sort by price delta (lower = better return potential)
    scored_candidates.sort(
        key=lambda x: (
            -x['smart_money_score'],      # Higher smart money score first
            -x['total_score'],             # Then higher total score
            x['price_delta_pct']           # Then lower price delta (more upside)
        )
    )
    
    print("\n" + "="*60)
    print("Top Candidates (Ranked by Smart Money Activity):")
    print("="*60)
    for i, c in enumerate(scored_candidates[:5], 1):
        print(f"{i}. {c['ticker']:6s} | Smart Money: {c['smart_money_score']:2.0f}/10 | "
              f"Total: {c['total_score']:5.2f} | Price Delta: +{c['price_delta_pct']:.1f}%")
    print("="*60)
    
    # 3. Select Best Candidate
    best_candidate = scored_candidates[0]
    ticker = best_candidate['ticker']
    
    # Record this recommendation in history
    history.add_recommendation(
        ticker=ticker,
        score=best_candidate['smart_money_score'],
        price_delta=best_candidate['price_delta_pct']
    )
    print(f"\n✓ {ticker} added to recommendation history (60-day exclusion)")
    
    print(f"\n[Phase 3] Generating Report for Top Candidate: {ticker}")
    
    # Fetch price history for chart (5 years)
    print("Fetching 5-year price history for chart...")
    start_date = datetime.now() - timedelta(days=1825)  # 5 years
    end_date = datetime.now()
    try:
        try:
            price_history = web.DataReader(ticker, 'stooq', start_date, end_date)
        except:
             price_history = web.DataReader(f"{ticker}.US", 'stooq', start_date, end_date)
    except:
        price_history = None
        
    # Generate AI Price Prediction
    print("Generating AI price prediction...")
    ai_prediction = None
    if price_history is not None and not price_history.empty:
        try:
            # Use AI to predict future prices
            context = f"""
            Stock: {ticker}
            Current Price: ${best_candidate['price_data']['Current_Price']}
            5-Year Low: ${price_history['Close'].min():.2f}
            5-Year High: ${price_history['Close'].max():.2f}
            Management Score: {best_candidate['ai_data']['management'].get('score', 'N/A')}
            Sustainability Score: {best_candidate['ai_data']['sustainability'].get('score', 'N/A')}
            
            Based on this data, predict the annual growth rate for the next 5 years and key growth drivers.
            Return JSON with: annual_growth_rate (decimal), growth_drivers (string)
            """
            
            if hasattr(ai, 'client'):
                try:
                    response = ai.client.chat.completions.create(
                        model=ai.model_name,
                        messages=[
                            {"role": "system", "content": "You are a financial analyst assistant. Always return valid JSON."},
                            {"role": "user", "content": context}
                        ],
                        temperature=0.3,
                        max_completion_tokens=1000
                    )
                    import json
                    text = response.choices[0].message.content.replace('```json', '').replace('```', '').strip()
                    ai_prediction = json.loads(text)
                except Exception as e:
                    print(f"AI prediction failed: {e}")
                    ai_prediction = {
                        'annual_growth_rate': 0.10,
                        'growth_drivers': 'market expansion and operational efficiency'
                    }
            else:
                ai_prediction = {
                    'annual_growth_rate': 0.10,
                    'growth_drivers': 'market expansion and operational efficiency'
                }
        except Exception as e:
            print(f"Error in price prediction: {e}")
            ai_prediction = {
                'annual_growth_rate': 0.10,
                'growth_drivers': 'market expansion and operational efficiency'
            }
        
    # News for report
    news = research.get_news(ticker)
    
    # Generate Charts using the existing function
    charts = report.generate_charts(
        ticker,
        price_history,
        best_candidate['analysis_data']['insider'],
        ai_prediction
    )
    
    # Add P/E Trend Chart
    if 'earnings_history' in best_candidate and best_candidate['earnings_history'] and price_history is not None and not price_history.empty:
        # Convert DataFrame to list of dicts for generate_pe_chart
        price_data_list = price_history.reset_index().rename(columns={'index': 'Date'}).to_dict('records')
        charts['pe_chart'] = report.generate_pe_chart(
            price_data_list,
            best_candidate['earnings_history']
        )
    
    # Report Data
    report_data = {
        'ticker': ticker,
        'price_data': best_candidate['price_data'],
        'superinvestor': best_candidate['analysis_data']['superinvestor'],
        'insider': best_candidate['analysis_data']['insider'],
        'ai_analysis': best_candidate['ai_data'],
        'total_score': best_candidate['total_score'],
        'smart_money_score': best_candidate['smart_money_score'],
        'quarterly_financials': best_candidate.get('quarterly_financials', []),
        'earnings_history': best_candidate.get('earnings_history', []),
        'ai_prediction': ai_prediction,
        'ai_prediction': ai_prediction,
        'news': news,
        'financial_metrics': best_candidate.get('financial_metrics', {}),
        'investment_thesis': best_candidate.get('investment_thesis')
    }
    
    # Generate charts (including prediction) - ALREADY DONE ABOVE
    # charts = report.generate_charts(ticker, price_history, report_data['insider'], ai_prediction)
    
    # Output
    desktop_path = os.path.expanduser("~/Desktop")
    output_dir = os.path.join(desktop_path, "Screener Reports")
    os.makedirs(output_dir, exist_ok=True)
    
    filename = os.path.join(output_dir, f"investment_thesis_{ticker}.pdf")
    
    report.create_pdf_report(filename, report_data, charts)
    print(f"Done! Report saved to: {filename}")

if __name__ == "__main__":
    main()
