from app.config import get_settings
import json
from typing import Dict, Any

settings = get_settings()


class LLMService:
    def __init__(self):
        self.provider = settings.llm_provider
        
        if self.provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=settings.openai_api_key)
            self.model = settings.openai_model
        elif self.provider == "ollama":
            from openai import OpenAI
            self.client = OpenAI(
                base_url=settings.ollama_base_url,
                api_key="ollama"  # Ollama doesn't require a real key
            )
            self.model = settings.ollama_model
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    def grade_submission(self, submission_text: str, rubric: Dict, 
                        context_chunks: list) -> Dict[str, Any]:
        """Grade a submission using LLM with RAG context."""
        
        # Build context from retrieved chunks
        context = "\n\n".join([
            f"[Reference {i+1}]: {chunk['text']}"
            for i, chunk in enumerate(context_chunks)
        ])
        
        # Build grading prompt
        system_prompt = self._build_grading_prompt()
        user_prompt = self._build_user_prompt(submission_text, rubric, context)
        
        # Call LLM
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            # Extract and parse JSON response
            response_text = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Parse JSON
            result = json.loads(response_text)
            
            # Validate required fields
            required_fields = ["score", "breakdown", "feedback", "citations"]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")
            
            return result
            
        except json.JSONDecodeError as e:
            raise Exception(f"LLM returned invalid JSON: {e}")
        except Exception as e:
            raise Exception(f"LLM grading failed: {e}")
    
    def _build_grading_prompt(self) -> str:
        """Build the system prompt for grading."""
        return """You are an expert grading assistant for academic submissions.

Your task is to grade student submissions based STRICTLY on:
1. The provided rubric
2. The reference context provided
3. Conservative, evidence-based assessment

CRITICAL RULES:
- Follow the rubric criteria EXACTLY
- Use ONLY the retrieved reference context for verification
- Deduct points conservatively - prefer undergrading to overgrading
- Do NOT award points for claims not supported by the submission
- Do NOT hallucinate criteria not in the rubric
- All feedback must be grounded in either the rubric or reference documents

OUTPUT FORMAT:
You MUST return ONLY valid JSON with this exact structure:
{
  "score": <integer>,
  "breakdown": {
    "criterion_1": {"points": <int>, "max_points": <int>, "comment": "<string>"},
    "criterion_2": {"points": <int>, "max_points": <int>, "comment": "<string>"}
  },
  "feedback": "<overall feedback string>",
  "citations": [
    {"reference_id": <int>, "text": "<quoted text>", "relevance": "<why cited>"}
  ]
}

DO NOT include any text outside this JSON structure.
DO NOT use markdown code blocks.
DO NOT add commentary before or after the JSON."""

    def _build_user_prompt(self, submission_text: str, rubric: Dict, 
                          context: str) -> str:
        """Build the user prompt with submission, rubric, and context."""
        rubric_text = json.dumps(rubric, indent=2)
        
        return f"""Grade the following submission.

RUBRIC:
{rubric_text}

REFERENCE CONTEXT:
{context}

SUBMISSION TO GRADE:
{submission_text}

Provide your grading in the required JSON format."""


llm_service = LLMService()
