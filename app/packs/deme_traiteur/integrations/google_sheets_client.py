"""
Google Drive & Sheets API Client for DéMé Traiteur Pack

Handles:
- Copying the devis template from Google Drive
- Renaming the copied file
- Filling the Google Sheet with prestation data
"""

import os
import json
from json.decoder import JSONDecodeError
import httpx
from typing import Dict, Any, Optional, List
import logging
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)


class GoogleSheetsClient:
    """Client for Google Drive and Sheets API operations"""

    def __init__(self):
        credentials_str = os.getenv("GOOGLE_DRIVE_CREDENTIALS")
        if credentials_str:
            try:
                # Try direct parsing first
                self.credentials = json.loads(credentials_str)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse GOOGLE_DRIVE_CREDENTIALS directly: {e}")
                # Try fixing common issues: real newlines in private key
                try:
                    # Replace literal newlines with \n escape sequences
                    fixed_str = credentials_str.replace('\r\n', '\\n').replace('\n', '\\n').replace('\r', '\\n')
                    self.credentials = json.loads(fixed_str)
                    logger.info("Successfully parsed GOOGLE_DRIVE_CREDENTIALS after fixing newlines")
                except Exception as e2:
                    logger.error(f"Failed to parse GOOGLE_DRIVE_CREDENTIALS even after fixing: {e2}")
                    raise Exception(f"Invalid GOOGLE_DRIVE_CREDENTIALS format: {e2}")
        else:
            self.credentials = {}
        self.template_file_id = os.getenv("GOOGLE_DRIVE_TEMPLATE_FILE_ID")
        self.shared_folder_id = os.getenv("GOOGLE_DRIVE_SHARED_FOLDER_ID")
        self.access_token: Optional[str] = None

        # Pool configuration file path
        self.pool_file = Path(__file__).parent.parent / "template_pool.json"
        self._pool_lock = asyncio.Lock()

    async def _get_access_token(self) -> str:
        """
        Get OAuth2 access token using service account credentials

        Returns:
            Access token string
        """
        if self.access_token:
            return self.access_token

        try:
            from google.oauth2 import service_account
            from google.auth.transport.requests import Request

            credentials = service_account.Credentials.from_service_account_info(
                self.credentials,
                scopes=[
                    'https://www.googleapis.com/auth/drive',
                    'https://www.googleapis.com/auth/spreadsheets'
                ]
            )

            credentials.refresh(Request())
            self.access_token = credentials.token
            logger.info("Google Drive/Sheets access token obtained")
            return self.access_token

        except Exception as e:
            logger.error(f"Error getting access token: {str(e)}")
            raise

    async def _read_pool(self) -> Dict[str, List[str]]:
        """Read the template pool from JSON file, initialize if missing or corrupted"""
        try:
            logger.info(f"Reading pool file: {self.pool_file}")
            with open(self.pool_file, 'r') as f:
                pool = json.load(f)
                # Validate structure
                if not isinstance(pool, dict) or 'available' not in pool or 'in_use' not in pool:
                    logger.warning(f"Pool structure invalid: {pool}")
                    raise ValueError("Invalid pool structure")
                logger.info(f"Pool loaded successfully: {len(pool.get('available', []))} available, {len(pool.get('in_use', []))} in use")
                return pool
        except (FileNotFoundError, JSONDecodeError, ValueError) as e:
            logger.warning(f"Pool file missing or corrupted ({type(e).__name__}: {str(e)}), initializing empty pool")
            # Initialize with empty pool
            empty_pool = {"available": [], "in_use": []}
            try:
                await self._write_pool(empty_pool)
                logger.info("Empty pool file created successfully")
            except Exception as write_error:
                logger.error(f"Failed to write empty pool: {write_error}")
                raise
            return empty_pool

    async def _write_pool(self, pool: Dict[str, List[str]]):
        """Write the template pool to JSON file"""
        with open(self.pool_file, 'w') as f:
            json.dump(pool, f, indent=2)

    async def get_template_from_pool(self) -> str:
        """
        Get a template from the pool of pre-created templates

        This avoids the quota issue by using templates that already exist
        and belong to the user account.

        If the pool is empty, automatically reloads it with new templates.

        Returns:
            ID of a template from the pool

        Raises:
            Exception: If pool reload fails
        """
        async with self._pool_lock:
            # Read current pool state
            pool = await self._read_pool()

            # Auto-reload if pool is empty (e.g., on Render Free after restart)
            if not pool["available"]:
                logger.warning("Pool is empty, auto-reloading with 5 new templates...")
                try:
                    # Release lock temporarily for reload (it needs the lock internally)
                    pass  # We're already in the lock, reload_pool will wait
                except Exception as e:
                    logger.error(f"Failed to auto-reload pool: {str(e)}")
                    raise Exception(
                        "Pool de templates épuisé et impossible de recharger automatiquement. "
                        f"Erreur: {str(e)}"
                    )

            # Try again after potential reload
            if not pool["available"]:
                # Reload manually since we're in the lock
                await self._reload_pool_internal(pool, count=5)

            if not pool["available"]:
                raise Exception("Failed to reload pool - no templates available")

            # Get first available template
            template_id = pool["available"].pop(0)

            # Move to in_use
            pool["in_use"].append(template_id)

            # Save updated pool
            await self._write_pool(pool)

            logger.info(f"Template retrieved from pool: {template_id}")
            logger.info(f"Remaining templates in pool: {len(pool['available'])}")

            return template_id

    async def _get_user_access_token(self) -> str:
        """
        Get OAuth2 access token using user credentials (token.json)
        This is used for operations that require user permissions (like copying files)

        Returns:
            Access token string
        """
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            from pathlib import Path

            token_path = Path(__file__).parent.parent.parent.parent / "token.json"

            if not token_path.exists():
                logger.error(f"token.json not found at {token_path}")
                raise Exception("User credentials not found. Run setup_gmail.py first.")

            creds = Credentials.from_authorized_user_file(str(token_path))

            # Refresh token if expired
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                # Save refreshed token
                with open(str(token_path), 'w') as token_file:
                    token_file.write(creds.to_json())
                logger.info("User token refreshed and saved")

            return creds.token

        except Exception as e:
            logger.error(f"Error getting user access token: {str(e)}")
            raise

    async def copy_template_file(self, new_name: str) -> str:
        """
        Copy the master template file using user account credentials

        This uses the user's Google account (via token.json) instead of the service account
        because the Drive API copy operation requires user permissions.

        Args:
            new_name: Name for the new file

        Returns:
            ID of the newly created file

        Raises:
            Exception: If copy fails or quota is exceeded
        """
        token = await self._get_user_access_token()

        url = f"https://www.googleapis.com/drive/v3/files/{self.template_file_id}/copy"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        payload = {
            "name": new_name,
            "parents": [self.shared_folder_id]
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                    params={"fields": "id,name,webViewLink"}
                )
                response.raise_for_status()
                data = response.json()

                logger.info(f"Template copied successfully with user account: {new_name} (ID: {data['id']})")
                return data["id"]

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                # Check if it's a quota error
                try:
                    error_data = e.response.json()
                    error_str = str(error_data)
                    if "quotaExceeded" in error_str or "userRateLimitExceeded" in error_str:
                        logger.warning("Google Drive quota exceeded")
                        raise Exception("QuotaExceeded")
                except Exception:
                    pass

            # Not a quota error - log and raise
            logger.error(f"Error copying template (HTTP {e.response.status_code}): {str(e)}")
            if e.response.status_code == 403:
                logger.error("Permission denied. Check user account permissions.")
            raise
        except Exception as e:
            logger.error(f"Error copying template: {str(e)}")
            raise

    async def _reload_pool_internal(self, pool: Dict[str, List[str]], count: int = 10) -> Dict[str, Any]:
        """
        Internal method to reload pool (assumes lock is already held)

        Args:
            pool: The current pool dictionary
            count: Number of templates to create

        Returns:
            Dictionary with status and statistics
        """
        logger.info(f"Starting pool reload: creating {count} new templates")
        initial_available = len(pool["available"])

        created_ids = []
        failed = 0

        for i in range(count):
            try:
                # Generate unique name
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                template_name = f"Template_Devis_{timestamp}_{i+1}"

                # Copy template
                template_id = await self.copy_template_file(template_name)
                created_ids.append(template_id)

                # Add to pool
                pool["available"].append(template_id)

                logger.info(f"Created template {i+1}/{count}: {template_id}")

                # Small delay to avoid rate limiting
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"Failed to create template {i+1}/{count}: {str(e)}")
                failed += 1

        # Save updated pool
        if created_ids:
            await self._write_pool(pool)

        return {
            "success": len(created_ids) > 0,
            "created": len(created_ids),
            "failed": failed,
            "initial_available": initial_available,
            "final_available": len(pool["available"])
        }

    async def reload_pool(self, count: int = 10) -> Dict[str, Any]:
        """
        Reload the template pool by creating new copies

        This method copies the master template multiple times and adds them to the pool.
        It should be called periodically (via cron or admin endpoint) to keep the pool full.

        Args:
            count: Number of templates to create (default: 10)

        Returns:
            Dictionary with status and statistics
        """
        async with self._pool_lock:
            pool = await self._read_pool()
            result = await self._reload_pool_internal(pool, count)

            logger.info(f"Pool reload completed: {result}")
            return result

    async def get_template_with_fallback(self, devis_name: str) -> str:
        """
        Get a template from pool, or copy master template if pool is empty

        This method tries to use the pre-created pool first (fast), but falls back
        to copying the master template if the pool is exhausted. The copy operation
        includes retry logic with exponential backoff to handle Google Drive quotas.

        Args:
            devis_name: Name for the devis (used if copying template)

        Returns:
            ID of the template (from pool or newly copied)

        Raises:
            Exception: If copy fails after all retries
        """
        try:
            # Try pool first (fast path)
            return await self.get_template_from_pool()
        except Exception as pool_error:
            logger.warning(f"Pool exhausted, falling back to template copy: {str(pool_error)}")

            # Pool empty → copy master template with retry
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    logger.info(f"Copying template (attempt {attempt + 1}/{max_attempts})")
                    template_id = await self.copy_template_file(devis_name)
                    logger.info(f"Template copied successfully: {template_id}")
                    return template_id

                except Exception as copy_error:
                    if "QuotaExceeded" in str(copy_error) and attempt < max_attempts - 1:
                        # Exponential backoff: 60s, 120s, 180s
                        delay = 60 * (attempt + 1)
                        logger.warning(
                            f"Quota exceeded, retrying in {delay}s "
                            f"(attempt {attempt + 1}/{max_attempts})"
                        )
                        await asyncio.sleep(delay)
                    else:
                        # Last attempt or other error
                        logger.error(f"Failed to copy template after {attempt + 1} attempts")
                        raise Exception(
                            f"Impossible de créer le devis: {str(copy_error)}. "
                            "Le quota Google Drive a été dépassé. Veuillez réessayer dans quelques minutes."
                        )

    async def rename_file(self, file_id: str, new_name: str) -> Dict[str, str]:
        """
        Rename a Google Drive file

        Args:
            file_id: Google Drive file ID
            new_name: New name for the file

        Returns:
            Dictionary with 'id', 'name', and 'webViewLink'
        """
        token = await self._get_access_token()

        url = f"https://www.googleapis.com/drive/v3/files/{file_id}"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        payload = {
            "name": new_name
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    url,
                    headers=headers,
                    json=payload,
                    params={"fields": "id,name,webViewLink"}
                )
                response.raise_for_status()
                data = response.json()

                logger.info(f"File renamed to: {new_name}")
                return {
                    "id": data["id"],
                    "name": data["name"],
                    "webViewLink": data.get("webViewLink", "")
                }

        except Exception as e:
            logger.error(f"Error renaming file: {str(e)}")
            raise

    async def update_cells(
        self,
        spreadsheet_id: str,
        updates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Update specific cells in a Google Sheet

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            updates: List of dictionaries with keys 'range' and 'values'
                    Example: [
                        {"range": "A1", "values": [["Client Name"]]},
                        {"range": "A2:B2", "values": [["Value1", "Value2"]]}
                    ]

        Returns:
            Response data from the API
        """
        token = await self._get_access_token()

        url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values:batchUpdate"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Build the data array for batchUpdate
        data_array = []
        for update in updates:
            data_array.append({
                "range": update["range"],
                "values": update["values"]
            })

        payload = {
            "valueInputOption": "USER_ENTERED",
            "data": data_array
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()

                logger.info(f"Updated {len(updates)} ranges in spreadsheet")
                return data

        except Exception as e:
            logger.error(f"Error updating cells: {str(e)}")
            raise

    async def append_rows(
        self,
        spreadsheet_id: str,
        range_start: str,
        values: List[List[Any]]
    ) -> Dict[str, Any]:
        """
        Append rows to a Google Sheet

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            range_start: Starting cell (e.g., "B10")
            values: List of rows, where each row is a list of values
                   Example: [["Item 1", 2, 15.5, 31.0], ["Item 2", 1, 20.0, 20.0]]

        Returns:
            Response data from the API
        """
        token = await self._get_access_token()

        url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{range_start}:append"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        payload = {
            "values": values
        }

        params = {
            "valueInputOption": "USER_ENTERED"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload, params=params)
                response.raise_for_status()
                data = response.json()

                logger.info(f"Appended {len(values)} rows starting at {range_start}")
                return data

        except Exception as e:
            logger.error(f"Error appending rows: {str(e)}")
            raise

    def _format_date(self, date_str: str) -> str:
        """
        Format date from YYYY-MM-DD to DD/MM/YYYY

        Args:
            date_str: Date in format YYYY-MM-DD (e.g., "2025-11-25")

        Returns:
            Date in format DD/MM/YYYY (e.g., "25/11/2025")
        """
        if not date_str:
            return ""

        try:
            # Parse YYYY-MM-DD
            year, month, day = date_str.split('-')
            # Return DD/MM/YYYY with slashes
            return f"{day}/{month}/{year}"
        except Exception:
            return date_str

    def _format_phone(self, phone: str) -> str:
        """
        Format phone number with spaces every 2 digits and prefix with apostrophe
        to force Google Sheets to treat it as text

        Args:
            phone: Phone number (e.g., "0612345678")

        Returns:
            Formatted phone with apostrophe prefix (e.g., "'06 12 34 56 78")
        """
        logger.info(f"Formatting phone - Input: '{phone}'")

        if not phone:
            logger.warning("Phone is empty or None")
            return ""

        # Remove all spaces first
        phone = phone.replace(" ", "")

        # Add spaces every 2 digits
        formatted = " ".join([phone[i:i+2] for i in range(0, len(phone), 2)])

        # Prefix with apostrophe to force Google Sheets to treat as text
        formatted_with_prefix = f"'{formatted}"

        logger.info(f"Formatting phone - Output: '{formatted_with_prefix}'")
        return formatted_with_prefix

    def _format_pax(self, pax: int) -> str:
        """
        Format PAX with "personnes" suffix

        Args:
            pax: Number of people

        Returns:
            Formatted string (e.g., "40 personnes")
        """
        return f"{pax} personnes"

    async def format_cells(
        self,
        spreadsheet_id: str,
        cell_ranges: List[str],
        horizontal_alignment: str = "LEFT"
    ) -> Dict[str, Any]:
        """
        Format specific cells with text alignment

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            cell_ranges: List of cell ranges to format (e.g., ["Feuille 1!D4", "Feuille 1!D5"])
            horizontal_alignment: Alignment value ("LEFT", "CENTER", "RIGHT")

        Returns:
            Response data from the API
        """
        token = await self._get_access_token()

        url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}:batchUpdate"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Build requests for each cell range
        requests = []
        for cell_range in cell_ranges:
            # Parse range to get sheet name and cell reference
            # Format: "Feuille 1!D4"
            sheet_name, cell_ref = cell_range.split("!")

            # Convert cell reference to row/column indices (0-based)
            # D4 -> row=3, col=3
            col_letter = ''.join(filter(str.isalpha, cell_ref))
            row_num = int(''.join(filter(str.isdigit, cell_ref))) - 1
            col_num = ord(col_letter.upper()) - ord('A')

            requests.append({
                "repeatCell": {
                    "range": {
                        "sheetId": 0,  # First sheet
                        "startRowIndex": row_num,
                        "endRowIndex": row_num + 1,
                        "startColumnIndex": col_num,
                        "endColumnIndex": col_num + 1
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "horizontalAlignment": horizontal_alignment
                        }
                    },
                    "fields": "userEnteredFormat.horizontalAlignment"
                }
            })

        payload = {
            "requests": requests
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()

                logger.info(f"Formatted {len(cell_ranges)} cells with alignment {horizontal_alignment}")
                return data

        except Exception as e:
            logger.error(f"Error formatting cells: {str(e)}")
            raise

    async def fill_devis_sheet(
        self,
        spreadsheet_id: str,
        client_data: Dict[str, Any],
        prestation_data: Dict[str, Any],
        devis_lines: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Fill the devis Google Sheet with all data

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            client_data: Client information (nom_complet, email, telephone, adresse, ville)
            prestation_data: Prestation information (nom_prestation, date, pax, moment)
            devis_lines: List of devis lines with keys: item_name, description, quantity, prix_unitaire, total_ligne

        Returns:
            Summary of operations performed
        """
        # Generate devis title: "Devis n°YYYYMMDDPAX" (all numbers concatenated)
        date_str = prestation_data.get("date", "")
        pax = prestation_data.get("pax", 0)
        # Remove dashes from date and concatenate with PAX
        date_no_dashes = date_str.replace("-", "")
        devis_title = f"Devis n°{date_no_dashes}{pax}"

        # Prepare cell updates - using sheet name "Feuille 1"
        updates = [
            {"range": "Feuille 1!A1", "values": [[devis_title]]},
            {"range": "Feuille 1!D3", "values": [[client_data.get("nom_complet", "")]]},
            {"range": "Feuille 1!D4", "values": [[self._format_phone(client_data.get("telephone", ""))]]},
            {"range": "Feuille 1!D5", "values": [[self._format_date(prestation_data.get("date", ""))]]},
            {"range": "Feuille 1!D6", "values": [[self._format_pax(pax)]]},
        ]

        # Update general information
        await self.update_cells(spreadsheet_id, updates)

        # Prepare devis lines for explicit insertion at row 9
        # Format: [Item du catalogue (A), Description (B), Quantité (C), Prix unitaire (D), Total ligne (E)]
        lines_values = []
        for line in devis_lines:
            lines_values.append([
                line.get("item_name", ""),                  # A: Item du catalogue
                line.get("description", line.get("item_name", "")),  # B: Description (fallback to item_name if not provided)
                line.get("quantity", 0),                    # C: Quantité
                line.get("prix_unitaire", 0),               # D: Prix unitaire
                line.get("total_ligne", 0)                  # E: Total ligne
            ])

        # Insert devis lines at exactly row 9 using update_cells (not append_rows)
        if lines_values:
            # Calculate the range: A9 to E(9+n-1) where n is number of lines
            end_row = 9 + len(lines_values) - 1
            range_spec = f"Feuille 1!A9:E{end_row}"
            logger.info(f"Inserting {len(lines_values)} devis lines at {range_spec}")

            await self.update_cells(spreadsheet_id, [
                {"range": range_spec, "values": lines_values}
            ])

            # Add SUM formula in E14 for total
            sum_formula = f"=SUM(E9:E{end_row})"
            await self.update_cells(spreadsheet_id, [
                {"range": "Feuille 1!E14", "values": [[sum_formula]]}
            ])
            logger.info(f"Added SUM formula in E14: {sum_formula}")

        # Apply left alignment to phone (D4) and date (D5) cells
        await self.format_cells(
            spreadsheet_id=spreadsheet_id,
            cell_ranges=["Feuille 1!D4", "Feuille 1!D5"],
            horizontal_alignment="LEFT"
        )

        logger.info(f"Devis sheet filled successfully with {len(devis_lines)} lines")

        return {
            "spreadsheet_id": spreadsheet_id,
            "client_updated": True,
            "prestation_updated": True,
            "lines_added": len(devis_lines)
        }
