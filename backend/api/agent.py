# backend/api/agent.py
import os
from typing import List, TypedDict
from pydantic import BaseModel, Field

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import START, END, StateGraph

# 1. Define the Graph State
class GraphState(TypedDict):
    question: str
    documents: List[str]
    generation: str
    loop_count: int

# 2. Pydantic Model for Structured Grading Output
class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""
    binary_score: str = Field(description="Documents are relevant to the question, 'yes' or 'no'")

class ShakespeareAgent:
    def __init__(self, fetch_context_callback):
        # Callback used to hit ChromaDB again if we need to rewrite the query
        self.fetch_context_callback = fetch_context_callback
        
        # Initialize Groq LLM (Ensure GROQ_API_KEY is loaded in your .env)
        self.llm = ChatGroq(temperature=0, model_name="openai/gpt-oss-120b")
        
        # Node 1: Grader Chain (json_schema mode: gpt-oss-120b is unreliable with tool-call grading)
        self.structured_grader = self.llm.with_structured_output(GradeDocuments, method="json_schema")
        grade_system = (
            "You are a strict grader assessing relevance of a retrieved document to a user question. "
            "If the document contains keywords or semantic meaning related to the question, grade it 'yes'. "
            "Otherwise, grade it 'no'."
        )
        self.grade_prompt = ChatPromptTemplate.from_messages([
            ("system", grade_system),
            ("human", "Retrieved document: \n\n {document} \n\n User question: {question}")
        ])
        self.grader_chain = self.grade_prompt | self.structured_grader

        # Node 2: Generator Chain
        gen_system = (
            "You are an AI Shakespearean assistant. Use the retrieved context to answer the question. "
            "If the context doesn't contain the answer, state that you don't know based on the text. "
            "Keep the answer concise and analytical."
        )
        self.gen_prompt = ChatPromptTemplate.from_messages([
            ("system", gen_system),
            ("human", "Question: {question} \n\n Context: {context}")
        ])
        self.generator_chain = self.gen_prompt | self.llm

        # Node 3: Query Rewriter Chain
        rewrite_system = (
            "You are a query re-writer. Look at the input question and reason about the underlying intent. "
            "Output only an improved, more generic Shakespearean search query."
        )
        self.rewrite_prompt = ChatPromptTemplate.from_messages([
            ("system", rewrite_system),
            ("human", "{question}")
        ])
        self.rewrite_chain = self.rewrite_prompt | self.llm

        # Compile the graph
        self.graph = self._build_graph()

    def grade_node(self, state: GraphState):
        """Filters out irrelevant documents."""
        filtered_docs = []
        for d in state["documents"]:
            try:
                score = self.grader_chain.invoke({"question": state["question"], "document": d})
                if score.binary_score == "yes":
                    filtered_docs.append(d)
            except Exception:
                # Grading failure: keep the document and let the generator decide
                filtered_docs.append(d)
                
        return {"documents": filtered_docs}

    def generate_node(self, state: GraphState):
        """Synthesizes the final answer using only the verified documents."""
        context = "\n\n".join(state["documents"])
        generation = self.generator_chain.invoke({"context": context, "question": state["question"]})
        return {"generation": generation.content}

    def rewrite_node(self, state: GraphState):
        """Rewrites the query and fetches new context from ChromaDB."""
        new_question = self.rewrite_chain.invoke({"question": state["question"]}).content
        new_docs = self.fetch_context_callback(new_question)
        
        loop_count = state.get("loop_count", 0) + 1
        return {"question": new_question, "documents": new_docs, "loop_count": loop_count}

    def route_after_grade(self, state: GraphState):
        """Conditional routing based on grading results."""
        # If no documents passed the relevance check, rewrite. Cap at 2 loops to prevent infinite cycles.
        if not state["documents"] and state.get("loop_count", 0) < 2:
            return "rewrite"
        return "generate"

    def _build_graph(self):
        workflow = StateGraph(GraphState)
        
        workflow.add_node("grade", self.grade_node)
        workflow.add_node("generate", self.generate_node)
        workflow.add_node("rewrite", self.rewrite_node)
        
        workflow.add_edge(START, "grade")
        workflow.add_conditional_edges("grade", self.route_after_grade, {"generate": "generate", "rewrite": "rewrite"})
        workflow.add_edge("rewrite", "grade")
        workflow.add_edge("generate", END)
        
        return workflow.compile()
        
    def answer(self, question: str, initial_documents: List[str]):
        """Entry point to invoke the pipeline."""
        result = self.graph.invoke({
            "question": question, 
            "documents": initial_documents,
            "loop_count": 0
        })
        return result["generation"]