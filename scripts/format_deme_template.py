#!/usr/bin/env python3
"""
Script standalone pour formater le template master Google Sheets DEVIS

Ce script formate le template MASTER avec le design du PDF ROSSETTI.
Il doit être exécuté UNE SEULE FOIS pour formater le template.
Après, toutes les copies du template auront automatiquement le bon formatage.

Usage:
    python scripts/format_deme_template.py

Variables d'environnement requises:
    - GOOGLE_DRIVE_CREDENTIALS: Credentials JSON du service account
    - GOOGLE_DRIVE_TEMPLATE_FILE_ID: ID du template master à formater
"""

import asyncio
import os
import sys
import json
import httpx
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def get_access_token(credentials_str: str) -> str:
    """Get OAuth2 access token from service account credentials"""
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request

        # Parse credentials with same logic as GoogleSheetsClient
        try:
            credentials_dict = json.loads(credentials_str)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse GOOGLE_DRIVE_CREDENTIALS directly: {e}")
            # Try fixing common issues: real newlines in private key
            try:
                fixed_str = credentials_str.replace('\r\n', '\\n').replace('\n', '\\n').replace('\r', '\\n')
                credentials_dict = json.loads(fixed_str)
                logger.info("Successfully parsed GOOGLE_DRIVE_CREDENTIALS after fixing newlines")
            except Exception as e2:
                logger.error(f"Failed to parse GOOGLE_DRIVE_CREDENTIALS even after fixing: {e2}")
                raise Exception(f"Invalid GOOGLE_DRIVE_CREDENTIALS format: {e2}")

        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=[
                'https://www.googleapis.com/auth/drive',
                'https://www.googleapis.com/auth/spreadsheets'
            ]
        )

        credentials.refresh(Request())
        logger.info("✓ Access token obtained")
        return credentials.token

    except Exception as e:
        logger.error(f"✗ Error getting access token: {str(e)}")
        raise


async def get_sheet_id(spreadsheet_id: str, sheet_name: str, token: str) -> int:
    """Get the sheet ID (gid) for a given sheet name"""
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            # Find the sheet with matching name
            for sheet in data.get("sheets", []):
                if sheet["properties"]["title"] == sheet_name:
                    sheet_id = sheet["properties"]["sheetId"]
                    logger.info(f"✓ Found sheet ID for '{sheet_name}': {sheet_id}")
                    return sheet_id

            # Default to 1 if not found (assuming DATA=0, DEVIS=1)
            logger.warning(f"Sheet '{sheet_name}' not found, defaulting to ID 1")
            return 1

    except Exception as e:
        logger.error(f"Error getting sheet ID: {str(e)}")
        return 1


