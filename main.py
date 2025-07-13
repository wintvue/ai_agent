from dotenv import load_dotenv
from typing import List, Optional, Dict

from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, SystemMessage

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

QUESTIONS: List[str] = [
    "Tell me about yourself.",
    "Why are you interested in this role?",
    "Describe a time you overcame a challenge.",
    "What is your greatest strength?",
    "What questions do you have for us?",
]

class InterviewAgent:
    """Unified interview agent that orchestrates the interview process and integrates with Streamlit."""

    def __init__(
        self,
        questions: List[str] = None,
        max_followups_per_question: int = 2,
        model_name: str = "gpt-4.1",
        temperature: float = 0.7
    ) -> None:
        if max_followups_per_question < 0:
            raise ValueError("max_followups_per_question must be non-negative")

        self.questions = questions or QUESTIONS
        self.max_followups_per_question = max_followups_per_question
        self.llm = ChatOpenAI(model_name=model_name, temperature=temperature)

        # runtime state
        self.q_index = 0          
        self.current_question_followups = 0  # Track follow-ups for current question
        self.is_started = False

        # System prompt for evaluating response quality
        self.evaluation_system_prompt = (
            "You are an experienced interviewer evaluating a candidate's response. "
            "Analyze the response and determine if it needs a follow-up question. "
            "A follow-up is needed if the response:\n"
            "1. Lacks specific examples or concrete details\n"
            "2. Is too brief or vague (under 30 words)\n"
            "3. Doesn't explain the candidate's role or actions clearly\n"
            "4. Missing the outcome or impact of their actions\n"
            "5. Doesn't address the STAR method (Situation, Task, Action, Result)\n\n"
            "Respond with only 'YES' if a follow-up is needed, or 'NO' if the response is adequate."
        )
        
        # System prompt for generating follow-up questions
        self.followup_generation_prompt = (
            "You are an experienced interviewer. Generate ONE specific follow-up question "
            "based on what's missing from the candidate's response. Focus on:\n"
            "1. Getting specific examples if response is vague\n"
            "2. Understanding their role and actions if unclear\n"
            "3. Learning about results/outcomes if missing\n"
            "4. Probing decision-making process if needed\n"
            "Keep it conversational and under 25 words. Be direct and specific."
        )
        
        logger.info(f"InterviewAgent initialized with {len(self.questions)} questions, max_followups_per_question={max_followups_per_question}")

    def _next_prepared_question(self) -> Optional[str]:
        if self.q_index < len(self.questions):
            q = self.questions[self.q_index]
            logger.info(f"Retrieving prepared question {self.q_index + 1}/{len(self.questions)}: '{q}'")
            self.q_index += 1
            self.current_question_followups = 0  # Reset follow-up counter for new question
            return q
        logger.info("No more prepared questions available")
        return None

    def _should_ask_followup(self, candidate_response: str) -> bool:
        """Evaluate if a follow-up question is needed based on response quality."""
        logger.info(f"Evaluating response quality for follow-up decision")
        
        # Basic checks first
        if len(candidate_response.strip()) < 20:
            logger.info("Response too short, follow-up needed")
            return True
            
        try:
            messages = [
                SystemMessage(content=self.evaluation_system_prompt),
                HumanMessage(content=f"Candidate's response: {candidate_response}")
            ]
            
            response = self.llm(messages)
            decision = response.content.strip().upper()
            
            logger.info(f"LLM evaluation decision: {decision}")
            return decision == "YES"
            
        except Exception as e:
            logger.error(f"Error in response evaluation: {e}")
            # Default to asking follow-up if evaluation fails
            return True

    def _generate_followup_question(self, conversation_history: List[dict]) -> str:
        """Generate a specific follow-up question based on conversation history."""
        logger.info("Generating follow-up question")
        
        # Convert conversation history to a readable format
        history_text = ""
        for msg in conversation_history[-4:]:  # Only use last 4 messages for context
            role = "Interviewer" if msg["role"] == "assistant" else "Candidate"
            history_text += f"{role}: {msg['content']}\n"
        
        try:
            messages = [
                SystemMessage(content=self.followup_generation_prompt),
                HumanMessage(content=f"Recent conversation:\n{history_text}\n\nWhat follow-up question should I ask?")
            ]
            
            response = self.llm(messages)
            followup = response.content.strip()
            
            if followup:
                logger.info(f"Generated follow-up question: '{followup}'")
                return followup
            else:
                logger.warning("LLM returned empty follow-up, using fallback")
                return "Can you give me a specific example?"
                
        except Exception as e:
            logger.error(f"Error generating follow-up: {e}")
            return "Could you elaborate on that with more details?"

    def _generate_followup(self, conversation_history: List[dict]) -> Optional[str]:
        """Use a two-step process to decide and generate follow-up questions."""
            
        last_user_msg = conversation_history[-1]['content']
                
        if self._should_ask_followup(last_user_msg):
            return self._generate_followup_question(conversation_history)
        else:
            logger.info("Response evaluation determined no follow-up needed")
            return None

    def agent_turn(self, conversation_history: List[dict] = None) -> str:
        """Advance the interview by one line.

        Args:
            conversation_history: Full conversation history from the app for follow-up generation.
        Returns:
            The next interviewer line.
        """
        logger.info(f"Agent turn started - current_question_followups: {self.current_question_followups}, max_per_question: {self.max_followups_per_question}")
        

        # Check if we should consider a follow-up (only if we have remaining follow-ups for current question)
        if conversation_history and self.current_question_followups < self.max_followups_per_question:
            logger.info("Checking if follow-up is needed")
            # Use conversation history from app if available
            follow = self._generate_followup(conversation_history)
            if follow:  # LLM decided to ask a follow-up
                self.current_question_followups += 1
                logger.info(f"Follow-up question generated: '{follow}' (current question followups: {self.current_question_followups})")
                return follow
            else:
                logger.info("LLM decided no follow-up needed, moving to next prepared question")

        # If no follow-up needed or max follow-ups reached, move to next prepared question
        prepared = self._next_prepared_question()
        if prepared is not None:
            logger.info(f"Prepared question asked: '{prepared}'")
            return prepared

        # If no more questions, close the interview
        closing = "Thank you for your time! We'll be in touch."
        logger.info(f"Interview completed with closing message: '{closing}'")
        return closing

    def get_response(self, conversation_history: List[dict]) -> str:
        """
        Get response from the interview agent.
        
        Args:
            conversation_history: List of previous messages from the Streamlit app
            user_prompt: Current user message
            
        Returns:
            Agent's response
        """
        logger.info(f"conversation_history: {conversation_history[:5]}")
        
        # If this is the first interaction, start the interview
        if not self.is_started:
            self.is_started = True
            return self.agent_turn()
        
        # Continue the interview with user input and conversation history
        return self.agent_turn(conversation_history)


if __name__ == "__main__":
    interview = InterviewAgent(max_followups_per_question=2)

    print("Agent:", interview.agent_turn())  
    conversation_history = []
    while True:
        user_input = input("Enter a message: ")
        # Build conversation history for follow-up generation
        conversation_history.append({"role": "user", "content": user_input})
        
        reply = interview.agent_turn(user_input, conversation_history)
        print("Agent:", reply)
        
        # Update conversation history
        conversation_history.append({"role": "assistant", "content": reply})
        
        if reply.startswith("Thank you"):
            break