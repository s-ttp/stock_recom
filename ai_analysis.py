import config
import os
import json
from openai import OpenAI

class AIAnalyzer:
    def __init__(self):
        self.openai_key = config.OPENAI_API_KEY
        self.mock_mode = False
        
        if self.openai_key and self.openai_key != "your-openai-key":
            self.client = OpenAI(api_key=self.openai_key)
            self.model_name = "gpt-5.1"  # Latest GPT-5 model
        else:
            print("Warning: No OpenAI API key found. Using Mock Mode for AI Analysis.")
            self.mock_mode = True

    def analyze_management(self, ticker, context_data):
        """
        Analyzes management quality based on provided context (news, summary, etc.)
        """
        if self.mock_mode:
            return {
                "score": 7,
                "analysis": "Mock Analysis: Management seems stable with decent capital allocation history.",
                "ceo_tenure": "5 years",
                "capital_allocation": "Buybacks and dividends consistent."
            }
            
        prompt = f"""
        Analyze the management quality of {ticker} based on the following context:
        {context_data}
        
        Focus on:
        1. CEO/CFO tenure and track record.
        2. Capital allocation history.
        3. Shareholder alignment.
        
        Return a JSON object with:
        - score (1-10)
        - analysis (short summary)
        - ceo_tenure
        - capital_allocation
        """
        
        return self._call_llm(prompt)

    def score_sustainability(self, ticker, context_data):
        """
        Scores business sustainability (moat, disruption risk).
        """
        if self.mock_mode:
            return {
                "score": 6,
                "analysis": "Mock Analysis: Strong brand but facing competitive headwinds.",
                "moat": "Brand",
                "disruption_risk": "Medium"
            }
            
        prompt = f"""
        Analyze the business sustainability of {ticker} based on the following context:
        {context_data}
        
        Focus on:
        1. Competitive moat.
        2. Technology disruption risk.
        3. Industry trends.
        
        Return a JSON object with:
        - score (1-10)
        - analysis (short summary)
        - moat
        - disruption_risk
        """
        
        return self._call_llm(prompt)

    def _call_llm(self, prompt):
        if self.mock_mode:
            return {
                "score": 5,
                "analysis": "Mock Analysis: API key missing.",
                "details": "N/A"
            }
            
        try:
            # Use Kimi (Moonshot) via OpenAI client
            if hasattr(self, 'client'):
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "You are a helpful financial analyst assistant. Always return valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_completion_tokens=100000,
                )
                text = response.choices[0].message.content
                
                # Clean up JSON
                text = text.replace('```json', '').replace('```', '').strip()
                
                # Handle potential empty response or non-JSON
                if not text:
                    return {'score': 5, 'analysis': "AI returned empty response."}
                    
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    print(f"JSON Decode Error. Raw text: {text[:100]}...")
                    # Fallback: try to extract JSON from text if it's embedded
                    start = text.find('{')
                    end = text.rfind('}') + 1
                    if start != -1 and end != -1:
                        try:
                            return json.loads(text[start:end])
                        except:
                            pass
                    return {'score': 5, 'analysis': "Analysis failed to parse JSON."}
                
        except Exception as e:
            print(f"Error calling AI: {e}")
            return {'score': 5, 'analysis': "Analysis failed."}

    def analyze_outlook(self, ticker, context):
        """
        Generates a summary of business outlook, industry potential, and durability.
        """
        if not hasattr(self, 'client'): 
            return "AI Analysis not available."
            
        prompt = f"""
        Analyze the business outlook and durability for {ticker} based on the following context:
        {context}
        
        Provide a concise summary (max 150 words) covering:
        1. Potential for the industry (growth/headwinds).
        2. Durability of the business model (moat/risks).
        3. Future outlook for the next 3-5 years.
        
        Format as a single cohesive paragraph.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful financial analyst assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_completion_tokens=32000,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error analyzing outlook: {e}")
            return "Outlook analysis not available."

    def generate_investment_thesis(self, ticker, context, financial_metrics, insider_data):
        """
        Generates a 5-point investment thesis based on all available data.
        """
        if not hasattr(self, 'client'):
            return None
            
        prompt = f"""
        Generate a "Deep Research" investment thesis for {ticker} consisting of exactly 5 key reasons to invest.
        
        Context:
        {context}
        
        Financial Metrics:
        {json.dumps(financial_metrics, indent=2)}
        
        Insider/Superinvestor Activity:
        {json.dumps(insider_data, indent=2)}
        
        Requirements:
        1. Output exactly 5 distinct points.
        2. Each point must be a specific, evidence-based reason (e.g., "Undervalued with P/E of X vs Industry Y", "Strong Insider Buying of $Z").
        3. Do NOT use generic fluff. Use the provided numbers.
        4. Format as a JSON list of strings. Example: ["Reason 1...", "Reason 2...", ...]
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful financial analyst assistant. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_completion_tokens=32000,
            )
            text = response.choices[0].message.content.replace('```json', '').replace('```', '').strip()
            
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                print(f"Thesis JSON Decode Error. Raw text: {text[:100]}...")
                # Fallback: try to find list
                start = text.find('[')
                end = text.rfind(']') + 1
                if start != -1 and end != -1:
                    try:
                        return json.loads(text[start:end])
                    except:
                        pass
                return None
        except Exception as e:
            print(f"Error generating thesis: {e}")
            return None

if __name__ == "__main__":
    analyzer = AIAnalyzer()
    print(analyzer.analyze_management("AAPL", "Apple Inc. is a technology company..."))
