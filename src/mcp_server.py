#!/usr/bin/env python3
import asyncio
import json
import re
from typing import Any, Dict, List
from mcp.server import Server
from mcp.types import Tool, TextContent
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FinancialDocumentAnalyzer:
    def __init__(self):
        self.server = Server("financial-document-analyzer")
        self.documents_store = {}
        self._setup_tools()
        logger.info("Financial Document Analyzer MCP Server initialized")

    def _setup_tools(self):
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available tools for financial document analysis"""
            return [
                Tool(
                    name="analyze_financial_document",
                    description="Analyze financial documents and extract key terms, risks, and compliance issues",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "document_content": {
                                "type": "string",
                                "description": "The content of the financial document to analyze"
                            },
                            "document_type": {
                                "type": "string",
                                "enum": ["loan_agreement", "investment_contract", "insurance_policy", "auto_detect"],
                                "description": "Type of financial document",
                                "default": "auto_detect"
                            }
                        },
                        "required": ["document_content"]
                    }
                ),
                Tool(
                    name="extract_key_terms",
                    description="Extract specific financial terms like interest rates, amounts, dates",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "document_content": {
                                "type": "string",
                                "description": "Document content to extract terms from"
                            },
                            "term_types": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Types of terms to extract (amount, rate, date, party)",
                                "default": ["amount", "rate", "date"]
                            }
                        },
                        "required": ["document_content"]
                    }
                ),
                Tool(
                    name="risk_assessment",
                    description="Perform risk assessment on financial document terms",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "document_content": {
                                "type": "string",
                                "description": "Document content for risk assessment"
                            },
                            "risk_categories": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Risk categories to evaluate",
                                "default": ["credit", "market", "operational"]
                            }
                        },
                        "required": ["document_content"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls from MCP clients"""
            logger.info(f"Tool called: {name} with args: {list(arguments.keys())}")

            try:
                if name == "analyze_financial_document":
                    result = await self._analyze_document(arguments)
                elif name == "extract_key_terms":
                    result = await self._extract_terms(arguments)
                elif name == "risk_assessment":
                    result = await self._assess_risk(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")

                return result

            except Exception as e:
                logger.error(f"Error in tool {name}: {str(e)}")
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Tool execution failed: {str(e)}",
                        "tool": name
                    }, indent=2)
                )]

    async def _analyze_document(self, args: Dict[str, Any]) -> List[TextContent]:
        """Main document analysis function"""
        content = args["document_content"]
        doc_type = args.get("document_type", "auto_detect")

        # Auto-detect if needed
        if doc_type == "auto_detect":
            doc_type = self._detect_type(content)

        # Perform comprehensive analysis
        analysis = {
            "document_info": {
                "type": doc_type,
                "length": len(content),
                "word_count": len(content.split())
            },
            "key_findings": self._extract_key_findings(content),
            "financial_terms": self._extract_financial_terms(content),
            "compliance_check": self._check_compliance(content, doc_type),
            "risk_indicators": self._identify_risks(content),
            "summary": self._generate_summary(content, doc_type),
            "confidence_score": self._calculate_confidence(content)
        }

        return [TextContent(
            type="text",
            text=json.dumps(analysis, indent=2)
        )]

    async def _extract_terms(self, args: Dict[str, Any]) -> List[TextContent]:
        """Extract specific financial terms"""
        content = args["document_content"]
        term_types = args.get("term_types", ["amount", "rate", "date"])

        extracted_terms = {}

        for term_type in term_types:
            if term_type == "amount":
                extracted_terms["amounts"] = self._extract_amounts(content)
            elif term_type == "rate":
                extracted_terms["rates"] = self._extract_rates(content)
            elif term_type == "date":
                extracted_terms["dates"] = self._extract_dates(content)
            elif term_type == "party":
                extracted_terms["parties"] = self._extract_parties(content)

        return [TextContent(
            type="text",
            text=json.dumps({
                "extracted_terms": extracted_terms,
                "extraction_summary": f"Extracted {sum(len(v) for v in extracted_terms.values())} terms total"
            }, indent=2)
        )]

    async def _assess_risk(self, args: Dict[str, Any]) -> List[TextContent]:
        """Perform risk assessment"""
        content = args["document_content"]
        risk_categories = args.get("risk_categories", ["credit", "market", "operational"])

        risk_assessment = {
            "overall_risk_score": 0,
            "risk_breakdown": {},
            "identified_risks": [],
            "mitigation_suggestions": []
        }

        total_risk = 0
        for category in risk_categories:
            category_risks = self._assess_category_risk(content, category)
            risk_assessment["risk_breakdown"][category] = category_risks
            total_risk += category_risks.get("score", 0)

        risk_assessment["overall_risk_score"] = round(total_risk / len(risk_categories), 2)
        risk_assessment["risk_level"] = self._categorize_risk_level(risk_assessment["overall_risk_score"])

        return [TextContent(
            type="text",
            text=json.dumps(risk_assessment, indent=2)
        )]

    def _detect_type(self, content: str) -> str:
        """Auto-detect document type"""
        content_lower = content.lower()

        loan_terms = ["loan", "borrower", "lender", "principal", "interest rate", "apr", "monthly payment"]
        investment_terms = ["investment", "portfolio", "returns", "securities", "dividend", "equity"]
        insurance_terms = ["insurance", "policy", "premium", "coverage", "deductible", "beneficiary"]

        loan_score = sum(1 for term in loan_terms if term in content_lower)
        investment_score = sum(1 for term in investment_terms if term in content_lower)
        insurance_score = sum(1 for term in insurance_terms if term in content_lower)

        if loan_score >= investment_score and loan_score >= insurance_score:
            return "loan_agreement"
        elif investment_score >= insurance_score:
            return "investment_contract"
        elif insurance_score > 0:
            return "insurance_policy"
        else:
            return "general_financial"

    def _extract_key_findings(self, content: str) -> Dict[str, Any]:
        """Extract key financial findings"""
        return {
            "monetary_amounts": self._extract_amounts(content),
            "interest_rates": self._extract_rates(content),
            "important_dates": self._extract_dates(content),
            "key_parties": self._extract_parties(content)
        }

    def _extract_amounts(self, content: str) -> List[str]:
        """Extract monetary amounts"""
        patterns = [
            r'\$[\d,]+(?:\.\d{2})?',  # $1,000.00
            r'USD\s*[\d,]+(?:\.\d{2})?',  # USD 1000.00
            r'[\d,]+(?:\.\d{2})?\s*dollars?'  # 1000 dollars
        ]
        amounts = []
        for pattern in patterns:
            amounts.extend(re.findall(pattern, content, re.IGNORECASE))
        return list(set(amounts))

    def _extract_rates(self, content: str) -> List[str]:
        """Extract interest rates and percentages"""
        patterns = [
            r'\d+\.?\d*\s*%',  # 5.25%
            r'\d+\.?\d*\s*percent',  # 5.25 percent
            r'APR[:\s]*\d+\.?\d*\s*%?'  # APR: 5.25%
        ]
        rates = []
        for pattern in patterns:
            rates.extend(re.findall(pattern, content, re.IGNORECASE))
        return list(set(rates))

    def _extract_dates(self, content: str) -> List[str]:
        """Extract dates"""
        patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b',  # MM/DD/YYYY
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',  # YYYY/MM/DD
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4}\b'  # Month DD, YYYY
        ]
        dates = []
        for pattern in patterns:
            dates.extend(re.findall(pattern, content, re.IGNORECASE))
        return list(set(dates))

    def _extract_parties(self, content: str) -> List[str]:
        """Extract party names (simplified)"""
        # Look for common party indicators
        party_patterns = [
            r'Borrower[:\s]+([A-Z][a-zA-Z\s]+)',
            r'Lender[:\s]+([A-Z][a-zA-Z\s]+)',
            r'Client[:\s]+([A-Z][a-zA-Z\s]+)',
            r'Company[:\s]+([A-Z][a-zA-Z\s]+)'
        ]
        parties = []
        for pattern in party_patterns:
            matches = re.findall(pattern, content)
            parties.extend([match.strip() for match in matches])
        return list(set(parties))

    def _extract_financial_terms(self, content: str) -> Dict[str, Any]:
        """Extract specific financial terms based on document type"""
        terms = {}
        content_lower = content.lower()

        # Common financial terms
        if "apr" in content_lower:
            apr_match = re.search(r'apr[:\s]*(\d+\.?\d*\s*%?)', content_lower)
            if apr_match:
                terms["apr"] = apr_match.group(1)

        if "term" in content_lower or "duration" in content_lower:
            term_patterns = [
                r'(\d+)\s*(?:years?|months?)',
                r'term[:\s]*(\d+\s*(?:years?|months?))'
            ]
            for pattern in term_patterns:
                match = re.search(pattern, content_lower)
                if match:
                    terms["term"] = match.group(1)
                    break

        return terms

    def _check_compliance(self, content: str, doc_type: str) -> Dict[str, Any]:
        """Check basic compliance requirements"""
        compliance = {
            "status": "pending_review",
            "issues": [],
            "recommendations": [],
            "score": 85  # Default score
        }

        content_lower = content.lower()

        # Common compliance checks
        required_disclosures = {
            "loan_agreement": ["apr", "total amount", "payment schedule"],
            "investment_contract": ["risk disclosure", "fees", "returns"],
            "insurance_policy": ["coverage limits", "exclusions", "premium"]
        }

        if doc_type in required_disclosures:
            missing = []
            for disclosure in required_disclosures[doc_type]:
                if disclosure.replace(" ", "") not in content_lower.replace(" ", ""):
                    missing.append(disclosure)

            if missing:
                compliance["issues"].extend([f"Missing {item} disclosure" for item in missing])
                compliance["score"] -= len(missing) * 10

        # Set overall status
        if compliance["score"] >= 90:
            compliance["status"] = "compliant"
        elif compliance["score"] >= 70:
            compliance["status"] = "minor_issues"
        else:
            compliance["status"] = "major_issues"

        return compliance

    def _identify_risks(self, content: str) -> List[Dict[str, Any]]:
        """Identify potential risk factors"""
        risks = []
        content_lower = content.lower()

        risk_indicators = [
            {"keyword": "variable rate", "risk": "Interest Rate Risk", "severity": "medium"},
            {"keyword": "balloon payment", "risk": "Payment Shock Risk", "severity": "high"},
            {"keyword": "penalty", "risk": "Penalty Risk", "severity": "medium"},
            {"keyword": "default", "risk": "Default Risk", "severity": "high"},
            {"keyword": "collateral", "risk": "Collateral Risk", "severity": "medium"},
            {"keyword": "prepayment", "risk": "Prepayment Risk", "severity": "low"}
        ]

        for indicator in risk_indicators:
            if indicator["keyword"] in content_lower:
                risks.append({
                    "type": indicator["risk"],
                    "severity": indicator["severity"],
                    "description": f"Document contains {indicator['keyword']} terms"
                })

        return risks

    def _assess_category_risk(self, content: str, category: str) -> Dict[str, Any]:
        """Assess risk for specific category"""
        risk_scores = {
            "credit": self._assess_credit_risk(content),
            "market": self._assess_market_risk(content),
            "operational": self._assess_operational_risk(content)
        }

        return risk_scores.get(category, {"score": 0, "factors": []})

    def _assess_credit_risk(self, content: str) -> Dict[str, Any]:
        """Assess credit-related risks"""
        score = 0
        factors = []
        content_lower = content.lower()

        if "no credit check" in content_lower:
            score += 30
            factors.append("No credit verification required")

        if "high interest" in content_lower or "subprime" in content_lower:
            score += 25
            factors.append("High interest rate indicators")

        return {"score": min(score, 100), "factors": factors}

    def _assess_market_risk(self, content: str) -> Dict[str, Any]:
        """Assess market-related risks"""
        score = 0
        factors = []
        content_lower = content.lower()

        if "variable" in content_lower or "adjustable" in content_lower:
            score += 20
            factors.append("Variable rate exposure")

        if "market conditions" in content_lower:
            score += 15
            factors.append("Market condition dependencies")

        return {"score": min(score, 100), "factors": factors}

    def _assess_operational_risk(self, content: str) -> Dict[str, Any]:
        """Assess operational risks"""
        score = 0
        factors = []
        content_lower = content.lower()

        if "manual process" in content_lower:
            score += 10
            factors.append("Manual processing risks")

        if "third party" in content_lower:
            score += 15
            factors.append("Third-party dependencies")

        return {"score": min(score, 100), "factors": factors}

    def _categorize_risk_level(self, score: float) -> str:
        """Categorize overall risk level"""
        if score >= 70:
            return "high"
        elif score >= 40:
            return "medium"
        elif score >= 20:
            return "low"
        else:
            return "minimal"

    def _generate_summary(self, content: str, doc_type: str) -> str:
        """Generate document summary"""
        word_count = len(content.split())
        char_count = len(content)

        return (f"Analyzed {doc_type} document with {word_count} words "
                f"({char_count} characters). Key financial terms extracted, "
                f"compliance checked, and risk assessment completed.")

    def _calculate_confidence(self, content: str) -> float:
        """Calculate analysis confidence score"""
        # Simple confidence based on content length and structure
        base_confidence = 0.7

        if len(content) > 1000:
            base_confidence += 0.1
        if len(content) > 5000:
            base_confidence += 0.1

        # Check for structured content
        if any(term in content.lower() for term in ["section", "clause", "paragraph"]):
            base_confidence += 0.05

        return min(base_confidence, 0.95)


# Main entry point for stdio
async def main():
    """Main entry point for MCP server"""
    analyzer = FinancialDocumentAnalyzer()

    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await analyzer.server.run(
            read_stream,
            write_stream,
            analyzer.server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())