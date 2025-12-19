"""Unit tests for the IRIS LangGraph agent router."""
import unittest
from unittest.mock import MagicMock, patch
from typing import Dict, Any


class TestAgentRouter(unittest.TestCase):
    """Test suite for the agent router logic."""

    def setUp(self):
        """Set up test fixtures."""
        # Import here to avoid requiring Ollama at module load time
        from core.agents.agent_router import classify_intent, AgentState

    def test_classify_intent_advice(self):
        """Test that price/analyze queries are classified as ADVICE."""
        from core.agents.agent_router import classify_intent
        
        state: Dict[str, Any] = {
            "user_id": "test_user",
            "messages": [("human", "What is the current price of TSLA?")],
            "intent": "",
            "tool_calls": []
        }
        
        result = classify_intent(state)
        self.assertEqual(result["intent"], "ADVICE")

    def test_classify_intent_profile_update(self):
        """Test that risk/goal queries are classified as ADVICE (merged intent)."""
        from core.agents.agent_router import classify_intent
        
        state: Dict[str, Any] = {
            "user_id": "test_user",
            "messages": [("human", "I want to update my risk tolerance to moderate")],
            "intent": "",
            "tool_calls": []
        }
        
        result = classify_intent(state)
        self.assertEqual(result["intent"], "ADVICE")

    def test_classify_intent_general_chat(self):
        """Test that unrelated queries are classified as GENERAL_CHAT."""
        from core.agents.agent_router import classify_intent
        
        state: Dict[str, Any] = {
            "user_id": "test_user",
            "messages": [("human", "Hello, how are you?")],
            "intent": "",
            "tool_calls": []
        }
        
        result = classify_intent(state)
        self.assertEqual(result["intent"], "GENERAL_CHAT")

    @patch('core.agents.agent_router.get_past_conversations')
    @patch('core.agents.agent_router.get_activity_log')
    @patch('core.agents.agent_router.get_portfolio_details')
    @patch('core.agents.agent_router.get_market_data')
    @patch('core.agents.agent_router.lookup_rag_context')
    @patch('core.agents.agent_router.build_user_context')
    def test_fetch_financial_data(self, mock_user_context, mock_rag, mock_market, mock_portfolio, mock_activity, mock_history):
        """Test that fetch_financial_data retrieves and formats context."""
        from core.agents.agent_router import fetch_financial_data
        
        # Mock the tool responses
        mock_user_context.return_value = "User Profile: Risk=High. Holdings: TSLA."
        mock_market.return_value = "SPY: $450.00, 5-day: +2.5%"
        mock_rag.return_value = "Market outlook is positive"
        mock_portfolio.return_value = "Total Value: $10000"
        mock_activity.return_value = "No recent activity"
        mock_history.return_value = ""
        
        state: Dict[str, Any] = {
            "user_id": "test_user",
            "messages": [("human", "Should I invest in tech stocks?")],
            "intent": "ADVICE",
            "tool_outputs": {}
        }
        
        result = fetch_financial_data(state)
        
        # Verify that tool_outputs are populated properly
        self.assertIn("tool_outputs", result)
        self.assertIn("context_data", result["tool_outputs"])
        self.assertIn("[Market Setup]", result["tool_outputs"]["context_data"])
        self.assertIn("User Profile", result["tool_outputs"]["context_data"])

    @patch('core.agents.agent_router.LLM')
    def test_generate_response(self, mock_llm):
        """Test that generate_response invokes the LLM correctly."""
        from core.agents.agent_router import generate_response
        
        # Mock LLM response
        mock_llm.invoke.return_value = "Based on current market conditions, tech stocks show moderate growth potential."
        
        state: Dict[str, Any] = {
            "user_id": "test_user",
            "messages": [
                ("human", "Should I invest in tech?")
            ],
            "tool_outputs": {"context_data": "SPY: $450. RAG Data=Positive outlook."},
            "intent": "ADVICE"
        }
        
        result = generate_response(state)
        
        # Verify that an AI message was added
        self.assertIn("messages", result)
        self.assertEqual(len(result["messages"]), 1)
        self.assertEqual(result["messages"][0][0], "ai")
        self.assertIsInstance(result["messages"][0][1], str)

    def test_router_advice(self):
        """Test that ADVICE intent routes to fetch_data node."""
        from core.agents.agent_router import router
        
        state: Dict[str, Any] = {
            "user_id": "test_user",
            "messages": [],
            "intent": "ADVICE",
            "tool_outputs": {}
        }
        
        result = router(state)
        self.assertEqual(result, "fetch_data")

    def test_router_general(self):
        """Test that non-ADVICE intent now routes to fetch_data for context."""
        from core.agents.agent_router import router
        
        state: Dict[str, Any] = {
            "user_id": "test_user",
            "messages": [],
            "intent": "GENERAL_CHAT",
            "tool_outputs": {}
        }
        
        result = router(state)
        self.assertEqual(result, "fetch_data")


if __name__ == '__main__':
    unittest.main()
