"""Vector store management for transaction categorization."""

import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI

from app.models import Transaction


class VectorStoreManager:
    """Manages ChromaDB vector store for transaction categorization."""
    
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, openai_api_key: str, persist_path: str = None):
        """
        Initialize vector store manager.

        Args:
            openai_api_key: OpenAI API key for embeddings
            persist_path: Path for ChromaDB persistence
        """
        if self._initialized:
            return
            
        self.openai_client = AsyncOpenAI(api_key=openai_api_key)
        self.embedding_model = "text-embedding-3-small"
        self.persist_path = persist_path or os.getenv(
            "VECTOR_STORE_PATH", "./vector_store"
        )

        # Initialize ChromaDB
        self._init_chromadb()
        self._initialized = True

    def _init_chromadb(self):
        """Initialize ChromaDB."""
        import chromadb
        from chromadb.config import Settings

        # Use absolute path to avoid issues with relative paths in different contexts
        if not os.path.isabs(self.persist_path):
            self.persist_path = os.path.abspath(self.persist_path)
        
        print(f"🔍 DEBUG: Initializing ChromaDB with persist_path: {self.persist_path}")

        # Check if directory is writable
        try:
            os.makedirs(self.persist_path, exist_ok=True)
            # Test write permissions
            test_file = os.path.join(self.persist_path, "test_write.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            print(f"✅ DEBUG: Directory {self.persist_path} is writable")
        except Exception as e:
            print(f"❌ DEBUG: Directory {self.persist_path} is NOT writable: {e}")
            # Try to use a fallback directory
            fallback_path = "/tmp/vector_store"
            os.makedirs(fallback_path, exist_ok=True)
            self.persist_path = fallback_path
            print(f"🔄 Using fallback vector store directory: {self.persist_path}")

        # Initialize ChromaDB
        print(f"🔍 DEBUG: Creating ChromaDB client with path: {self.persist_path}")
        self.client = chromadb.PersistentClient(
            path=self.persist_path,
            settings=Settings(anonymized_telemetry=False, is_persistent=True),
        )

        # Get or create collection
        print(f"🔍 DEBUG: Getting or creating collection 'transaction_categories'")
        self.collection = self.client.get_or_create_collection(
            name="transaction_categories",
            metadata={"description": "Transaction categorization embeddings"},
        )
        print(f"✅ DEBUG: ChromaDB initialized successfully")

    async def create_embedding(self, text: str) -> List[float]:
        """
        Create embedding for text using OpenAI.

        Args:
            text: Text to embed

        Returns:
            List of embedding values
        """
        try:
            response = await self.openai_client.embeddings.create(
                model=self.embedding_model, input=text
            )
            print(f"🔍 DEBUG: Response keys: {list(response.__dict__.keys())}")
            embedding = response.data[0].embedding
            print(
                f"🔍 DEBUG: Response data embedding (first 5 values): {embedding[:5]}"
            )
            print(f"🔍 DEBUG: Embedding length: {len(embedding)}")
            return response.data[0].embedding
        except Exception as e:
            raise Exception(f"Failed to create embedding: {e}") from e

    async def store_transaction(
        self,
        user_id: str,
        transaction: Transaction,
        category: str,
        transaction_id: str = None,
    ) -> str:
        """
        Store transaction with embedding in vector store.

        Args:
            user_id: User identifier
            transaction: Transaction object
            category: Assigned category
            transaction_id: Optional transaction ID

        Returns:
            Stored transaction ID
        """
        # Generate transaction ID if not provided
        if transaction_id is None:
            transaction_id = f"{user_id}_{uuid.uuid4().hex[:8]}"

        print(f"💾 DEBUG: Storing transaction {transaction_id} for user {user_id} with category {category}")

        # Create embedding from transaction description
        print(f"🔍 DEBUG: Creating embedding for description: {transaction.description}")
        embedding = await self.create_embedding(transaction.description)

        # Prepare metadata
        metadata = {
            "user_id": user_id,
            "transaction_id": transaction_id,
            "description": transaction.description,
            "category": category,
            "stored_at": datetime.utcnow().isoformat(),
        }
        print(f"🔍 DEBUG: Prepared metadata: {metadata}")

        # Store in ChromaDB
        print(f"🔍 DEBUG: Adding to ChromaDB collection...")
        try:
            # Get current count before adding
            count_before = self.collection.count()
            print(f"🔍 DEBUG: Documents in collection before: {count_before}")
            
            # Get all existing IDs to check for conflicts
            all_results = self.collection.get()
            existing_ids = all_results.get("ids", [])
            print(f"🔍 DEBUG: Existing IDs in collection: {existing_ids}")
            
            if transaction_id in existing_ids:
                print(f"⚠️ DEBUG: Transaction ID {transaction_id} already exists!")
                # Generate new ID
                transaction_id = f"{user_id}_{uuid.uuid4().hex[:8]}"
                metadata["transaction_id"] = transaction_id
                print(f"🔍 DEBUG: Generated new ID: {transaction_id}")
            
            # Try to add with explicit error handling
            try:
                self.collection.add(
                    embeddings=[embedding],
                    documents=[transaction.description],
                    metadatas=[metadata],
                    ids=[transaction_id],
                )
                print(f"✅ DEBUG: Successfully called collection.add() for {transaction_id}")
            except Exception as add_error:
                print(f"❌ DEBUG: Error in collection.add(): {add_error}")
                raise
            
            # Get count after adding
            count_after = self.collection.count()
            print(f"🔍 DEBUG: Documents in collection after: {count_after}")
            
            # Verify the document was actually added
            try:
                verify_results = self.collection.get(ids=[transaction_id])
                if verify_results["ids"]:
                    print(f"✅ DEBUG: Transaction {transaction_id} verified in collection")
                else:
                    print(f"❌ DEBUG: Transaction {transaction_id} NOT found in collection after adding!")
            except Exception as verify_error:
                print(f"❌ DEBUG: Error verifying transaction: {verify_error}")
            
            if count_after > count_before:
                print(f"✅ DEBUG: Successfully added transaction {transaction_id} to ChromaDB (count increased)")
            else:
                print(f"⚠️ DEBUG: Transaction added but count didn't increase - possible issue")
            
        except Exception as e:
            print(f"❌ DEBUG: Failed to add to ChromaDB: {e}")
            raise

        return transaction_id

    async def search_similar_transactions(
        self, description: str, user_id: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar transactions by description.
        """
        print(f"🔍 DEBUG: search_similar_transactions called with description='{description}'")
        
        # First, try exact text match - simplified approach
        try:
            # Get all transactions for this user first
            all_user_transactions = self.collection.get(
                where={"user_id": user_id}
            )
            
            print(f"🔍 DEBUG: Exact matches result: {all_user_transactions}")
            
            # Filter for exact matches
            exact_matches = []
            for i, doc in enumerate(all_user_transactions["documents"]):
                if doc == description:
                    metadata = all_user_transactions["metadatas"][i]
                    exact_matches.append({
                        "description": doc,
                        "category": metadata["category"],
                        "transaction_id": metadata["transaction_id"],
                        "user_id": metadata["user_id"],
                        "stored_at": metadata["stored_at"],
                        "similarity_score": 1.0,  # Exact match
                        "match_type": "exact"
                    })
            
            if exact_matches:
                print(f"🔍 DEBUG: Found exact matches!")
                return exact_matches[:limit]
                
        except Exception as e:
            print(f"🔍 DEBUG: Error in exact match search: {e}")
        
        print(f"🔍 DEBUG: No exact matches, trying vector similarity...")
        
        # If no exact matches, try vector similarity
        try:
            # Generate embedding for the description
            embedding = await self.create_embedding(description)
            
            # Search for similar transactions
            results = self.collection.query(
                query_embeddings=[embedding],
                where={"user_id": user_id},
                n_results=limit,
                include=["metadatas", "documents", "distances"]
            )
            
            print(f"🔍 DEBUG: Vector similarity results: {results}")
            
            similar_transactions = []
            if results["ids"] and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    metadata = results["metadatas"][0][i]
                    document = results["documents"][0][i]
                    distance = results["distances"][0][i]
                    
                    # Convert distance to similarity score (ensure it's always positive)
                    # Use max(0, 1 - distance) to ensure similarity_score >= 0
                    similarity_score = max(0.0, 1.0 - distance)
                    
                    similar_transactions.append({
                        "description": document,
                        "category": metadata["category"],
                        "transaction_id": metadata["transaction_id"],
                        "user_id": metadata["user_id"],
                        "stored_at": metadata["stored_at"],
                        "similarity_score": similarity_score,
                        "match_type": "vector_similarity"
                    })
            
            return similar_transactions
            
        except Exception as e:
            print(f"🔍 DEBUG: Error in vector similarity search: {e}")
            return []

    async def update_transaction_category(
        self, user_id: str, transaction_id: str, new_category: str
    ) -> bool:
        """
        Update category for existing transaction.

        Args:
            user_id: User identifier
            transaction_id: Transaction identifier
            new_category: New category

        Returns:
            True if updated successfully
        """
        try:
            # Get existing transaction
            results = self.collection.get(
                ids=[transaction_id], where={"user_id": user_id}
            )

            if results["metadatas"] and results["metadatas"][0]:
                # Update metadata
                metadata = results["metadatas"][0]
                metadata["category"] = new_category
                metadata["updated_at"] = datetime.utcnow().isoformat()

                # Update in ChromaDB
                self.collection.update(ids=[transaction_id], metadatas=[metadata])
                return True

        except Exception as e:
            print(f"⚠️ Failed to update in ChromaDB: {e}")
            return False

        return False

    async def get_user_transactions(
        self, user_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get transactions for a specific user.

        Args:
            user_id: User identifier
            limit: Maximum number of results

        Returns:
            List of user transactions
        """
        print(
            f"🔍 DEBUG: get_user_transactions called for user_id='{user_id}', limit={limit}"
        )

        # Query by user_id in metadata
        print(f"🔍 DEBUG: Querying ChromaDB collection for user_id='{user_id}'")
        try:
            results = self.collection.get(where={"user_id": user_id}, limit=limit)
            print(f"🔍 DEBUG: ChromaDB query results: {results}")
        except Exception as e:
            print(f"❌ DEBUG: Failed to query ChromaDB: {e}")
            raise

        transactions = []
        if results["metadatas"]:
            print(f"🔍 DEBUG: Found {len(results['metadatas'])} metadata entries")
            for i, metadata in enumerate(results["metadatas"]):
                transactions.append(
                    {
                        "transaction_id": metadata["transaction_id"],
                        "description": metadata["description"],
                        "category": metadata["category"],
                        "user_id": metadata["user_id"],
                        "stored_at": metadata["stored_at"],
                    }
                )
        else:
            print(f"🔍 DEBUG: No metadata found in results")

        print(
            f"✅ DEBUG: Found {len(transactions)} transactions in ChromaDB for user {user_id}"
        )
        return transactions

    async def delete_transaction(self, user_id: str, transaction_id: str) -> bool:
        """
        Delete transaction from vector store.

        Args:
            user_id: User identifier
            transaction_id: Transaction identifier

        Returns:
            True if deleted successfully
        """
        try:
            # Verify transaction belongs to user before deleting
            results = self.collection.get(
                ids=[transaction_id], where={"user_id": user_id}
            )
            
            if results["metadatas"] and results["metadatas"][0]:
                self.collection.delete(ids=[transaction_id])
                return True
                
        except Exception as e:
            print(f"⚠️ Failed to delete from ChromaDB: {e}")
            
        return False

    async def delete_user_transactions(self, user_id: str) -> dict:
        """
        Delete all transactions for a specific user.

        Args:
            user_id: User identifier

        Returns:
            Dictionary with deletion statistics
        """
        print(f"🗑️ DEBUG: Deleting all transactions for user {user_id}")

        try:
            # Get all transaction IDs for this user
            results = self.collection.get(where={"user_id": user_id})
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                deleted_count = len(results["ids"])
                print(f"🗑️ DEBUG: Deleted {deleted_count} transactions from ChromaDB")
                
                result = {
                    "user_id": user_id,
                    "deleted_transactions": deleted_count,
                    "chromadb_deleted": deleted_count,
                    "errors": None,
                }
            else:
                result = {
                    "user_id": user_id,
                    "deleted_transactions": 0,
                    "chromadb_deleted": 0,
                    "errors": None,
                }
                
        except Exception as e:
            error_msg = f"Failed to delete from ChromaDB: {e}"
            print(f"⚠️ DEBUG: {error_msg}")
            result = {
                "user_id": user_id,
                "deleted_transactions": 0,
                "chromadb_deleted": 0,
                "errors": [error_msg],
            }

        print(f"✅ DEBUG: Deletion completed for user {user_id}: {result}")
        return result

    async def get_all_transactions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all transactions (for debugging).

        Args:
            limit: Maximum number of results

        Returns:
            List of all transactions
        """
        results = self.collection.get(limit=limit)

        transactions = []
        if results["metadatas"]:
            for i, metadata in enumerate(results["metadatas"]):
                transactions.append(
                    {
                        "transaction_id": metadata["transaction_id"],
                        "description": metadata["description"],
                        "category": metadata["category"],
                        "user_id": metadata["user_id"],
                        "stored_at": metadata["stored_at"],
                    }
                )

        return transactions

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store collection.

        Returns:
            Dictionary with collection statistics
        """
        try:
            count = self.collection.count()
            stats = {
                "total_transactions": count,
                "collection_name": self.collection.name,
                "persist_path": self.persist_path,
            }
        except Exception as e:
            print(f"⚠️ Failed to get ChromaDB stats: {e}")
            stats = {
                "total_transactions": 0,
                "collection_name": "transaction_categories",
                "persist_path": self.persist_path,
                "error": str(e),
            }

        return stats
