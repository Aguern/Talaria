"""
Notion API Client for DéMé Traiteur Pack

Handles all interactions with Notion databases:
- Clients
- Prestations
- Catalogue
- Lignes de Devis
"""

import os
import httpx
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class NotionClient:
    """Client for Notion API operations"""

    def __init__(self):
        self.api_token = os.getenv("NOTION_API_TOKEN")
        self.clients_db_id = os.getenv("NOTION_DATABASE_CLIENTS_ID")
        self.prestations_db_id = os.getenv("NOTION_DATABASE_PRESTATIONS_ID")
        self.catalogue_db_id = os.getenv("NOTION_DATABASE_CATALOGUE_ID")
        self.lignes_devis_db_id = os.getenv("NOTION_DATABASE_LIGNES_DEVIS_ID")

        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }

    async def find_client_by_email(self, email: str) -> Optional[str]:
        """
        Search for a client by email in the Clients database

        Args:
            email: Client email address

        Returns:
            Client page ID if found, None otherwise
        """
        url = f"{self.base_url}/databases/{self.clients_db_id}/query"

        payload = {
            "filter": {
                "property": "Email",
                "email": {
                    "equals": email
                }
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                data = response.json()

                if data.get("results"):
                    client_id = data["results"][0]["id"]
                    logger.info(f"Client found with email {email}: {client_id}")
                    return client_id
                else:
                    logger.info(f"No client found with email {email}")
                    return None

        except Exception as e:
            logger.error(f"Error searching for client: {str(e)}")
            raise

    async def create_client(self, client_data: Dict[str, Any]) -> str:
        """
        Create a new client in the Clients database

        Args:
            client_data: Dictionary with keys: nom_complet, email, telephone,
                        ville, adresse, type_client

        Returns:
            Created client page ID
        """
        url = f"{self.base_url}/pages"

        # Extract first name and last name from nom_complet
        nom_complet = client_data.get("nom_complet", "")
        prenom = ""
        nom = ""

        if nom_complet:
            parts = nom_complet.split(' ', 1)
            prenom = parts[0] if len(parts) > 0 else ""
            nom = parts[1] if len(parts) > 1 else ""

        properties = {
            "Nom complet": {
                "title": [{"text": {"content": nom_complet}}]
            },
            "Email": {
                "email": client_data.get("email", "")
            }
        }

        # Add Prénom and Nom
        if prenom:
            properties["Prénom"] = {
                "rich_text": [{"text": {"content": prenom}}]
            }

        if nom:
            properties["Nom"] = {
                "rich_text": [{"text": {"content": nom}}]
            }

        # Add optional fields if provided
        if client_data.get("telephone"):
            properties["Téléphone"] = {
                "phone_number": client_data["telephone"]
            }

        if client_data.get("ville"):
            properties["Ville"] = {
                "rich_text": [{"text": {"content": client_data["ville"]}}]
            }

        if client_data.get("adresse"):
            properties["Adresse"] = {
                "rich_text": [{"text": {"content": client_data["adresse"]}}]
            }

        if client_data.get("type_client"):
            properties["Type client"] = {
                "select": {"name": client_data["type_client"]}
            }

        payload = {
            "parent": {"database_id": self.clients_db_id},
            "properties": properties
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                data = response.json()

                client_id = data["id"]
                logger.info(f"Client created: {client_id}")
                return client_id

        except Exception as e:
            logger.error(f"Error creating client: {str(e)}")
            raise

    async def create_prestation(self, prestation_data: Dict[str, Any], client_id: str) -> Dict[str, str]:
        """
        Create a new prestation in the Prestations database

        Args:
            prestation_data: Dictionary with keys: nom_prestation, date, pax,
                           moment, statut
            client_id: Notion page ID of the related client

        Returns:
            Dictionary with 'id' and 'url' of the created prestation
        """
        url = f"{self.base_url}/pages"

        properties = {
            "Nom prestation": {
                "title": [{"text": {"content": prestation_data.get("nom_prestation", "")}}]
            },
            "Date": {
                "date": {
                    "start": prestation_data.get("date", "")
                }
            },
            "PAX": {
                "number": prestation_data.get("pax", 0)
            },
            "Moment": {
                "select": {"name": prestation_data.get("moment", "Midi")}
            },
            "Statut": {
                "select": {"name": prestation_data.get("statut", "A confirmer")}
            },
            "Client": {
                "relation": [{"id": client_id}]
            }
        }

        payload = {
            "parent": {"database_id": self.prestations_db_id},
            "properties": properties
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                data = response.json()

                prestation_id = data["id"]
                prestation_url = data["url"]
                logger.info(f"Prestation created: {prestation_id}")
                return {"id": prestation_id, "url": prestation_url}

        except Exception as e:
            logger.error(f"Error creating prestation: {str(e)}")
            raise

    async def find_catalogue_item_by_name(self, item_name: str) -> Optional[Dict[str, Any]]:
        """
        Find a catalogue item by name

        Args:
            item_name: Name of the catalogue item

        Returns:
            Dictionary with 'id' and 'prix_ht' if found, None otherwise
        """
        url = f"{self.base_url}/databases/{self.catalogue_db_id}/query"

        payload = {
            "filter": {
                "property": "Nom",
                "title": {
                    "contains": item_name
                }
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                data = response.json()

                if data.get("results"):
                    item = data["results"][0]
                    item_id = item["id"]

                    # Extract price from properties
                    prix_ht = None
                    if "Prix" in item["properties"]:
                        prix_prop = item["properties"]["Prix"]
                        if prix_prop.get("number") is not None:
                            prix_ht = prix_prop["number"]

                    logger.info(f"Catalogue item found: {item_name} ({item_id})")
                    return {"id": item_id, "prix_ht": prix_ht}
                else:
                    logger.warning(f"Catalogue item not found: {item_name}")
                    return None

        except Exception as e:
            logger.error(f"Error searching catalogue: {str(e)}")
            raise

    async def create_devis_line(
        self,
        prestation_id: str,
        catalogue_item_id: str,
        catalogue_item_name: str,
        quantity: int
    ) -> str:
        """
        Create a line in Lignes de Devis

        Args:
            prestation_id: Notion page ID of the related prestation
            catalogue_item_id: Notion page ID of the catalogue item
            catalogue_item_name: Name of the catalogue item (for Description)
            quantity: Quantity for this line

        Returns:
            Created line page ID
        """
        url = f"{self.base_url}/pages"

        properties = {
            "Description": {
                "title": [{"text": {"content": catalogue_item_name}}]
            },
            "Prestation": {
                "relation": [{"id": prestation_id}]
            },
            "Item du catalogue": {
                "relation": [{"id": catalogue_item_id}]
            },
            "Quantité": {
                "number": quantity
            }
        }

        payload = {
            "parent": {"database_id": self.lignes_devis_db_id},
            "properties": properties
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                data = response.json()

                line_id = data["id"]
                logger.info(f"Devis line created: {line_id}")
                return line_id

        except Exception as e:
            logger.error(f"Error creating devis line: {str(e)}")
            raise

    async def get_devis_lines_for_prestation(self, prestation_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all devis lines for a given prestation

        Args:
            prestation_id: Notion page ID of the prestation

        Returns:
            List of dictionaries with keys: item_name, description, quantity, prix_unitaire, total_ligne
        """
        url = f"{self.base_url}/databases/{self.lignes_devis_db_id}/query"

        payload = {
            "filter": {
                "property": "Prestation",
                "relation": {
                    "contains": prestation_id
                }
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                data = response.json()

                lines = []
                for line in data.get("results", []):
                    props = line["properties"]

                    # Extract description from title property
                    description = ""
                    if "Description" in props:
                        title_array = props["Description"].get("title", [])
                        if title_array:
                            description = title_array[0]["text"]["content"]

                    # Extract item name from catalogue relation
                    item_name = "N/A"
                    if "Item du catalogue" in props and props["Item du catalogue"].get("relation"):
                        catalogue_item_id = props["Item du catalogue"]["relation"][0]["id"]
                        # Fetch the catalogue item to get its name
                        item_data = await self._get_page(catalogue_item_id)
                        if item_data and "Nom" in item_data["properties"]:
                            title_array = item_data["properties"]["Nom"].get("title", [])
                            if title_array:
                                item_name = title_array[0]["text"]["content"]

                    # Extract quantity
                    quantity = props.get("Quantité", {}).get("number", 0)

                    # Extract prix unitaire (rollup)
                    prix_unitaire = 0
                    if "Prix unitaire" in props:
                        rollup = props["Prix unitaire"].get("rollup", {})
                        if rollup.get("type") == "number":
                            prix_unitaire = rollup.get("number", 0)

                    # Extract total ligne (formula)
                    total_ligne = 0
                    if "Total ligne" in props:
                        formula = props["Total ligne"].get("formula", {})
                        if formula.get("type") == "number":
                            total_ligne = formula.get("number", 0)

                    lines.append({
                        "item_name": item_name,
                        "description": description,
                        "quantity": quantity,
                        "prix_unitaire": prix_unitaire,
                        "total_ligne": total_ligne
                    })

                logger.info(f"Retrieved {len(lines)} devis lines for prestation {prestation_id}")
                return lines

        except Exception as e:
            logger.error(f"Error retrieving devis lines: {str(e)}")
            raise

    async def _get_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a Notion page by ID

        Args:
            page_id: Notion page ID

        Returns:
            Page data dictionary or None
        """
        url = f"{self.base_url}/pages/{page_id}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching page {page_id}: {str(e)}")
            return None

    async def count_client_prestations(self, client_id: str) -> int:
        """
        Count the number of prestations for a given client

        Args:
            client_id: Notion page ID of the client

        Returns:
            Number of prestations linked to this client
        """
        url = f"{self.base_url}/databases/{self.prestations_db_id}/query"

        payload = {
            "filter": {
                "property": "Client",
                "relation": {
                    "contains": client_id
                }
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                data = response.json()

                count = len(data.get("results", []))
                logger.info(f"Client {client_id} has {count} prestations")
                return count

        except Exception as e:
            logger.error(f"Error counting prestations for client: {str(e)}")
            raise

    def calculate_segment(self, prestation_count: int) -> str:
        """
        Calculate the segment value based on number of prestations

        Args:
            prestation_count: Number of prestations

        Returns:
            Segment name: "Bronze", "Argent", "Or", or "Platine"
        """
        if prestation_count == 1:
            return "Bronze"
        elif prestation_count == 2:
            return "Argent"
        elif prestation_count in [3, 4]:
            return "Or"
        else:  # 5+
            return "Platine"

    async def update_client_segment(self, client_id: str, segment: str) -> None:
        """
        Update the "Segment valeur" property of a client

        Args:
            client_id: Notion page ID of the client
            segment: Segment value ("Bronze", "Argent", "Or", "Platine")
        """
        url = f"{self.base_url}/pages/{client_id}"

        payload = {
            "properties": {
                "Segment valeur": {
                    "select": {"name": segment}
                }
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(url, headers=self.headers, json=payload)
                response.raise_for_status()
                logger.info(f"Client {client_id} segment updated to {segment}")

        except Exception as e:
            logger.error(f"Error updating client segment: {str(e)}")
            raise
