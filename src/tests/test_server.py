import pytest
import asyncio
import json
import subprocess
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mcp_server import FinancialDocumentAnalyzer as FinancialDocumentAnalyzer


class TestFinancialDocumentAnalyzer:

    @pytest.fixture
    def analyzer(self):
        return FinancialDocumentAnalyzer()

    def test_document_type_detection(self, analyzer):
        """Test document type auto-detection"""
        loan_content = """
        LOAN AGREEMENT
        Principal: $50,000
        Interest Rate: 5.25% APR
        Borrower: John Doe
        """

        doc_type = analyzer._detect_type(loan_content)
        assert doc_type == "loan_agreement"

    def test_amount_extraction(self, analyzer):
        """Test monetary amount extraction"""
        content = "The loan amount is $50,000 with a monthly payment of $943.56"
        amounts = analyzer._extract_amounts(content)
        assert "$50,000" in amounts
        assert "$943.56" in amounts

    def test_rate_extraction(self, analyzer):
        """Test interest rate extraction"""
        content = "Interest rate is 5.25% APR with a 2.5% processing fee"
        rates = analyzer._extract_rates(content)
        assert any("5.25" in rate for rate in rates)

    @pytest.mark.asyncio
    async def test_document_analysis(self, analyzer):
        """Test complete document analysis"""
        test_document = """
        PERSONAL LOAN AGREEMENT

        Principal Amount: $25,000
        Interest Rate: 6.75% APR
        Term: 48 months
        Monthly Payment: $603.48

        Borrower: Jane Smith
        Lender: ABC Financial Corp

        This loan is secured by collateral and includes penalty clauses
        for late payments and prepayment fees.
        """

        result = await analyzer._analyze_document({
            "document_content": test_document,
            "document_type": "auto_detect"
        })

        assert len(result) == 1
        response_data = json.loads(result[0].text)

        assert response_data["document_info"]["type"] == "loan_agreement"
        assert "key_findings" in response_data
        assert "risk_indicators" in response_data
        assert response_data["confidence_score"] > 0.7


# Integration test with actual MCP protocol
class TestMCPIntegration:

    @pytest.mark.asyncio
    async def test_mcp_stdio_communication(self):
        """Test MCP server via stdio"""
        # Start MCP server process
        process = await asyncio.create_subprocess_exec(
            sys.executable, "src/mcp_server.py",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            # Send initialization request
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0.0"}
                }
            }

            request_json = json.dumps(init_request) + "\n"
            process.stdin.write(request_json.encode())
            await process.stdin.drain()

            # Read initialization response
            response_line = await asyncio.wait_for(
                process.stdout.readline(), timeout=5.0
            )
            init_response = json.loads(response_line.decode().strip())

            assert "result" in init_response

            # Test tools/list
            tools_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }

            request_json = json.dumps(tools_request) + "\n"
            process.stdin.write(request_json.encode())
            await process.stdin.drain()

            response_line = await asyncio.wait_for(
                process.stdout.readline(), timeout=5.0
            )
            tools_response = json.loads(response_line.decode().strip())

            assert "result" in tools_response
            assert "tools" in tools_response["result"]
            assert len(tools_response["result"]["tools"]) >= 3

        finally:
            process.terminate()
            await process.wait()


# Load test
class TestPerformance:

    @pytest.mark.asyncio
    async def test_concurrent_analysis(self):
        """Test multiple concurrent analyses"""
        analyzer = FinancialDocumentAnalyzer()

        test_documents = [
                             "Loan agreement with $10,000 principal at 5% APR",
                             "Investment contract with 8% expected returns",
                             "Insurance policy with $100,000 coverage"
                         ] * 10  # 30 documents total

        # Process concurrently
        tasks = []
        for doc in test_documents:
            task = analyzer._analyze_document({
                "document_content": doc,
                "document_type": "auto_detect"
            })
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        assert len(results) == 30
        for result in results:
            assert len(result) == 1
            response_data = json.loads(result[0].text)
            assert "document_info" in response_data