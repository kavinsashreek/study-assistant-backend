import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"


def answer_question_with_rag(question: str, relevant_chunks: list[dict], document_name: str) -> dict:
    context_text = ""
    for i, chunk in enumerate(relevant_chunks):
        context_text += f"\n--- Excerpt {i+1} ---\n"
        context_text += chunk["text"]
        context_text += "\n"

    system_prompt = """You are a helpful friendly study assistant for students.
Answer questions based on uploaded study material.

IMPORTANT RULES:
1. First try to answer ONLY from the provided document excerpts
2. If the answer IS in the document: Answer clearly using that information
3. If the answer is NOT in the document:
   - First say: "This specific information is not in your uploaded material."
   - Then say: "However, based on general knowledge from trusted sources:"
   - Give a helpful answer from your general knowledge
   - End with: "Source: General academic knowledge (not from your uploaded document)"
4. Always be encouraging and student-friendly
5. Use simple language"""

    user_message = f"""Document: {document_name}

Relevant excerpts:
{context_text}

Student's Question: {question}"""

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=1500,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    )
    return {
        "answer": response.choices[0].message.content,
        "sources_used": len(relevant_chunks),
        "model": MODEL
    }


def generate_summary(chunks: list[str], document_name: str) -> dict:
    max_chunks = min(30, len(chunks))
    combined_text = "\n\n".join(chunks[:max_chunks])

    system_prompt = """You are a friendly study assistant. Create a VERY DETAILED and ELABORATE summary.

For EACH topic found in the document:
1. Give a proper heading
2. Explain the topic in detail (at least 3-5 sentences)
3. List all important subtopics and concepts
4. Give examples where possible

Format like this:

## Summary: [Document Name]

### Overview
[2-3 sentences about what this document covers]

### Topic 1: [Name]
[Detailed explanation - at least 4-5 sentences covering all aspects]
Key points:
- [point 1]
- [point 2]
- [point 3]

### Topic 2: [Name]
[Detailed explanation - at least 4-5 sentences]
Key points:
- [point 1]
- [point 2]

[Continue for ALL topics found in the document]

### Quick Revision Points
[10-15 most important facts to remember]

Be THOROUGH and DETAILED. Do not skip any topic found in the document!"""

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=4000,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Create a detailed summary for: {document_name}\n\nContent:\n{combined_text}"}
        ]
    )
    return {
        "summary": response.choices[0].message.content,
        "document_name": document_name,
        "chunks_analyzed": max_chunks
    }


def generate_flashcards(chunks: list[str], document_name: str) -> dict:
    max_chunks = min(20, len(chunks))
    combined_text = "\n\n".join(chunks[:max_chunks])

    system_prompt = """Create exactly 10 flashcards. Return ONLY valid JSON, nothing else.

{
  "flashcards": [
    {
      "id": 1,
      "question": "What is...?",
      "answer": "The answer is...",
      "difficulty": "easy",
      "hint": "Think about..."
    }
  ]
}

Rules:
- Clear specific questions
- Concise answers (1-3 sentences)
- Mix: 3 easy, 4 medium, 3 hard
- Cover the most important concepts
- Base questions on actual content from the document"""

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=2000,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Create flashcards for: {document_name}\n\n{combined_text}"}
        ]
    )

    response_text = response.choices[0].message.content.strip()
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
    response_text = response_text.strip()

    try:
        flashcard_data = json.loads(response_text)
        return {
            "flashcards": flashcard_data.get("flashcards", []),
            "document_name": document_name,
            "total_cards": len(flashcard_data.get("flashcards", []))
        }
    except json.JSONDecodeError:
        return {
            "flashcards": [],
            "document_name": document_name,
            "total_cards": 0,
            "error": "Failed to generate flashcards. Please try again."
        }


def generate_study_guide(chunks: list[str], document_name: str) -> dict:
    max_chunks = min(20, len(chunks))
    combined_text = "\n\n".join(chunks[:max_chunks])

    system_prompt = """You are an expert study coach. Create a DETAILED personalized study guide.

Format like this:

## Study Guide: [Topic Name]

### Difficulty Level
[Easy/Medium/Hard] - [Detailed reason why]

### Recommended Study Time
[Total hours and exactly how to split them day by day]

### Complete Study Plan

#### Day 1: Foundation
- What to read: [specific topics]
- What to focus on: [specific concepts]
- Goal: [what you should know by end of day 1]

#### Day 2: Deep Dive
- What to read: [specific topics]
- What to focus on: [specific concepts]
- Goal: [what you should know by end of day 2]

#### Day 3: Practice and Review
- Practice questions to attempt
- Topics to revise
- Goal: [exam readiness]

### Best Study Strategies for This Topic
[4-5 very specific strategies that work for THIS content]

### Most Important Concepts to Master
[List 8-10 key concepts with brief explanation of each]

### Common Mistakes to Avoid
[4-5 specific mistakes students make with this topic]

### How to Know You Have Mastered It
[5 specific signs that show you truly understand]

### Sample Questions to Test Yourself
[Give 5 practice questions based on the content]

### Real Life Applications
[3-4 practical real world uses of this knowledge]

Be SPECIFIC to the actual content provided!"""

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=4000,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Create a detailed study guide for: {document_name}\n\nContent:\n{combined_text}"}
        ]
    )
    return {
        "study_guide": response.choices[0].message.content,
        "document_name": document_name
    }


def generate_quiz(chunks: list[str], document_name: str, difficulty: str = "medium") -> dict:
    max_chunks = min(20, len(chunks))
    combined_text = "\n\n".join(chunks[:max_chunks])

    system_prompt = f"""Create exactly 10 multiple choice quiz questions at {difficulty} difficulty.
Return ONLY valid JSON, nothing else.

{{
  "quiz": [
    {{
      "id": 1,
      "question": "What is...?",
      "options": {{
        "A": "First option",
        "B": "Second option",
        "C": "Third option",
        "D": "Fourth option"
      }},
      "correct_answer": "A",
      "explanation": "This is correct because...",
      "difficulty": "{difficulty}"
    }}
  ]
}}

Rules:
- Questions must be based on the provided content
- Each question has exactly 4 options (A, B, C, D)
- Only ONE correct answer per question
- Include a brief explanation for the correct answer
- Make wrong options plausible but clearly incorrect
- Mix question types: definition, application, comparison"""

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=3000,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Create a quiz for: {document_name}\n\n{combined_text}"}
        ]
    )

    response_text = response.choices[0].message.content.strip()
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
    response_text = response_text.strip()

    try:
        quiz_data = json.loads(response_text)
        return {
            "quiz": quiz_data.get("quiz", []),
            "document_name": document_name,
            "total_questions": len(quiz_data.get("quiz", [])),
            "difficulty": difficulty
        }
    except json.JSONDecodeError:
        return {
            "quiz": [],
            "document_name": document_name,
            "total_questions": 0,
            "error": "Failed to generate quiz. Please try again."
        }