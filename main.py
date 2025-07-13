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
        max_followups: int = 5,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.3
    ) -> None:
        if max_followups < 0:
            raise ValueError("max_followups must be non-negative")

        self.questions = questions or QUESTIONS
        self.max_followups = max_followups
        self.llm = ChatOpenAI(model_name=model_name, temperature=temperature)
        self.followups_remaining = max_followups

        # runtime state
        self.memory = ConversationBufferMemory(return_messages=True)
        self.q_index = 0          
        self.need_followup = False  
        self.is_started = False

        # System prompt for follow-up questions
        self.followup_system_prompt = (
            "You are an experienced interviewer conducting a behavioral interview. "
            "Based on the candidate's response, ask ONE specific follow-up question that:\n"
            "1. Probes for concrete examples or details\n"
            "2. Explores the candidate's decision-making process\n"
            "3. Uncovers their role and impact in the situation\n"
            "Keep it conversational and under 25 words."
        )
        
        logger.info(f"InterviewAgent initialized with {len(self.questions)} questions, max_followups={max_followups}")

    def _next_prepared_question(self) -> Optional[str]:
        if self.q_index < len(self.questions):
            q = self.questions[self.q_index]
            logger.info(f"Retrieving prepared question {self.q_index + 1}/{len(self.questions)}: '{q}'")
            self.q_index += 1
            return q
        logger.info("No more prepared questions available")
        return None

    def _generate_followup_direct(self, conversation_history: List[dict]) -> str:
        logger.info(f"Generating follow-up question using direct LLM call (remaining: {self.followups_remaining})")
        
        # Convert conversation history to a readable format
        history_text = ""
        for msg in conversation_history:
            role = "Interviewer" if msg["role"] == "assistant" else "Candidate"
            history_text += f"{role}: {msg['content']}\n"
        
        try:
            # Direct LLM call with messages
            messages = [
                SystemMessage(content=self.followup_system_prompt),
                HumanMessage(content=f"Interview conversation:\n{history_text}\n\nWhat's your follow-up question?")
            ]
            
            response = self.llm(messages)
            followup = response.content.strip()
            
            if followup:
                logger.info(f"Generated follow-up question: '{followup}'")
                return followup
            else:
                logger.warning("LLM returned empty follow-up, using fallback")
                return "Could you elaborate further on that?"
                
        except Exception as e:
            logger.error(f"Error generating follow-up: {e}")
            return "Could you tell me more about that?"

    def _generate_followup(self, conversation_history: List[dict]) -> str:
        """Use the LLM to craft one follow-up question based on app's chat history."""
        # Using direct approach by default (most recommended)
        return self._generate_followup_direct(conversation_history)

    def agent_turn(self, user_msg: Optional[str] = None, conversation_history: List[dict] = None) -> str:
        """Advance the interview by one line.

        Args:
            user_msg: Candidate's response to the *previous* interviewer line.
                       Use ``None`` on the very first call to start the session.
            conversation_history: Full conversation history from the app for follow-up generation.
        Returns:
            The next interviewer line.
        """
        logger.info(f"Agent turn started - need_followup: {self.need_followup}, followups_remaining: {self.followups_remaining}")
        
        if user_msg is not None:
            self.memory.chat_memory.add_user_message(user_msg)

        if self.need_followup and self.followups_remaining > 0:
            logger.info("Processing follow-up question")
            # Use conversation history from app if available, otherwise fall back to internal memory
            if conversation_history:
                follow = self._generate_followup(conversation_history)
            else:
                # Convert internal memory to expected format
                internal_history = self.memory.load_memory_variables({})["history"]
                follow = f"Could you elaborate further on that? (Internal: {internal_history})"
                logger.warning("No conversation history provided, using default follow-up")
            
            self.memory.chat_memory.add_ai_message(follow)
            self.need_followup = False
            self.followups_remaining -= 1
            logger.info(f"Follow-up question generated: '{follow}' (remaining followups: {self.followups_remaining})")
            return follow

        prepared = self._next_prepared_question()
        if prepared is not None:
            self.memory.chat_memory.add_ai_message(prepared)
            self.need_followup = self.followups_remaining > 0
            logger.info(f"Prepared question asked: '{prepared}' (will need followup: {self.need_followup})")
            return prepared

        # If no more questions, close the interview
        closing = "Thank you for your time! We'll be in touch."
        self.memory.chat_memory.add_ai_message(closing)
        logger.info(f"Interview completed with closing message: '{closing}'")
        return closing

    def get_response(self, conversation_history: List[dict], user_prompt: str) -> str:
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
        return self.agent_turn(user_prompt, conversation_history)


if __name__ == "__main__":
    interview = InterviewAgent(max_followups=3)

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