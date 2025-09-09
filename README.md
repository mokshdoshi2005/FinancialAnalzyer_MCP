# FinanceIQ Analyzer

An MCP-powered financial document assistant that automatically parses complex financial paperwork to identify critical information, generate digestible summaries, and respond to user queries about document contents.

## Team: Fantastic404

- Moksh Doshi
- Arpit Chandra Singh
- Mohit Shukla

## Hackathon Challenge

**Theme 2:** Build a Secure MCP Server for Agents (w/ Cequence)

This project tackles the challenge of making complex financial decisions accessible to everyone by automating document analysis, fee detection, and cost optimization across various financial scenarios.

## What We Built

FinanceIQ Analyzer is an MCP (Model Context Protocol) server that processes financial documents and extracts key information. Our tool can:

### Core Features

- **Document Processing**: Extract key clauses, terms, and conditions from financial documents
- **Intelligent Summarization**: Parse complex financial documents and highlight key terms
- **Interactive Q&A:**: Calculate total costs and identify savings opportunities
- **Mortgage Document Review**: Calculate total costs and identify savings opportunities

### Real-World Impact

- Reduce review fees through automated loan comparison (Small Business Loans)
- Identify hidden fees in complex financial contracts (Investment Contracts)
- Discover potential savings through mortgage optimization (Mortgage Analysis)
- Save significant time through automated plan comparison (Insurance Plans)

## How to Run It

### Prerequisites

- Python 3.8+
- UV package manager
- Claude Desktop application

### Installation

1. Clone the repository
   ```bash
   git clone https://github.com/your-username/financeiq-analyzer.git
   cd financeiq-analyzer
   ```

2. Create virtual environment
   ```bash
   python -m venv finance-analyzer-env
   source finance-analyzer-env/bin/activate  # On Windows: finance-analyzer-env\Scripts\activate
   ```

3. Install dependencies using UV
   ```bash
   uv install
   ```

4. Install MCP CLI for testing
   ```bash
   pip install mcp-cli
   ```

5. Configure Claude Desktop
   
   Edit your Claude Desktop configuration file to include the MCP server:
   ```json
   {
     "mcpServers": {
       "finance-analyzer": {
         "command": "uv",
         "args": ["run", "python", "src/finance_analyzer_server.py"]
       }
     }
   }
   ```

6. Run the MCP server
   ```bash
   mcp run finance_analyzer_server.py
   ```

7. Test the connection
   ```bash
   mcp-cli test finance-analyzer
   ```

### Usage

Once running, you can use Claude Desktop to:

- Upload financial documents (PDFs, contracts, loan offers)
- Request high-level summaries of complex financial documents
- Ask specific questions about document content and term
- Extract key clauses and conditions from uploaded files

## Tech Stack

### Core Technologies

- **Python 3.8+** - Main programming language
- **UV Package Manager** - Fast Python package installer
- **MCP (Model Context Protocol)** - Server framework for AI integration
- **FastMCP** - Quick MCP server setup and connection management

### Required Tools

- **Claude Desktop** - AI interface and MCP client
- **MCP CLI** - Testing and development tools

### Python Libraries

- to be added

## Demo Video

[Watch Demo Video](add link)

Demo showcases real-time analysis of loan documents, investment contracts, and insurance plans with live cost comparisons and savings identification.

## What We'd Do With More Time

### Short-term Enhancements (1-2 weeks)

- **Interactive Dashboard**: Web-based UI for document upload and analysis
- **Email Integration**: Automated report generation and delivery
- **OCR Enhancement**: Better handling of scanned documents
- **Mobile App**: iOS/Android companion for quick document capture

### Medium-term Features (1-2 months)

- **Advanced ML Models**: Custom-trained models for specific financial document types
- **API Integration**: Connect with banks, insurance providers, and financial institutions
- **Trend Analysis**: Historical data tracking and market trend insights
- **Multi-user Support**: Team collaboration features for financial advisors

### Long-term Vision (3-6 months)

- **SaaS Platform**: Full-scale deployment with subscription tiers
- **Regulatory Compliance**: Integration with financial regulations and compliance checks
- **Personalized AI**: Learning user preferences for better recommendations
- **Enterprise Security**: Bank-level encryption and security protocols

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Built during Global MCP Hackathon by Team Fantastic404
