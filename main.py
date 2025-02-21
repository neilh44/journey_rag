from embeddings import CustomEmbedding, ChromaDBManager
from api_client import APIClient
from datetime import datetime
import json

class FlightSearchPipeline:
    def __init__(self):
        self.embedding_model = CustomEmbedding()
        self.chroma_manager = ChromaDBManager(self.embedding_model)
        self.api_client = APIClient()

    async def process_query(self, user_query: str):
        try:
            # Store query embeddings
            query_id = self.chroma_manager.store_text_embeddings(
                user_query,
                metadata={"type": "flight_search", "timestamp": datetime.now().isoformat()}
            )
            
            # Get formatted JSON from Groq
            formatted_json = await self.api_client.query_llama_groq(user_query)
            
            # Query Duffel API
            duffel_response = await self.api_client.query_duffel_api(formatted_json)
            
            # Store API response
            response_id = self.chroma_manager.store_api_response(duffel_response, user_query)
            
            # Find similar queries
            similar_results = self.chroma_manager.query_similar_responses(user_query)
            
            return {
                "query_id": query_id,
                "response_id": response_id,
                "similar_results": similar_results,
                "duffel_response": duffel_response
            }
            
        except Exception as e:
            print(f"Error in pipeline: {str(e)}")
            return None

async def main():
    pipeline = FlightSearchPipeline()
    user_query = "find me flights between new delhi to mumbai next week"
    results = await pipeline.process_query(user_query)
    if results:
        print("\nSimilar results found:")
        print(json.dumps(results["similar_results"], indent=2))

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
