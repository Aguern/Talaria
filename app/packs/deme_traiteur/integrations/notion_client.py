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
        self.regles_rh_db_id = os.getenv("NOTION_DATABASE_REGLES_RH_ID")

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
            },
            "Message": {
                "rich_text": [{"text": {"content": prestation_data.get("message", "")}}]
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

    async def get_rh_rules_for_prestation(
        self,
        pax: int,
        options: List[str]
    ) -> Dict[str, Any]:
        """
        Calculate required staff based on PAX and selected options

        Queries the "Règles RH" database to find the matching rule based on:
        - PAX range (PAX Min <= pax <= PAX Max)
        - Selected options (checkboxes must match)

        Args:
            pax: Number of persons for the event
            options: List of selected menu options

        Returns:
            Dict with:
                - chefs_count: Number of chefs needed
                - assistants_count: Number of assistants needed
                - chef_cost: Cost per chef (fixed at 220€)
                - assistant_cost: Cost per assistant (fixed at 90€)
                - total_cost: Total RH cost
                - rule_name: Name of the matching rule
        """
        url = f"{self.base_url}/databases/{self.regles_rh_db_id}/query"

        logger.info(f"Querying RH rules for PAX={pax}, options={options}")

        # Map full option names to checkbox column names
        option_mapping = {
            "Antipasti froids (Burrata, salade, carpaccio, etc.)": "Antipasti froids",
            "Antipasti chauds (fritures, arancini, crispy mozza, etc.)": "Antipasti chauds",
            "Pizza (sur-mesure)": "Pizza",
            "Pâtes (truffes, Carbonara, Ragù, etc.)": "Pâtes",
            "Risotto (champignon, fruits de mer, 4 fromages, etc.)": "Risotto",
            "Desserts (tiramisù, Panna cotta, crème pistache)": "Desserts",
            "Planches (charcuterie, fromage)": "Planches",
            "Boissons (soft, vin, cocktail)": "Boissons"
        }

        # Convert full names to short names
        short_options = set()
        for opt in options:
            if opt in option_mapping:
                short_options.add(option_mapping[opt])
            else:
                # If already short name, use it directly
                short_options.add(opt)

        # Query all rules (we'll filter client-side)
        payload = {}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                data = response.json()

                results = data.get("results", [])
                logger.info(f"Found {len(results)} RH rules in database")

                # Find best matching rule
                best_match = None
                best_match_score = -1

                for page in results:
                    props = page.get("properties", {})

                    # Extract PAX range
                    pax_min = props.get("PAX Min", {}).get("number", 0)
                    pax_max = props.get("PAX Max", {}).get("number", 999)

                    # Check if PAX is in range
                    if not (pax_min <= pax <= pax_max):
                        continue

                    # Extract option checkboxes
                    rule_options = set()
                    option_columns = [
                        "Antipasti froids", "Antipasti chauds", "Pizza",
                        "Pâtes", "Risotto", "Desserts", "Planches", "Boissons"
                    ]

                    for col in option_columns:
                        if props.get(col, {}).get("checkbox", False):
                            rule_options.add(col)

                    # Calculate match score (number of matching options)
                    matching_options = short_options & rule_options
                    match_score = len(matching_options)

                    # Only consider if all selected options are present in rule
                    if not short_options.issubset(rule_options):
                        continue

                    # Prefer rules with exact match or more specific rules
                    if match_score > best_match_score:
                        best_match_score = match_score
                        best_match = page

                if not best_match:
                    # Fallback: find rule with just PAX range match
                    logger.warning(f"No exact option match, falling back to PAX-only match")
                    for page in results:
                        props = page.get("properties", {})
                        pax_min = props.get("PAX Min", {}).get("number", 0)
                        pax_max = props.get("PAX Max", {}).get("number", 999)

                        if pax_min <= pax <= pax_max:
                            best_match = page
                            break

                if not best_match:
                    logger.error(f"No RH rule found for PAX={pax}, options={options}")
                    # Return default values
                    return {
                        "chefs_count": 1,
                        "assistants_count": 1,
                        "chef_cost": 220,
                        "assistant_cost": 90,
                        "total_cost": 310,
                        "rule_name": "Default (no rule found)"
                    }

                # Extract staff requirements
                props = best_match.get("properties", {})
                chefs_count = props.get("Chefs nécessaires", {}).get("number", 1)
                assistants_count = props.get("Assistants nécessaires", {}).get("number", 1)

                # Get rule name
                rule_name_prop = props.get("Nom règle", {}).get("title", [])
                rule_name = rule_name_prop[0].get("plain_text", "Unknown") if rule_name_prop else "Unknown"

                # Fixed costs (as per PDF example)
                chef_cost = 220  # Chef Pizzaiolo cost
                assistant_cost = 90  # Chef de rang / Assistant cost

                total_cost = (chefs_count * chef_cost) + (assistants_count * assistant_cost)

                result = {
                    "chefs_count": chefs_count,
                    "assistants_count": assistants_count,
                    "chef_cost": chef_cost,
                    "assistant_cost": assistant_cost,
                    "total_cost": total_cost,
                    "rule_name": rule_name
                }

                logger.info(f"RH calculation: {result}")
                return result

        except Exception as e:
            logger.error(f"Error querying RH rules: {str(e)}")
            # Return default values on error
            return {
                "chefs_count": 1,
                "assistants_count": 1,
                "chef_cost": 220,
                "assistant_cost": 90,
                "total_cost": 310,
                "rule_name": "Default (error)"
            }

    async def create_lignes_devis_rh(
        self,
        prestation_id: str,
        nb_chefs: int,
        nb_assistants: int
    ) -> List[str]:
        """
        Crée les lignes de devis RH (Chef + Assistant)

        Args:
            prestation_id: ID de la prestation
            nb_chefs: Nombre de chefs nécessaires
            nb_assistants: Nombre d'assistants nécessaires

        Returns:
            Liste des IDs des lignes de devis créées
        """
        ligne_ids = []

        # Récupérer les items RH du catalogue
        catalogue_url = f"{self.base_url}/databases/{self.catalogue_db_id}/query"

        # Rechercher "Chef Pizzaïolo" dans le catalogue
        payload_chef = {
            "filter": {
                "and": [
                    {
                        "property": "Nom",
                        "title": {
                            "contains": "Chef"
                        }
                    },
                    {
                        "property": "Type",
                        "select": {
                            "equals": "RH"
                        }
                    }
                ]
            }
        }

        # Rechercher "Assistant" dans le catalogue
        payload_assistant = {
            "filter": {
                "and": [
                    {
                        "property": "Nom",
                        "title": {
                            "contains": "Assistant"
                        }
                    },
                    {
                        "property": "Type",
                        "select": {
                            "equals": "RH"
                        }
                    }
                ]
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                # Récupérer Chef
                if nb_chefs > 0:
                    response_chef = await client.post(
                        catalogue_url,
                        headers=self.headers,
                        json=payload_chef
                    )
                    response_chef.raise_for_status()
                    chef_results = response_chef.json().get("results", [])

                    if not chef_results:
                        error_msg = (
                            "Configuration error: Item 'Chef Pizzaïolo' not found in Catalogue. "
                            "Please ensure an item with 'Chef' in the name and Type='RH' exists."
                        )
                        logger.error(error_msg)
                        raise Exception(error_msg)

                    chef_id = chef_results[0]["id"]

                    # Créer ligne de devis Chef
                    ligne_chef = await self._create_ligne_devis(
                        prestation_id=prestation_id,
                        item_id=chef_id,
                        quantite=nb_chefs,
                        description=f"{nb_chefs} Chef(s) Pizzaïolo"
                    )
                    ligne_ids.append(ligne_chef)
                    logger.info(f"✅ Ligne devis RH Chef créée: {nb_chefs} chef(s)")

                # Récupérer Assistant
                if nb_assistants > 0:
                    response_assistant = await client.post(
                        catalogue_url,
                        headers=self.headers,
                        json=payload_assistant
                    )
                    response_assistant.raise_for_status()
                    assistant_results = response_assistant.json().get("results", [])

                    if not assistant_results:
                        error_msg = (
                            "Configuration error: Item 'Assistant' not found in Catalogue. "
                            "Please ensure an item with 'Assistant' in the name and Type='RH' exists."
                        )
                        logger.error(error_msg)
                        raise Exception(error_msg)

                    assistant_id = assistant_results[0]["id"]

                    # Créer ligne de devis Assistant
                    ligne_assistant = await self._create_ligne_devis(
                        prestation_id=prestation_id,
                        item_id=assistant_id,
                        quantite=nb_assistants,
                        description=f"{nb_assistants} Assistant(s)"
                    )
                    ligne_ids.append(ligne_assistant)
                    logger.info(f"✅ Ligne devis RH Assistant créée: {nb_assistants} assistant(s)")

            return ligne_ids

        except Exception as e:
            logger.error(f"❌ Error creating lignes devis RH: {str(e)}")
            raise

    async def _create_ligne_devis(
        self,
        prestation_id: str,
        item_id: str,
        quantite: int,
        description: str
    ) -> str:
        """
        Méthode helper pour créer une ligne de devis

        Returns:
            ID de la ligne de devis créée
        """
        url = f"{self.base_url}/pages"

        payload = {
            "parent": {"database_id": self.lignes_devis_db_id},
            "properties": {
                "Description": {
                    "title": [{"text": {"content": description}}]
                },
                "Prestation": {
                    "relation": [{"id": prestation_id}]
                },
                "Item du catalogue": {
                    "relation": [{"id": item_id}]
                },
                "Quantité": {
                    "number": quantite
                }
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            ligne_id = response.json()["id"]

        return ligne_id

    # ============================================
    # MÉTHODES POUR L'ÉDITEUR DE DEVIS
    # ============================================

    async def get_all_catalogue_items(self) -> List[Dict[str, Any]]:
        """
        Récupère tous les items du catalogue (Produit catalogue + RH)

        Returns:
            Liste de dictionnaires avec: id, nom, prix, type
        """
        url = f"{self.base_url}/databases/{self.catalogue_db_id}/query"

        # Pas de filtre - on veut tous les items
        payload = {}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                data = response.json()

                items = []
                for page in data.get("results", []):
                    props = page.get("properties", {})

                    # Extract nom
                    nom = ""
                    if "Nom" in props:
                        title_array = props["Nom"].get("title", [])
                        if title_array:
                            nom = title_array[0]["text"]["content"]

                    # Extract prix
                    prix = props.get("Prix", {}).get("number", 0)

                    # Extract type
                    type_item = ""
                    if "Type" in props:
                        select = props["Type"].get("select")
                        if select:
                            type_item = select.get("name", "")

                    items.append({
                        "id": page["id"],
                        "nom": nom,
                        "prix": prix if prix is not None else 0,
                        "type": type_item
                    })

                logger.info(f"Retrieved {len(items)} catalogue items")
                return items

        except Exception as e:
            logger.error(f"Error retrieving catalogue items: {str(e)}")
            raise

    async def get_devis_lines_for_editor(self, prestation_id: str) -> List[Dict[str, Any]]:
        """
        Récupère les lignes de devis pour l'éditeur (avec IDs)

        Args:
            prestation_id: ID de la prestation

        Returns:
            Liste avec: id, item_id, item_name, description, quantite, prix_unitaire
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

                    # Extract description
                    description = ""
                    if "Description" in props:
                        title_array = props["Description"].get("title", [])
                        if title_array:
                            description = title_array[0]["text"]["content"]

                    # Extract item_id from relation
                    item_id = None
                    item_name = ""
                    if "Item du catalogue" in props and props["Item du catalogue"].get("relation"):
                        item_id = props["Item du catalogue"]["relation"][0]["id"]
                        # Fetch catalogue item name
                        item_data = await self._get_page(item_id)
                        if item_data and "Nom" in item_data["properties"]:
                            title_array = item_data["properties"]["Nom"].get("title", [])
                            if title_array:
                                item_name = title_array[0]["text"]["content"]

                    # Extract quantite
                    quantite = props.get("Quantité", {}).get("number", 0)

                    # Extract prix unitaire (rollup)
                    prix_unitaire = 0
                    if "Prix unitaire" in props:
                        rollup = props["Prix unitaire"].get("rollup", {})
                        if rollup.get("type") == "number":
                            prix_unitaire = rollup.get("number", 0)

                    lines.append({
                        "id": line["id"],
                        "item_id": item_id,
                        "item_name": item_name,
                        "description": description,
                        "quantite": quantite if quantite is not None else 0,
                        "prix_unitaire": prix_unitaire if prix_unitaire is not None else 0
                    })

                logger.info(f"Retrieved {len(lines)} devis lines for editor")
                return lines

        except Exception as e:
            logger.error(f"Error retrieving devis lines for editor: {str(e)}")
            raise

    async def update_ligne_devis(self, ligne_id: str, quantite: int) -> None:
        """
        Met à jour la quantité d'une ligne de devis

        Args:
            ligne_id: ID de la ligne de devis
            quantite: Nouvelle quantité
        """
        url = f"{self.base_url}/pages/{ligne_id}"

        payload = {
            "properties": {
                "Quantité": {
                    "number": quantite
                }
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(url, headers=self.headers, json=payload)
                response.raise_for_status()
                logger.info(f"Updated ligne {ligne_id} with quantite={quantite}")

        except Exception as e:
            logger.error(f"Error updating ligne devis: {str(e)}")
            raise

    async def delete_ligne_devis(self, ligne_id: str) -> None:
        """
        Archive (supprime) une ligne de devis

        Args:
            ligne_id: ID de la ligne de devis
        """
        url = f"{self.base_url}/pages/{ligne_id}"

        payload = {
            "archived": True
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(url, headers=self.headers, json=payload)
                response.raise_for_status()
                logger.info(f"Deleted (archived) ligne {ligne_id}")

        except Exception as e:
            logger.error(f"Error deleting ligne devis: {str(e)}")
            raise

    async def create_ligne_devis_from_editor(
        self,
        prestation_id: str,
        item_id: str,
        quantite: int
    ) -> str:
        """
        Crée une nouvelle ligne de devis depuis l'éditeur

        Args:
            prestation_id: ID de la prestation
            item_id: ID de l'item du catalogue
            quantite: Quantité

        Returns:
            ID de la ligne créée
        """
        # Récupérer le nom de l'item pour la description
        item_data = await self._get_page(item_id)
        if not item_data:
            raise ValueError(f"Catalogue item {item_id} not found")

        item_name = ""
        if "Nom" in item_data["properties"]:
            title_array = item_data["properties"]["Nom"].get("title", [])
            if title_array:
                item_name = title_array[0]["text"]["content"]

        # Créer la ligne avec la description = nom de l'item
        ligne_id = await self._create_ligne_devis(
            prestation_id=prestation_id,
            item_id=item_id,
            quantite=quantite,
            description=item_name
        )

        logger.info(f"Created ligne from editor: {item_name} x{quantite}")
        return ligne_id

    async def get_active_prestations(self) -> List[Dict[str, Any]]:
        """
        Récupère les prestations actives (statut "A confirmer" ou "Confirmée", date future/aujourd'hui)

        Returns:
            Liste des prestations avec: id, nom_prestation, date, statut, client_name, pax
        """
        from datetime import datetime

        url = f"{self.base_url}/databases/{self.prestations_db_id}/query"

        # Obtenir la date d'aujourd'hui au format ISO
        today = datetime.now().strftime("%Y-%m-%d")

        payload = {
            "filter": {
                "and": [
                    {
                        "property": "Date",
                        "date": {
                            "on_or_after": today
                        }
                    },
                    {
                        "or": [
                            {
                                "property": "Statut",
                                "select": {
                                    "equals": "A confirmer"
                                }
                            },
                            {
                                "property": "Statut",
                                "select": {
                                    "equals": "Confirmée"
                                }
                            }
                        ]
                    }
                ]
            },
            "sorts": [
                {
                    "property": "Date",
                    "direction": "ascending"
                }
            ]
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                data = response.json()

                prestations = []
                for page in data.get("results", []):
                    props = page.get("properties", {})

                    # Extract nom prestation
                    nom_prestation = ""
                    if "Nom prestation" in props:
                        title_array = props["Nom prestation"].get("title", [])
                        if title_array:
                            nom_prestation = title_array[0]["text"]["content"]

                    # Extract date
                    date_str = ""
                    if "Date" in props and props["Date"].get("date"):
                        date_str = props["Date"]["date"].get("start", "")

                    # Extract statut
                    statut = ""
                    if "Statut" in props and props["Statut"].get("select"):
                        statut = props["Statut"]["select"].get("name", "")

                    # Extract PAX
                    pax = props.get("PAX", {}).get("number", 0)

                    # Extract client name from relation
                    client_name = ""
                    if "Client" in props and props["Client"].get("relation"):
                        client_id = props["Client"]["relation"][0]["id"]
                        client_data = await self._get_page(client_id)
                        if client_data and "Nom complet" in client_data["properties"]:
                            title_array = client_data["properties"]["Nom complet"].get("title", [])
                            if title_array:
                                client_name = title_array[0]["text"]["content"]

                    prestations.append({
                        "id": page["id"],
                        "nom_prestation": nom_prestation,
                        "date": date_str,
                        "statut": statut,
                        "client_name": client_name,
                        "pax": pax if pax is not None else 0
                    })

                logger.info(f"Retrieved {len(prestations)} active prestations")
                return prestations

        except Exception as e:
            logger.error(f"Error retrieving active prestations: {str(e)}")
            raise
