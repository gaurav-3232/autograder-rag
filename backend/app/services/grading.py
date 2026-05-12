"""
services/grading.py

Loads the fine-tuned DistilBERT grading model and exposes a
grade_answer() function for use by the /grade endpoint.

Model architecture: frozen DistilBERT + custom grading head
Weights: only the head is saved (autograder_head.pth)
BERT base: loaded from HuggingFace cache
"""

import torch
import torch.nn as nn
from transformers import DistilBertTokenizer, DistilBertModel
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
MODEL_NAME  = "distilbert-base-uncased"
MAX_LENGTH  = 128
HEAD_WEIGHTS_PATH = Path(__file__).parent.parent / "notebooks" / "autograder_head.pth"


# ── Model definition (must match notebook 05 exactly) ─────────────────────────
class AutoGraderModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.bert = DistilBertModel.from_pretrained(MODEL_NAME)

        # Freeze BERT — we only trained the head
        for param in self.bert.parameters():
            param.requires_grad = False

        self.grading_head = nn.Sequential(
            nn.Linear(768, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 1),
            nn.Sigmoid()
        )

    def forward(self, input_ids, attention_mask):
        output        = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        cls_embedding = output.last_hidden_state[:, 0, :]  # [batch, 768]
        return self.grading_head(cls_embedding)            # [batch, 1]


# ── Singleton loader — model loads once at startup, reused for every request ──
_model     = None
_tokenizer = None
_device    = None


def _get_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    elif torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def load_model() -> None:
    """
    Call this once at application startup (e.g. in main.py lifespan).
    Loads tokenizer + BERT + head weights into memory.
    """
    global _model, _tokenizer, _device

    _device    = _get_device()
    _tokenizer = DistilBertTokenizer.from_pretrained(MODEL_NAME)

    _model = AutoGraderModel().to(_device)

    if HEAD_WEIGHTS_PATH.exists():
        _model.grading_head.load_state_dict(
            torch.load(HEAD_WEIGHTS_PATH, map_location=_device, weights_only=True)
        )
        logger.info(f"Grading head loaded from {HEAD_WEIGHTS_PATH}")
    else:
        logger.warning(
            f"Head weights not found at {HEAD_WEIGHTS_PATH}. "
            "Using untrained head — run notebook 05 to generate autograder_head.pth"
        )

    _model.eval()
    logger.info(f"AutoGraderModel ready on {_device}")


def grade_answer(student_answer: str, correct_answer: str) -> float:
    """
    Grade a student answer against the correct answer.

    Args:
        student_answer: The student's submitted answer text.
        correct_answer: The reference/correct answer text.

    Returns:
        Float between 0.0 and 1.0 representing similarity/grade.

    Raises:
        RuntimeError: If load_model() has not been called yet.
    """
    if _model is None or _tokenizer is None:
        raise RuntimeError("Grading model not loaded. Call load_model() at startup.")

    encoded = _tokenizer(
        student_answer,
        correct_answer,
        max_length=MAX_LENGTH,
        padding="max_length",
        truncation=True,
        return_tensors="pt"
    )

    input_ids      = encoded["input_ids"].to(_device)
    attention_mask = encoded["attention_mask"].to(_device)

    with torch.no_grad():
        score = _model(input_ids, attention_mask)

    return round(score.item(), 4)