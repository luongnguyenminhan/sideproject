"""
Router Demo - Test router functionality trong basic workflow
Demonstrates LLM router với structured output theo LangChain documentation
"""

import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Demo queries để test router decisions
TEST_QUERIES = [
    {
        "query": "Tôi cần tư vấn về cách quản lý tiền lương hàng tháng",
        "expected_target": "rag_query",
        "description": "Financial advice - should route to RAG",
    },
    {
        "query": "Tính giúp tôi 1000 + 500 * 2",
        "expected_target": "math_tools",
        "description": "Math calculation - should route to math tools",
    },
    {
        "query": "Xin chào, bạn có khỏe không?",
        "expected_target": "direct_agent",
        "description": "Greeting - should route to direct agent",
    },
    {
        "query": "Hướng dẫn đầu tư chứng khoán cho người mới bắt đầu",
        "expected_target": "rag_query",
        "description": "Investment guidance - should route to RAG",
    },
    {
        "query": "Chia 1500 cho 3 rồi cộng thêm 200",
        "expected_target": "math_tools",
        "description": "Complex math - should route to math tools",
    },
]


async def test_router_decisions():
    """Test router decisions with various query types"""

    print("🧭 ROUTER DEMO - Testing LLM Router với Structured Output")
    print("=" * 60)

    try:
        # Import router components
        from ..basic_workflow import router_node, RouterDecision, ROUTER_SYSTEM_PROMPT
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_google_genai import ChatGoogleGenerativeAI

        # Initialize model
        model = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite", temperature=0)

        # Create router prompt
        router_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", ROUTER_SYSTEM_PROMPT),
                (
                    "human",
                    "User query: {input}\n\nAnalyze this query and determine the best routing target.",
                ),
            ]
        )

        # Create router chain
        router_chain = router_prompt | model.with_structured_output(RouterDecision)

        print(f"📋 Testing {len(TEST_QUERIES)} queries...\n")

        results = []

        for i, test_case in enumerate(TEST_QUERIES, 1):
            query = test_case["query"]
            expected = test_case["expected_target"]
            description = test_case["description"]

            print(f"Test {i}: {description}")
            print(f"Query: {query}")
            print(f"Expected: {expected}")

            try:
                # Execute router decision
                result = await router_chain.ainvoke({"input": query})

                actual_target = (
                    result.target if hasattr(result, "target") else "unknown"
                )
                explanation = (
                    result.explanation
                    if hasattr(result, "explanation")
                    else "No explanation"
                )

                # Check if routing matches expectation
                is_correct = actual_target == expected
                status = "✅ CORRECT" if is_correct else "❌ INCORRECT"

                print(f"Actual: {actual_target}")
                print(f"Explanation: {explanation}")
                print(f"Result: {status}")

                results.append(
                    {
                        "query": query,
                        "expected": expected,
                        "actual": actual_target,
                        "correct": is_correct,
                        "explanation": explanation,
                    }
                )

            except Exception as e:
                print(f"❌ ERROR: {str(e)}")
                results.append(
                    {
                        "query": query,
                        "expected": expected,
                        "actual": "error",
                        "correct": False,
                        "explanation": str(e),
                    }
                )

            print("-" * 40)

        # Summary
        correct_count = sum(1 for r in results if r["correct"])
        total_count = len(results)
        accuracy = (correct_count / total_count) * 100 if total_count > 0 else 0

        print(f"\n📊 ROUTER PERFORMANCE SUMMARY")
        print(f"Correct Routing: {correct_count}/{total_count} ({accuracy:.1f}%)")
        print(f"Timestamp: {datetime.now().isoformat()}")

        # Detailed results
        print(f"\n📋 DETAILED RESULTS:")
        for i, result in enumerate(results, 1):
            status = "✅" if result["correct"] else "❌"
            print(
                f'{i}. {status} Expected: {result["expected"]} | Actual: {result["actual"]}'
            )

        return results

    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        return []


async def test_router_node_integration():
    """Test router node integration in workflow state"""

    print("\n🔧 ROUTER NODE INTEGRATION TEST")
    print("=" * 40)

    try:
        from ..state.workflow_state import AgentState, StateManager
        from langchain_core.messages import HumanMessage

        # Create test state
        test_query = "Tôi muốn biết về hoạt động của CLB CGSEM"
        initial_state = StateManager.create_initial_state(test_query)

        print(f"Query: {test_query}")
        print(f"Initial State Keys: {list(initial_state.keys())}")

        # Mock config
        config = {"configurable": {"thread_id": "demo_thread_123"}}

        # Test router node
        from ..basic_workflow import router_node

        updated_state = await router_node(initial_state, config)

        # Check results
        router_decision = updated_state.get("router_decision", {})
        routing_complete = updated_state.get("routing_complete", False)

        print(f"Router Decision: {router_decision}")
        print(f"Routing Complete: {routing_complete}")

        if router_decision:
            target = (
                router_decision.get("target", "unknown")
                if isinstance(router_decision, dict)
                else "unknown"
            )
            explanation = (
                router_decision.get("explanation", "No explanation")
                if isinstance(router_decision, dict)
                else "No explanation"
            )
            print(f"Target: {target}")
            print(f"Explanation: {explanation}")
            print("✅ Router node integration successful")
        else:
            print("❌ Router decision not found in state")

        return updated_state

    except Exception as e:
        print(f"❌ Integration test failed: {str(e)}")
        return None


if __name__ == "__main__":
    print("🚀 Starting Router Demo...")

    async def main():
        # Test router decisions
        router_results = await test_router_decisions()

        # Test router node integration
        integration_result = await test_router_node_integration()

        print(f"\n🎯 DEMO COMPLETE")
        print(f"Router Tests: {len(router_results)} executed")
        print(
            f'Integration Test: {"✅ Success" if integration_result else "❌ Failed"}'
        )

    # Run demo
    asyncio.run(main())
