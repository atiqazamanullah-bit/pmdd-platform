from abc import ABC, abstractmethod
from typing import Any, Dict
from agents.schemas import CognitiveState, AgentOutput, ValidationFeedback
import logging

logger = logging.getLogger("pmdd.agents")

class BaseCognitiveAgent(ABC):
    def __init__(self, agent_name: str, max_retries: int = 3):
        self.agent_name = agent_name
        self.max_retries = max_retries

    async def execute(self, state: CognitiveState) -> AgentOutput:
        """The main cognitive loop."""
        logger.info(f"[{self.agent_name}] Starting cognitive cycle for segment {state.segment.segment_id}")
        
        # 1. Observe (Load Context & Memory)
        context = await self.observe(state)
        
        while state.retry_count < self.max_retries:
            # 2. Analyze
            if state.retry_count == 0:
                output = await self.analyze(context, state)
            else:
                # 4 & 5. Reflect and Correct
                output = await self.reflect_and_correct(context, state)
            
            state.current_output = output
            
            # 3. Validate
            validation = await self.validate(output, state)
            state.validation_history.append(validation)
            
            if validation.is_valid:
                # 6 & 7. Score & Store
                output.validation_status = "Passed"
                await self.store_memory(state, success=True)
                return output
            
            logger.warning(f"[{self.agent_name}] Validation failed: {validation.errors}. Retrying...")
            state.retry_count += 1

        # Fallback if max retries reached
        logger.error(f"[{self.agent_name}] Max retries reached.")
        if state.current_output:
            state.current_output.validation_status = "Failed"
        await self.store_memory(state, success=False)
        return state.current_output

    @abstractmethod
    async def observe(self, state: CognitiveState) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def analyze(self, context: Dict[str, Any], state: CognitiveState) -> AgentOutput:
        pass

    @abstractmethod
    async def validate(self, output: AgentOutput, state: CognitiveState) -> ValidationFeedback:
        pass

    @abstractmethod
    async def reflect_and_correct(self, context: Dict[str, Any], state: CognitiveState) -> AgentOutput:
        pass

    @abstractmethod
    async def store_memory(self, state: CognitiveState, success: bool):
        pass
