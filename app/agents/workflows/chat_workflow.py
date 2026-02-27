"""Chat Sub-Agent 서브그래프"""

from langgraph.graph import StateGraph, END

from app.agents.constants import WorkflowSteps
from app.agents.nodes.chat.classifier import classify_question
from app.agents.nodes.chat.generator import generate_answer
from app.agents.nodes.chat.router import route_question
from app.agents.state import RouterState


def create_chat_subgraph() -> StateGraph:
    """Chat Sub-Agent 서브그래프 생성 (Router Workflow에 노드로 등록)"""

    workflow = StateGraph(RouterState)

    workflow.add_node(WorkflowSteps.CLASSIFIER, classify_question)
    workflow.add_node(WorkflowSteps.GENERATOR, generate_answer)

    workflow.set_entry_point(WorkflowSteps.CLASSIFIER)

    workflow.add_conditional_edges(
        WorkflowSteps.CLASSIFIER,
        route_question,
        {
            "generator": WorkflowSteps.GENERATOR,
            "search_generator": WorkflowSteps.GENERATOR,
            "summary_generator": WorkflowSteps.GENERATOR,
            "compare_generator": WorkflowSteps.GENERATOR,
        }
    )

    workflow.add_edge(WorkflowSteps.GENERATOR, END)

    return workflow.compile()
