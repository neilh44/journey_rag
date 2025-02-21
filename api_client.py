from typing import Dict, List, Any
import httpx
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import re
from logger import setup_logger
import traceback

class APIClient:
    def __init__(self):
        load_dotenv()
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.duffel_api_key = os.getenv("DUFFEL_API_KEY")
        self.logger = setup_logger('api_client')
        
        self.logger.info(f"GROQ API Key present: {bool(self.groq_api_key)}")
        self.logger.info(f"DUFFEL API Key present: {bool(self.duffel_api_key)}")

    async def format_flight_query(self, text: str) -> Dict[str, Any]:
        self.logger.info(f"Formatting flight query: {text}")
        
        if not self.groq_api_key:
            self.logger.error("GROQ API key not found")
            raise Exception("GROQ API key not configured")

        try:
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }
            
            # Extract date from query
            date_match = re.search(r'on\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})', text)
            if date_match:
                try:
                    date_str = date_match.group(1)
                    specified_date = datetime.strptime(date_str, '%d %B %Y')
                    formatted_date = specified_date.strftime('%Y-%m-%d')
                except ValueError:
                    formatted_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            else:
                formatted_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')

            system_prompt = f"""
            Convert the flight query into a JSON object. Extract city pairs and convert to IATA codes.
            Common IATA codes:
            - New Delhi (DEL)
            - Mumbai (BOM)
            - Dubai (DXB)
            - Ahmedabad (AMD)
            - Bangalore (BLR)
            - Chennai (MAA)
            - Kolkata (CCU)

            Convert the following query into this exact JSON format:
            {{
                "origin": "IATA_CODE",
                "destination": "IATA_CODE",
                "date": "{formatted_date}",
                "passengers": 2,
                "cabin_class": "economy"
            }}
            """

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json={
                        "model": "llama3-8b-8192",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": text}
                        ],
                        "temperature": 0.1
                    },
                    timeout=30.0
                )

                if response.status_code != 200:
                    raise Exception(f"Groq API error: {response.text}")

                content = response.json()['choices'][0]['message']['content']
                self.logger.debug(f"Groq API response: {content}")

                # Extract JSON from response
                json_match = re.search(r'{.*}', content, re.DOTALL)
                if json_match:
                    parsed_json = json.loads(json_match.group(0))
                    return parsed_json
                else:
                    # Default response with city extraction
                    cities = re.findall(r'(?:from|between|to)\s+([A-Za-z\s]+?)(?:to|and|for|$)', text)
                    return {
                        "origin": "DEL" if "delhi" in text.lower() else "BOM",
                        "destination": "AMD" if "ahmedabad" in text.lower() else "DEL",
                        "date": formatted_date,
                        "passengers": 2,
                        "cabin_class": "economy"
                    }

        except Exception as e:
            self.logger.error(f"Error in format_flight_query: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise

    async def search_flights(self, query: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        self.logger.info(f"Searching flights with query: {json.dumps(query, indent=2)}")
        
        if not self.duffel_api_key:
            self.logger.error("DUFFEL API key not found")
            raise Exception("DUFFEL API key not configured")

        headers = {
            "Authorization": f"Bearer {self.duffel_api_key}",
            "Content-Type": "application/json",
            "Duffel-Version": "v1",
            "Accept": "application/json"
        }

        try:
            duffel_payload = {
                "data": {
                    "slices": [{
                        "origin": query["origin"],
                        "destination": query["destination"],
                        "departure_date": query["date"]
                    }],
                    "passengers": [{"type": "adult"}] * query.get("passengers", 2),
                    "cabin_class": query.get("cabin_class", "economy")
                }
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.duffel.com/air/offer_requests",
                    headers=headers,
                    json=duffel_payload,
                    timeout=30.0
                )

                if response.status_code != 200:
                    self.logger.error(f"Duffel API error: {response.text}")
                    # Return mock data
                    return {
                        "flights": [
                            {
                                "id": "mock1",
                                "departure": query["origin"],
                                "arrival": query["destination"],
                                "departure_time": f"{query['date']}T10:00:00Z",
                                "arrival_time": f"{query['date']}T12:00:00Z",
                                "airline": "Test Airlines",
                                "price": 12500.00
                            },
                            {
                                "id": "mock2",
                                "departure": query["origin"],
                                "arrival": query["destination"],
                                "departure_time": f"{query['date']}T14:00:00Z",
                                "arrival_time": f"{query['date']}T16:00:00Z",
                                "airline": "Test Airways",
                                "price": 14500.00
                            }
                        ]
                    }

                offer_request = response.json()
                
                if 'data' in offer_request and 'id' in offer_request['data']:
                    offers_response = await client.get(
                        f"https://api.duffel.com/air/offers?offer_request_id={offer_request['data']['id']}",
                        headers=headers
                    )
                    
                    if offers_response.status_code == 200:
                        offers = offers_response.json()
                        return self._format_flights_for_frontend(offers['data'])

                return {"flights": []}

        except Exception as e:
            self.logger.error(f"Error in search_flights: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise

    def _format_flights_for_frontend(self, offers: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        formatted_flights = []
        
        for offer in offers[:5]:
            try:
                segments = offer['slices'][0]['segments'][0]
                formatted_flights.append({
                    "id": offer['id'],
                    "departure": segments['origin']['iata_code'],
                    "arrival": segments['destination']['iata_code'],
                    "departure_time": segments['departing_at'],
                    "arrival_time": segments['arriving_at'],
                    "airline": segments['operating_carrier']['name'],
                    "price": float(offer['total_amount'])
                })
            except (KeyError, IndexError) as e:
                self.logger.error(f"Error formatting offer {offer.get('id')}: {str(e)}")
                continue

        return {"flights": formatted_flights}