async def format_devis_template(spreadsheet_id: str, token: str) -> bool:
    """
    Apply ROSSETTI PDF formatting to the DEVIS tab

    Design based on PDF DEVIS ROSSETTI - 24052025.pdf:
    - Maroon/terracotta header (#7B3F2C) with DéMé branding
    - Beige description section (#F5E6D3)
    - Table with maroon header and alternating white/light gray rows
    - Maroon TOTAL TTC row with white text
    - Terms and conditions footer
    """
    logger.info("Applying ROSSETTI PDF formatting to DEVIS tab...")

    url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}:batchUpdate"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Get sheet ID for DEVIS tab
    sheet_id = await get_sheet_id(spreadsheet_id, "DEVIS", token)

    requests = []

    # COLOR PALETTE (from ROSSETTI PDF)
    # Maroon/Terracotta: RGB(123, 63, 44) = #7B3F2C
    maroon_bg = {"red": 0.482, "green": 0.247, "blue": 0.173}
    # Beige/Cream: RGB(245, 230, 211) = #F5E6D3
    beige_bg = {"red": 0.961, "green": 0.902, "blue": 0.827}
    # Light gray for alternating rows
    light_gray = {"red": 0.97, "green": 0.97, "blue": 0.97}
    # White
    white = {"red": 1.0, "green": 1.0, "blue": 1.0}

    # ========== SECTION 1: HEADER (rows 1-5) - Maroon background ==========
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 0,
                "endRowIndex": 5,
                "startColumnIndex": 0,
                "endColumnIndex": 7
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": maroon_bg,
                    "textFormat": {
                        "foregroundColor": white,
                        "fontSize": 10,
                        "bold": False,
                        "fontFamily": "Arial"
                    },
                    "verticalAlignment": "TOP",
                    "wrapStrategy": "WRAP"
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,verticalAlignment,wrapStrategy)"
        }
    })

    # ========== SECTION 2: DESCRIPTION AREA (rows 6-9) - Beige background ==========
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 5,
                "endRowIndex": 9,
                "startColumnIndex": 0,
                "endColumnIndex": 7
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": beige_bg,
                    "textFormat": {
                        "foregroundColor": {"red": 0.0, "green": 0.0, "blue": 0.0},
                        "fontSize": 11,
                        "fontFamily": "Arial"
                    },
                    "verticalAlignment": "MIDDLE",
                    "wrapStrategy": "WRAP"
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,verticalAlignment,wrapStrategy)"
        }
    })

    # Row 6 (Description:) - Bold
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 5,
                "endRowIndex": 6,
                "startColumnIndex": 0,
                "endColumnIndex": 4
            },
            "cell": {
                "userEnteredFormat": {
                    "textFormat": {
                        "bold": True,
                        "fontSize": 12
                    }
                }
            },
            "fields": "userEnteredFormat.textFormat"
        }
    })

    # "À L'ATTENTION DE" section (right side, rows 6)
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 5,
                "endRowIndex": 6,
                "startColumnIndex": 4,
                "endColumnIndex": 7
            },
            "cell": {
                "userEnteredFormat": {
                    "textFormat": {
                        "bold": True,
                        "fontSize": 10
                    },
                    "horizontalAlignment": "RIGHT"
                }
            },
            "fields": "userEnteredFormat(textFormat,horizontalAlignment)"
        }
    })

    # Client name (row 7, right side)
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 6,
                "endRowIndex": 7,
                "startColumnIndex": 4,
                "endColumnIndex": 7
            },
            "cell": {
                "userEnteredFormat": {
                    "textFormat": {
                        "fontSize": 14,
                        "bold": True
                    },
                    "horizontalAlignment": "RIGHT"
                }
            },
            "fields": "userEnteredFormat(textFormat,horizontalAlignment)"
        }
    })

    # ========== SECTION 3: TABLE HEADER (row 10) - Maroon background ==========
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 9,
                "endRowIndex": 10,
                "startColumnIndex": 0,
                "endColumnIndex": 7
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": maroon_bg,
                    "textFormat": {
                        "foregroundColor": white,
                        "fontSize": 11,
                        "bold": True,
                        "fontFamily": "Arial"
                    },
                    "horizontalAlignment": "CENTER",
                    "verticalAlignment": "MIDDLE",
                    "borders": {
                        "top": {"style": "SOLID", "width": 2, "color": maroon_bg},
                        "bottom": {"style": "SOLID", "width": 2, "color": maroon_bg},
                        "left": {"style": "SOLID", "width": 1, "color": maroon_bg},
                        "right": {"style": "SOLID", "width": 1, "color": maroon_bg}
                    }
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,borders)"
        }
    })

    # ========== SECTION 4: TABLE DATA ROWS (11-22) - Alternating white/gray ==========
    # All data rows: add borders
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 10,
                "endRowIndex": 22,
                "startColumnIndex": 0,
                "endColumnIndex": 7
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": white,
                    "textFormat": {
                        "foregroundColor": {"red": 0.0, "green": 0.0, "blue": 0.0},
                        "fontSize": 10,
                        "fontFamily": "Arial"
                    },
                    "verticalAlignment": "TOP",
                    "wrapStrategy": "WRAP",
                    "borders": {
                        "top": {"style": "SOLID", "width": 1, "color": {"red": 0.85, "green": 0.85, "blue": 0.85}},
                        "bottom": {"style": "SOLID", "width": 1, "color": {"red": 0.85, "green": 0.85, "blue": 0.85}},
                        "left": {"style": "SOLID", "width": 1, "color": {"red": 0.85, "green": 0.85, "blue": 0.85}},
                        "right": {"style": "SOLID", "width": 1, "color": {"red": 0.85, "green": 0.85, "blue": 0.85}}
                    }
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,verticalAlignment,wrapStrategy,borders)"
        }
    })

    # Alternating gray rows (every other row)
    for row in range(11, 22, 2):
        requests.append({
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": row,
                    "endRowIndex": row + 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": 7
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": light_gray
                    }
                },
                "fields": "userEnteredFormat.backgroundColor"
            }
        })

    # Column A (Description): Left-aligned, bold
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 10,
                "endRowIndex": 22,
                "startColumnIndex": 0,
                "endColumnIndex": 1
            },
            "cell": {
                "userEnteredFormat": {
                    "horizontalAlignment": "LEFT",
                    "textFormat": {
                        "bold": True
                    }
                }
            },
            "fields": "userEnteredFormat(horizontalAlignment,textFormat)"
        }
    })

    # Column E: Prix - centered
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 10,
                "endRowIndex": 22,
                "startColumnIndex": 4,
                "endColumnIndex": 5
            },
            "cell": {
                "userEnteredFormat": {
                    "numberFormat": {
                        "type": "NUMBER",
                        "pattern": "#,##0"
                    },
                    "horizontalAlignment": "CENTER"
                }
            },
            "fields": "userEnteredFormat(numberFormat,horizontalAlignment)"
        }
    })

    # Column F: Quantité - centered
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 10,
                "endRowIndex": 22,
                "startColumnIndex": 5,
                "endColumnIndex": 6
            },
            "cell": {
                "userEnteredFormat": {
                    "numberFormat": {
                        "type": "NUMBER",
                        "pattern": "00"
                    },
                    "horizontalAlignment": "CENTER"
                }
            },
            "fields": "userEnteredFormat(numberFormat,horizontalAlignment)"
        }
    })

    # Column G: Total - centered
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 10,
                "endRowIndex": 22,
                "startColumnIndex": 6,
                "endColumnIndex": 7
            },
            "cell": {
                "userEnteredFormat": {
                    "numberFormat": {
                        "type": "NUMBER",
                        "pattern": "#,##0"
                    },
                    "horizontalAlignment": "CENTER"
                }
            },
            "fields": "userEnteredFormat(numberFormat,horizontalAlignment)"
        }
    })

    # ========== SECTION 5: TOTALS (rows 25-27) ==========
    # Row 25: Sous total HT
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 24,
                "endRowIndex": 25,
                "startColumnIndex": 0,
                "endColumnIndex": 7
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": white,
                    "textFormat": {
                        "fontSize": 12,
                        "bold": True,
                        "foregroundColor": {"red": 0.0, "green": 0.0, "blue": 0.0}
                    },
                    "horizontalAlignment": "RIGHT"
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
        }
    })

    # Row 26: TVA
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 25,
                "endRowIndex": 26,
                "startColumnIndex": 0,
                "endColumnIndex": 7
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": white,
                    "textFormat": {
                        "fontSize": 12,
                        "bold": True,
                        "foregroundColor": {"red": 0.0, "green": 0.0, "blue": 0.0}
                    },
                    "horizontalAlignment": "RIGHT"
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
        }
    })

    # Row 27: TOTAL TTC - MAROON background with WHITE text
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 26,
                "endRowIndex": 27,
                "startColumnIndex": 0,
                "endColumnIndex": 7
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": maroon_bg,
                    "textFormat": {
                        "foregroundColor": white,
                        "bold": True,
                        "fontSize": 14,
                        "fontFamily": "Arial"
                    },
                    "horizontalAlignment": "RIGHT",
                    "verticalAlignment": "MIDDLE"
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
        }
    })

    # ========== SECTION 6: TERMS AND CONDITIONS (rows 29-35) ==========
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 28,
                "endRowIndex": 35,
                "startColumnIndex": 0,
                "endColumnIndex": 7
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": white,
                    "textFormat": {
                        "fontSize": 9,
                        "foregroundColor": {"red": 0.2, "green": 0.2, "blue": 0.2}
                    },
                    "verticalAlignment": "TOP",
                    "wrapStrategy": "WRAP"
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,verticalAlignment,wrapStrategy)"
        }
    })

    # Footer section (row 36+) - Maroon background with bank details
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 35,
                "endRowIndex": 37,
                "startColumnIndex": 0,
                "endColumnIndex": 7
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": maroon_bg,
                    "textFormat": {
                        "foregroundColor": white,
                        "fontSize": 9,
                        "bold": True
                    },
                    "verticalAlignment": "MIDDLE",
                    "wrapStrategy": "WRAP"
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,verticalAlignment,wrapStrategy)"
        }
    })

    # ========== SECTION 7: COLUMN WIDTHS ==========
    column_widths = [
        {"column": 0, "width": 450},  # A: Description
        {"column": 1, "width": 80},
        {"column": 2, "width": 80},
        {"column": 3, "width": 80},
        {"column": 4, "width": 100},  # E: Prix
        {"column": 5, "width": 100},  # F: Quantité
        {"column": 6, "width": 100},  # G: Total
    ]

    for col_config in column_widths:
        requests.append({
            "updateDimensionProperties": {
                "range": {
                    "sheetId": sheet_id,
                    "dimension": "COLUMNS",
                    "startIndex": col_config["column"],
                    "endIndex": col_config["column"] + 1
                },
                "properties": {
                    "pixelSize": col_config["width"]
                },
                "fields": "pixelSize"
            }
        })

    # ========== SECTION 8: ROW HEIGHTS ==========
    # Header rows (1-5)
    requests.append({
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "ROWS",
                "startIndex": 0,
                "endIndex": 5
            },
            "properties": {
                "pixelSize": 25
            },
            "fields": "pixelSize"
        }
    })

    # Description rows (6-9)
    requests.append({
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "ROWS",
                "startIndex": 5,
                "endIndex": 9
            },
            "properties": {
                "pixelSize": 30
            },
            "fields": "pixelSize"
        }
    })

    # Table header row (10)
    requests.append({
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "ROWS",
                "startIndex": 9,
                "endIndex": 10
            },
            "properties": {
                "pixelSize": 35
            },
            "fields": "pixelSize"
        }
    })

    # Total TTC row (27)
    requests.append({
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "ROWS",
                "startIndex": 26,
                "endIndex": 27
            },
            "properties": {
                "pixelSize": 40
            },
            "fields": "pixelSize"
        }
    })

    # Execute all formatting requests
    payload = {"requests": requests}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()

            logger.info("✓ DEVIS tab formatting applied successfully (ROSSETTI PDF style)")
            return True

    except Exception as e:
        logger.error(f"✗ Error formatting DEVIS tab: {str(e)}")
        if hasattr(e, 'response'):
            logger.error(f"Response: {e.response.text}")
        return False


