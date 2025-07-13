import pytest
from unittest.mock import Mock, patch
from main import InterviewAgent, QUESTIONS


class TestInterviewAgent:
    """Test suite for InterviewAgent class."""
    
    def test_init_default_values(self):
        """Test InterviewAgent initialization with default values."""
        agent = InterviewAgent()
        
        assert agent.questions == QUESTIONS
        assert agent.max_followups_per_question == 2
        assert agent.q_index == 0
        assert agent.current_question_followups == 0
        assert not agent.is_started
    
    def test_init_custom_values(self):
        """Test InterviewAgent initialization with custom values."""
        custom_questions = ["Question 1", "Question 2"]
        agent = InterviewAgent(
            questions=custom_questions,
            max_followups_per_question=3,
            model_name="gpt-4",
            temperature=0.5
        )
        
        assert agent.questions == custom_questions
        assert agent.max_followups_per_question == 3
    
    def test_init_invalid_followups(self):
        """Test InterviewAgent initialization with invalid followups value."""
        with pytest.raises(ValueError):
            InterviewAgent(max_followups_per_question=-1)
    
    def test_next_prepared_question(self):
        """Test _next_prepared_question method."""
        agent = InterviewAgent()
        
        # First question
        question = agent._next_prepared_question()
        assert question == QUESTIONS[0]
        assert agent.q_index == 1
        assert agent.current_question_followups == 0
        
        # Second question
        question = agent._next_prepared_question()
        assert question == QUESTIONS[1]
        assert agent.q_index == 2
    
    def test_next_prepared_question_exhausted(self):
        """Test _next_prepared_question when all questions are exhausted."""
        agent = InterviewAgent()
        agent.q_index = len(QUESTIONS)  # Set to end
        
        question = agent._next_prepared_question()
        assert question is None
    
    def test_should_ask_followup_short_response(self):
        """Test _should_ask_followup with short response."""
        agent = InterviewAgent()
        
        result = agent._should_ask_followup("Yes")
        assert result is True
    
    @patch('main.ChatOpenAI')
    def test_should_ask_followup_llm_decision(self, mock_llm):
        """Test _should_ask_followup with LLM decision."""
        mock_response = Mock()
        mock_response.content = "YES"
        mock_llm.return_value.return_value = mock_response
        
        agent = InterviewAgent()
        result = agent._should_ask_followup("This is a longer response with more details")
        
        assert result is True
    
    @patch('main.ChatOpenAI')
    def test_should_ask_followup_llm_no_followup(self, mock_llm):
        """Test _should_ask_followup when LLM says no followup needed."""
        mock_response = Mock()
        mock_response.content = "NO"
        mock_llm.return_value.return_value = mock_response
        
        agent = InterviewAgent()
        result = agent._should_ask_followup("This is a comprehensive response with all details")
        
        assert result is False
    
    @patch('main.ChatOpenAI')
    def test_generate_followup_question(self, mock_llm):
        """Test _generate_followup_question method."""
        mock_response = Mock()
        mock_response.content = "Can you provide more details about that?"
        mock_llm.return_value.return_value = mock_response
        
        agent = InterviewAgent()
        conversation_history = [
            {"role": "assistant", "content": "Tell me about yourself."},
            {"role": "user", "content": "I am a developer."}
        ]
        
        result = agent._generate_followup_question(conversation_history)
        assert result == "Can you provide more details about that?"
    
    @patch('main.ChatOpenAI')
    def test_generate_followup_question_empty_response(self, mock_llm):
        """Test _generate_followup_question with empty LLM response."""
        mock_response = Mock()
        mock_response.content = ""
        mock_llm.return_value.return_value = mock_response
        
        agent = InterviewAgent()
        conversation_history = [
            {"role": "assistant", "content": "Tell me about yourself."},
            {"role": "user", "content": "I am a developer."}
        ]
        
        result = agent._generate_followup_question(conversation_history)
        assert result == "Can you give me a specific example?"
    
    def test_generate_followup_no_history(self):
        """Test _generate_followup with no conversation history."""
        agent = InterviewAgent()
        
        result = agent._generate_followup([])
        assert result is None
    
    @patch('main.ChatOpenAI')
    def test_agent_turn_first_call(self, mock_llm):
        """Test agent_turn on first call."""
        agent = InterviewAgent()
        
        result = agent.agent_turn()
        assert result == QUESTIONS[0]
        assert agent.q_index == 1
    
    @patch('main.ChatOpenAI')
    def test_agent_turn_with_followup(self, mock_llm):
        """Test agent_turn with followup generation."""
        # Mock LLM responses
        mock_response_eval = Mock()
        mock_response_eval.content = "YES"
        mock_response_followup = Mock()
        mock_response_followup.content = "What specific challenges did you face?"
        mock_llm.return_value.side_effect = [mock_response_eval, mock_response_followup]
        
        agent = InterviewAgent()
        agent.q_index = 1  # Simulate having asked first question
        
        conversation_history = [
            {"role": "assistant", "content": "Tell me about yourself."},
            {"role": "user", "content": "I work in tech."}
        ]
        
        result = agent.agent_turn(conversation_history)
        assert result == "What specific challenges did you face?"
        assert agent.current_question_followups == 1
    
    @patch('main.ChatOpenAI')
    def test_agent_turn_max_followups_reached(self, mock_llm):
        """Test agent_turn when max followups reached."""
        agent = InterviewAgent()
        agent.q_index = 1
        agent.current_question_followups = 2  # Max reached
        
        conversation_history = [
            {"role": "assistant", "content": "Tell me about yourself."},
            {"role": "user", "content": "I work in tech."}
        ]
        
        result = agent.agent_turn(conversation_history)
        assert result == QUESTIONS[1]  # Should move to next question
    
    def test_agent_turn_interview_completed(self):
        """Test agent_turn when interview is completed."""
        agent = InterviewAgent()
        agent.q_index = len(QUESTIONS)  # All questions asked
        
        result = agent.agent_turn()
        assert result == "Thank you for your time! We'll be in touch."
    
    @patch('main.ChatOpenAI')
    def test_get_response_first_interaction(self, mock_llm):
        """Test get_response for first interaction."""
        agent = InterviewAgent()
        
        result = agent.get_response([])
        assert result == QUESTIONS[0]
        assert agent.is_started is True
    
    @patch('main.ChatOpenAI')
    def test_get_response_continued_interaction(self, mock_llm):
        """Test get_response for continued interaction."""
        agent = InterviewAgent()
        agent.is_started = True
        agent.q_index = 1
        
        conversation_history = [
            {"role": "assistant", "content": "Tell me about yourself."},
            {"role": "user", "content": "I am a software engineer."}
        ]
        
        result = agent.get_response(conversation_history)
        assert result == QUESTIONS[1]  # Should return next question 