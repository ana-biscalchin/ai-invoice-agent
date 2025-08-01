"""Categorization service for transaction categorization."""

import os
import uuid
from datetime import datetime
from typing import Any, Dict, List

from app.models import Transaction

from .models import (
    CategorizedTransaction,
    CategorizationRequest,
    CategorizationResponse,
    UserCategories,
)
from .vector_store import VectorStoreManager


class CategorizationService:
    """Service for categorizing transactions using vector store."""

    def __init__(self, openai_api_key: str = None):
        """
        Initialize categorization service.

        Args:
            openai_api_key: OpenAI API key. If None, will be read from environment.
        """
        if openai_api_key is None:
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                raise ValueError("OpenAI API key is required")

        print(f"🔍 DEBUG: Initializing CategorizationService...")
        self.vector_store = VectorStoreManager(openai_api_key)
        print(f"🔍 DEBUG: CategorizationService initialized successfully")

    async def _categorize_single_transaction(
        self,
        transaction: Transaction,
        user_categories: UserCategories,
        transaction_id: str,
        confidence_threshold: float = 0.3,
    ) -> CategorizedTransaction:
        """
        Categorize a single transaction.
        """
        print(f" DEBUG: _categorize_single_transaction called for '{transaction.description}'")
        
        # Search for similar transactions
        similar_transactions = await self.vector_store.search_similar_transactions(
            description=transaction.description,
            user_id=user_categories.user_id,
            limit=5,
        )

        # Determine category based on similar transactions
        category, confidence_score, method = self._determine_category(
            transaction=transaction,
            similar_transactions=similar_transactions,
            user_categories=user_categories,
            confidence_threshold=confidence_threshold,
        )

        # If no category found from similar transactions, try fallback categorization
        if category is None:
            print(f" DEBUG: No category found from similar transactions, trying fallback...")
            category, confidence_score, method = self._fallback_categorization(
                transaction=transaction,
                user_categories=user_categories,
                confidence_threshold=confidence_threshold,
            )

        return CategorizedTransaction(
            transaction_id=transaction_id,
            transaction=transaction,
            category=category,  # Can be None now
            confidence_score=confidence_score,
            categorization_method=method,
            created_at=datetime.utcnow(),
        )

    def _determine_category(
        self,
        transaction: Transaction,
        similar_transactions: List[Dict[str, Any]],
        user_categories: UserCategories,
        confidence_threshold: float = 0.3,
    ) -> tuple[str | None, float, str]:
        """
        Determine category for transaction based on similar transactions.
        """
        print(f"🔍 DEBUG: _determine_category called with {len(similar_transactions)} similar transactions")
        
        if not similar_transactions:
            print(f"🔍 DEBUG: No similar transactions found")
            return None, 0.0, "no_similar_transactions"
        
        # Check for exact matches first
        exact_matches = [t for t in similar_transactions if t.get("match_type") == "exact"]
        if exact_matches:
            best_match = exact_matches[0]
            print(f" DEBUG: Found exact match: {best_match}")
            return best_match["category"], 1.0, "exact_match"
        
        # Check for high confidence vector similarity matches
        high_confidence_matches = [
            t for t in similar_transactions 
            if t.get("similarity_score", 0) >= confidence_threshold
        ]
        
        if high_confidence_matches:
            # Sort by similarity score (highest first)
            high_confidence_matches.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)
            best_match = high_confidence_matches[0]
            
            print(f"🔍 DEBUG: Found high confidence match: {best_match}")
            return best_match["category"], best_match["similarity_score"], "vector_similarity_high_confidence"
        
        # If we have any matches but they're below threshold, return the best one with low confidence
        if similar_transactions:
            best_match = max(similar_transactions, key=lambda x: x.get("similarity_score", 0))
            print(f"🔍 DEBUG: Found low confidence match: {best_match}")
            return best_match["category"], best_match["similarity_score"], "vector_similarity_low_confidence"
        
        print(f" DEBUG: No suitable matches found")
        return None, 0.0, "no_suitable_matches"

    def _fallback_categorization(
        self,
        transaction: Transaction,
        user_categories: UserCategories,
        confidence_threshold: float = 0.3,
    ) -> tuple[str | None, float, str]:
        """
        Fallback categorization when no similar transactions are found.

        Args:
            transaction: Transaction to categorize
            user_categories: User's categories
            confidence_threshold: Minimum confidence to assign a category

        Returns:
            Tuple of (category, confidence_score, method)
            category can be None if no suitable category is found
        """
        # Simple rule-based categorization
        description_lower = transaction.description.lower()

        # Define some basic rules with more comprehensive keywords
        rules = {
            "Alimentação": [
                "ifood",
                "rappi",
                "uber eats",
                "mcdonalds",
                "burger",
                "pizza",
                "restaurante",
                "lanche",
                "comida",
                "food",
            ],
            "Transporte": [
                "uber",
                "99",
                "taxi",
                "metro",
                "onibus",
                "gasolina",
                "combustivel",
                "estacionamento",
                "pedagio",
            ],
            "Streaming": [
                "netflix",
                "spotify",
                "disney",
                "hbo",
                "prime",
                "youtube",
                "music",
                "video",
            ],
            "Shopping": [
                "amazon",
                "mercadolivre",
                "magazine",
                "loja",
                "store",
                "shop",
                "mall",
                "centro comercial",
            ],
            "Saúde": [
                "farmacia",
                "drogaria",
                "hospital",
                "medico",
                "consulta",
                "exame",
                "plano de saude",
            ],
            "Pet": [
                "pet",
                "petlove",
                "pet shop",
                "veterinario",
                "racao",
                "cachorro",
                "gato",
                "animal",
            ],
        }

        # Check rules against user categories
        for user_category in user_categories.categories:
            if user_category in rules:
                for keyword in rules[user_category]:
                    if keyword in description_lower:
                        return user_category, 0.6, "rule_based"

        # If no rules match, check if any user category has a reasonable match
        for user_category in user_categories.categories:
            # Simple keyword matching for user categories
            if user_category.lower() in description_lower:
                return user_category, 0.4, "keyword_match"

            # Check if description contains words similar to category
            category_words = user_category.lower().split()
            description_words = description_lower.split()

            # If at least 50% of category words are in description
            matches = sum(
                1
                for word in category_words
                if any(word in desc_word for desc_word in description_words)
            )
            if matches >= len(category_words) * 0.5:
                return user_category, 0.3, "partial_keyword_match"

        # No suitable category found - return None with 0 confidence
        return None, 0.0, "no_suitable_category"

    async def get_user_categories(self, user_id: str) -> UserCategories:
        """
        Get user's categories from vector store.

        Args:
            user_id: User identifier

        Returns:
            User categories
        """
        # Get user's transactions to extract unique categories
        transactions = await self.vector_store.get_user_transactions(user_id)

        # Extract unique categories
        categories = list(set(tx["category"] for tx in transactions))

        return UserCategories(
            user_id=user_id, categories=categories if categories else ["Outros"]
        )

    async def update_user_categories(self, user_categories: UserCategories) -> bool:
        """
        Update user's categories.

        Args:
            user_categories: Updated user categories

        Returns:
            True if updated successfully
        """
        # For now, just validate the categories
        # In a real implementation, you might store this in a separate database
        if not user_categories.categories:
            raise ValueError("User must have at least one category")

        return True

    async def categorization(
        self, request: CategorizationRequest
    ) -> CategorizationResponse:
        """
        Process user feedback and update vector store for improved categorization.

        This method processes user feedback on categorizations:
        - If informed_category is provided: user wants to correct the categorization
        - If informed_category is null: user agrees with the system's categorization

        ALL transactions that pass through this endpoint are stored in the vector store
        for learning, as this represents user feedback and corrections.

        Args:
            request: Categorization request with transactions and user feedback

        Returns:
            Categorization response with updated transactions
        """
        # Generate or use provided session ID
        session_id = request.session_id or f"sess_{uuid.uuid4().hex[:8]}"

        # Process each transaction based on user feedback
        processed_transactions = []
        transactions_to_store = []

        for transaction in request.transactions:
            # Determine final category (user's choice or system's)
            final_category = (
                transaction.informed_category
                if transaction.informed_category is not None
                else transaction.category
            )

            # Check if user provided feedback
            if transaction.informed_category is not None:
                # User wants to correct the categorization
                processed_transaction = CategorizedTransaction(
                    transaction_id=transaction.transaction_id,
                    transaction=transaction.transaction,
                    category=transaction.informed_category,  # Use user's choice
                    informed_category=None,  # Clear informed_category after processing
                    confidence_score=1.0,  # User choice has highest confidence
                    categorization_method="user_feedback",
                    created_at=datetime.utcnow(),
                )
                
            else:
                # User agrees with system categorization, keep as is
                processed_transaction = transaction

            processed_transactions.append(processed_transaction)

            # Store transaction in vector store for learning (if it has a category)
            if final_category is not None:
                transactions_to_store.append(
                    {
                        "transaction_id": transaction.transaction_id,
                        "transaction": transaction.transaction,
                        "category": final_category,
                    }
                )

        # Store all transactions in vector store for learning (APENAS AQUI)
        if transactions_to_store:
            await self._store_transactions_for_learning(
                request.user_id, transactions_to_store
            )

        return CategorizationResponse(
            session_id=session_id,
            user_id=request.user_id,
            confidence_threshold=request.confidence_threshold,
            categorized_transactions=processed_transactions,
        )

    async def _store_transactions_for_learning(
        self, user_id: str, transactions_to_store: list[dict]
    ) -> None:
        """
        Store transactions in vector store for learning from user feedback.

        Args:
            user_id: User identifier
            transactions_to_store: List of transactions to store with their categories
        """
        print(f"🔍 DEBUG: Storing {len(transactions_to_store)} transactions for user {user_id}")
        
        # Verify vector store is working
        print(f"🔍 DEBUG: Verifying vector store connection...")
        try:
            total_docs = self.vector_store.collection.count()
            print(f"🔍 DEBUG: Vector store has {total_docs} total documents")
        except Exception as e:
            print(f"❌ DEBUG: Vector store connection failed: {e}")
            # Try to reinitialize
            print(f"🔍 DEBUG: Attempting to reinitialize vector store...")
            self.vector_store = VectorStoreManager(os.getenv("OPENAI_API_KEY"))
            total_docs = self.vector_store.collection.count()
            print(f"🔍 DEBUG: After reinit - Vector store has {total_docs} total documents")

        stored_count = 0
        for tx_data in transactions_to_store:
            transaction_id = tx_data["transaction_id"]
            transaction = tx_data["transaction"]
            category = tx_data["category"]

            try:
                # Store new transaction
                stored_id = await self.vector_store.store_transaction(
                    user_id, transaction, category, transaction_id
                )
                stored_count += 1
                print(f"✅ DEBUG: Stored transaction {transaction_id} with category {category}")
            except Exception as e:
                print(f"❌ DEBUG: Failed to store transaction {transaction_id}: {e}")

        print(f"✅ DEBUG: Completed storing {stored_count} transactions for learning")
        
        # FINAL VERIFICATION - Check if transactions are actually in the database
        print(f"🔍 DEBUG: === FINAL VERIFICATION ===")
        try:
            # Check total documents in collection
            total_docs = self.vector_store.collection.count()
            print(f"🔍 DEBUG: Total documents in collection: {total_docs}")
            
            # Get all transactions for this user
            all_user_transactions = await self.vector_store.get_user_transactions(user_id)
            print(f"🔍 DEBUG: Final check - Found {len(all_user_transactions)} transactions for user '{user_id}'")
            
            # List all transaction IDs for this user
            user_transaction_ids = [tx.get('transaction_id') for tx in all_user_transactions]
            print(f"🔍 DEBUG: User transaction IDs: {user_transaction_ids}")
            
            # Check if our stored transactions are there
            expected_ids = [tx["transaction_id"] for tx in transactions_to_store]
            missing_ids = [tid for tid in expected_ids if tid not in user_transaction_ids]
            
            if missing_ids:
                print(f"❌ DEBUG: MISSING TRANSACTIONS: {missing_ids}")
            else:
                print(f"✅ DEBUG: All transactions successfully stored and verified!")
                
        except Exception as e:
            print(f"❌ DEBUG: Error in final verification: {e}")

    async def delete_user(self, user_id: str) -> dict:
        """
        Delete user and all their data (transactions and categories).

        Args:
            user_id: User identifier

        Returns:
            Dictionary with deletion statistics
        """

        deletion_stats = {
            "user_id": user_id,
            "transactions_deleted": 0,
            "categories_deleted": False,
            "errors": [],
        }

        try:
            # Delete all user transactions
            tx_deletion_result = await self.vector_store.delete_user_transactions(
                user_id
            )
            deletion_stats["transactions_deleted"] = tx_deletion_result[
                "deleted_transactions"
            ]

            if tx_deletion_result.get("errors"):
                deletion_stats["errors"].extend(tx_deletion_result["errors"])


        except Exception as e:
            error_msg = f"Failed to delete user {user_id}: {e}"
            deletion_stats["errors"].append(error_msg)
            print(f"❌ DEBUG: {error_msg}")

        return deletion_stats
