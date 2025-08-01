"""Pydantic models for categorization system."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models import Transaction


class UserCategories(BaseModel):
    """User's custom categories for transaction categorization."""

    user_id: str = Field(..., description="Unique user identifier")
    categories: list[str] = Field(
        ..., 
        description="List of user's category names",
        min_items=1
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When categories were created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When categories were last updated"
    )


class CategorizedTransaction(BaseModel):
    """Transaction with categorization and user feedback capability."""
    
    transaction_id: str = Field(..., description="Unique transaction identifier")
    transaction: Transaction = Field(..., description="Original transaction data")
    category: str | None = Field(
        default=None,
        description="Category assigned by the system (null if no suitable category found)"
    )
    informed_category: str | None = Field(
        default=None,
        description="Category informed by the user (null if user agrees with system or no correction needed)"
    )
    confidence_score: float = Field(
        ...,
        description="Confidence score for categorization (0-1)",
        ge=0,
        le=1
    )
    categorization_method: str = Field(
        default="vector_similarity",
        description="Method used for categorization"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When categorization was performed"
    )


class CategorizationRequest(BaseModel):
    """Simplified request for categorization and feedback."""
    
    session_id: str | None = Field(
        default=None,
        description="Session identifier (optional, for referencing existing session)"
    )
    user_id: str = Field(..., description="User identifier")
    user_categories: UserCategories = Field(
        ..., 
        description="User's categories for categorization"
    )
    transactions: list[CategorizedTransaction] = Field(
        ...,
        description="List of transactions with categorization info and optional user feedback"
    )
    confidence_threshold: float = Field(
        default=0.3,
        description="Minimum confidence score to assign a category (0.0-1.0)",
        ge=0.0,
        le=1.0
    )


class CategorizationResponse(BaseModel):
    """Response for categorization with user feedback capability."""
    
    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    confidence_threshold: float = Field(..., description="Confidence threshold used")
    categorized_transactions: list[CategorizedTransaction] = Field(
        ...,
        description="List of categorized transactions with user feedback capability"
    )


 