# 🚀 AI E-Commerce Lead Generation & Store Audit Agent (100% Free)

An autonomous AI Agent system built with Python, FastMCP, and Google Gemini API that finds international e-commerce stores (UK, US, Europe, Australia), extracts contact emails & founder LinkedIn profiles, audits technical conversion/tracking bottlenecks, and drafts personalized pitches ready to send.

---

## 📁 System Architecture

```
/home/hanzla/agents/
├── config.py                 # API keys, targeting settings & Talha's case study stats
├── requirements.txt          # Python dependencies (mcp, ddgs, pandas, openpyxl, google-genai)
├── mcp_server.py             # Official FastMCP server exposing tools to LLMs
├── main.py                   # Interactive CLI runner
├── scraper/
│   ├── store_finder.py       # Discovers active Shopify/e-commerce stores via search footprints
│   └── contact_enricher.py   # Extracts emails, socials & performs Google X-Ray for LinkedIn
├── auditor/
│   └── store_auditor.py      # Technical inspection for Meta Pixel, TikTok Pixel, GA4, Klaviyo, TTFB
├── agent/
│   └── pitch_generator.py    # Google Gemini Flash integration for tailored 3-channel pitches
├── exporter/
│   └── excel_exporter.py     # Formats and exports data to CSV & Excel (.xlsx)
└── output/
    ├── leads_latest.xlsx     # Latest generated spreadsheet with clickable links
    └── leads_latest.csv      # CSV export
```

---

## ⚡ Quick Start

### 1. Activate Environment
```bash
cd /home/hanzla/agents
source .venv/bin/activate
```

### 2. Run Interactive Agent
```bash
python main.py
```

### 3. Run Automated Discovery (Niche & Region)
```bash
# Example: Find and pitch 10 UK streetwear stores
python -c "from main import run_lead_generation_pipeline; run_lead_generation_pipeline('streetwear sneakers', 'UK', count=10)"
```

### 4. Audit a Single Custom Store
```bash
# Audit and generate pitch for any specific store URL
python -c "from main import process_single_store, export_leads_to_files; lead = process_single_store('https://example-uk-store.co.uk', region='UK'); export_leads_to_files([lead])"
```

---

## 🔌 Running as an MCP Server (Model Context Protocol)

To let any MCP-compatible AI client (like Claude Desktop, Antigravity, Cursor) control this agent directly:
```bash
python mcp_server.py
```

Exposed MCP Tools:
- `search_stores(niche, region, max_results)`
- `extract_contacts_and_linkedin(store_url, region)`
- `audit_ecommerce_store(store_url)`
- `generate_ai_pitches(brand_name, store_url, region, contact_data, audit_data)`
- `export_leads_to_spreadsheet(leads)`

---

## 📊 Output Columns in Generated Excel
1. **Brand Name**
2. **Store URL**
3. **Target Region** (UK, US, AU, etc.)
4. **Contact Email**
5. **Founder / Owner Name & Title**
6. **Founder LinkedIn Profile URL**
7. **Instagram Profile URL**
8. **Platform** (Shopify, WooCommerce, etc.)
9. **Meta Pixel Status**
10. **TikTok Pixel Status**
11. **Google Analytics / GTM Status**
12. **Key Gaps Identified**
13. **Custom Email Pitch (Subject + Body)**
14. **Custom LinkedIn Connection Note (<300 chars)**
15. **Custom Instagram DM Pitch**
16. **Outreach Status** (Ready to Send)
