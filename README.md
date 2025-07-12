# 🎤 AI Interview Question Selector (LangChain + OpenAI)

This Python script simulates a structured interview using a predefined list of questions. It uses OpenAI's GPT model via LangChain.

---

## 🧠 Features

- Selects from a fixed list of predefined interview questions.
- Uses GPT via LangChain to dynamically choose the next question.
- The agent will stick to valid, pre-approved questions.
- Gracefully ends when all questions have been asked.

---

## 📋 Predefined Question List

The interviewer will only ask questions from the following list:

1. Tell me about yourself.
2. Why are you interested in this role?
3. Describe a time you overcame a challenge.
4. What is your greatest strength?
5. What questions do you have for us?

---

## 🚀 Quickstart Guide

### 1. Install Requirements

Create a virtual environment (optional):

```bash
python -m venv venv
source venv/bin/activate 

Install dependencies::

```bash
pip install -r requirements.txt
```

### 2. Set Your OpenAI API Key

Set your API key as an environment variable:

```bash
export OPENAI_API_KEY="your-api-key"
```

Or add it to your Python environment using os.environ if needed.


### 3. Run the Script

```bash
python main.py
```