async def main():
    """Main entry point"""
    print("=" * 70)
    print("  DéMé Traiteur - Template Formatter")
    print("  Format master template with ROSSETTI PDF design")
    print("=" * 70)
    print()

    # Check environment variables
    credentials_json = os.getenv("GOOGLE_DRIVE_CREDENTIALS")
    template_id = os.getenv("GOOGLE_DRIVE_TEMPLATE_FILE_ID")

    if not credentials_json:
        logger.error("✗ Missing GOOGLE_DRIVE_CREDENTIALS environment variable")
        sys.exit(1)

    if not template_id:
        logger.error("✗ Missing GOOGLE_DRIVE_TEMPLATE_FILE_ID environment variable")
        sys.exit(1)

    print(f"Template to format: {template_id}")
    print()
    print("⚠️  WARNING: This will modify the master template's formatting")
    print("   All future copies will inherit this formatting")
    print()

    response = input("Do you want to proceed? (yes/no): ").strip().lower()

    if response not in ["yes", "y", "oui", "o"]:
        logger.info("Operation cancelled by user")
        sys.exit(0)

    print()
    logger.info("Starting template formatting...")

    try:
        # Get access token
        token = await get_access_token(credentials_json)

        # Format template
        success = await format_devis_template(template_id, token)

        if success:
            print()
            print("=" * 70)
            print("✓ SUCCESS!")
            print("=" * 70)
            print()
            print(f"The template {template_id} has been formatted.")
            print("All future copies will have the ROSSETTI PDF design.")
            sys.exit(0)
        else:
            print()
            print("=" * 70)
            print("✗ FAILED")
            print("=" * 70)
            sys.exit(1)

    except Exception as e:
        logger.error(f"✗ Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
