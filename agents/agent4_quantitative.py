from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from agents.base import BaseCognitiveAgent
from agents.schemas import CognitiveState, AgentOutput, ValidationFeedback
from agents.prompts import QUANTITATIVE_SYSTEM_PROMPT

class QuantitativeAnalyzerAgent(BaseCognitiveAgent):
    """Agent 4: Quantitative Analyzer."""
    
    def __init__(self):
        super().__init__(agent_name="Agent4_Quantitative", max_retries=3)
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
        self.structured_llm = self.llm.with_structured_output(AgentOutput)

    async def observe(self, state: CognitiveState) -> Dict[str, Any]:
        return {"memory": "Quantitative context loaded."}

    async def analyze(self, context: Dict[str, Any], state: CognitiveState) -> AgentOutput:
        prompt = ChatPromptTemplate.from_messages([
            ("system", QUANTITATIVE_SYSTEM_PROMPT),
            ("human", "Keywords focus: {keywords}\n\nAnalyze the following segment:\n{text}")
        ])
        
        chain = prompt | self.structured_llm
        result = await chain.ainvoke({
            "keywords": context.get("keywords", "None provided"),
            "text": state.segment.raw_text
        })
        return result

    async def validate(self, output: AgentOutput, state: CognitiveState) -> ValidationFeedback:
        errors = []
        if output.overall_confidence < 0.7:
            errors.append("Overall confidence is too low.")
        for finding in output.findings:
            for ev in finding.corpus_evidence:
                if ev.exact_quote not in state.segment.raw_text:
                    errors.append(f"Hallucination detected: Quote '{ev.exact_quote}' not found in source text.")
                    
        return ValidationFeedback(
            is_valid=len(errors) == 0,
            errors=errors,
            suggested_correction="Ensure all quotes exactly match the provided segment text." if errors else None
        )

    async def reflect_and_correct(self, context: Dict[str, Any], state: CognitiveState) -> AgentOutput:
        last_feedback = state.validation_history[-1]
        prompt = ChatPromptTemplate.from_messages([
            ("system", QUANTITATIVE_SYSTEM_PROMPT),
            ("human", "Analyze this segment: {text}\n\nYOUR PREVIOUS ATTEMPT FAILED. Feedback: {feedback}\nCorrect your analysis and ensure perfect evidence tracing.")
        ])
        chain = prompt | self.structured_llm
        return await chain.ainvoke({
            "text": state.segment.raw_text,
            "feedback": last_feedback.errors
        })

    async def store_memory(self, state: CognitiveState, success: bool):
        pass
