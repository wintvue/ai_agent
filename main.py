from dotenv import load_dotenv
from typing import List, Optional

from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts.chat import ChatPromptTemplate
from langchain.chains import LLMChain

load_dotenv()

QUESTIONS: List[str] = [
    "Tell me about yourself.",
    "Why are you interested in this role?",
    "Describe a time you overcame a challenge.",
    "What is your greatest strength?",
    "What questions do you have for us?",
]

class InterviewManager:
    """Interview state machine with interleaved follow-ups.

    Flow per candidate reply:
        • If a follow-up is due → ask it.
        • Else ask next prepared question.
        • After asking a prepared question, schedule a follow-up (if any left).
    """

    def __init__(
        self,
        questions: List[str],
        llm: ChatOpenAI,
        max_followups: int = 3,
    ) -> None:
        if max_followups < 0:
            raise ValueError("max_followups must be non-negative")

        self.questions = questions
        self.llm = llm
        self.followups_remaining = max_followups

        # runtime state
        self.memory = ConversationBufferMemory(return_messages=True)
        self.q_index = 0          
        self.need_followup = False  
    def _next_prepared_question(self) -> Optional[str]:
        if self.q_index < len(self.questions):
            q = self.questions[self.q_index]
            self.q_index += 1
            return q
        return None

    def _generate_followup(self) -> str:
        """Use the LLM to craft one follow-up question."""
        history = self.memory.load_memory_variables({})["history"]

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an interviewer. Craft ONE concise, insightful "
                    "follow-up question that probes deeper into the candidate's "
                    "last answer, based on the conversation so far. Avoid "
                    "repeating any previous question."
                ),
                ("human", "Conversation so far:\n{history}\n"),
            ]
        )

        chain = LLMChain(llm=self.llm, prompt=prompt)
        followup = chain.run(history=history).strip()
        return followup or "Could you elaborate further?"


    def agent_turn(self, user_msg: Optional[str] = None) -> str:
        """Advance the interview by one line.

        Args:
            user_msg: Candidate's response to the *previous* interviewer line.
                       Use ``None`` on the very first call to start the session.
        Returns:
            The next interviewer line.
        """
        if user_msg is not None:
            self.memory.chat_memory.add_user_message(user_msg)

        if self.need_followup and self.followups_remaining > 0:
            follow = self._generate_followup()
            self.memory.chat_memory.add_ai_message(follow)
            self.need_followup = False
            self.followups_remaining -= 1
            return follow

        prepared = self._next_prepared_question()
        if prepared is not None:
            self.memory.chat_memory.add_ai_message(prepared)
            self.need_followup = self.followups_remaining > 0
            return prepared

        closing = "Thank you for your time! We’ll be in touch."
        self.memory.chat_memory.add_ai_message(closing)
        return closing


if __name__ == "__main__":
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.3)

    interview = InterviewManager(QUESTIONS, llm, max_followups=3)

    print("Agent:", interview.agent_turn())  
    while True:
        user_input = input("Enter a message: ")
        reply = interview.agent_turn(user_input)
        print("Agent:", reply)
        if reply.startswith("Thank you"):
            break