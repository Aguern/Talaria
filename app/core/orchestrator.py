# Fichier: app/core/orchestrator.py

import json
import uuid
import importlib
from pathlib import Path
from typing import List, Dict, Any, Optional
import structlog
from pydantic import ValidationError

from .schemas import RecipeManifest, InputParameter
# Import dynamique pour éviter les imports circulaires
# from .tasks import execute_recipe_task

log = structlog.get_logger()

class OrchestratorService:
    """
    Service d'orchestration générique pour découvrir et exécuter des recettes.

    Principe :
    - Scanne les dossiers de packs pour découvrir les recettes via leurs manifests
    - Valide les inputs par rapport aux manifests
    - Lance les tâches Celery de manière asynchrone
    - Ne fait jamais l'exécution directement (délégation à Celery)
    """

    def __init__(self):
        self.packs_directory = Path(__file__).parent.parent / "packs"
        log.info("OrchestratorService initialisé", packs_dir=str(self.packs_directory))

    async def discover_recipes(self) -> List[RecipeManifest]:
        """
        Scanne tous les sous-dossiers de app/packs/, lit les manifest.json,
        les valide avec le schéma Pydantic, et retourne une liste d'objets RecipeManifest.
        """
        recipes = []

        if not self.packs_directory.exists():
            log.warning("Répertoire des packs introuvable", path=str(self.packs_directory))
            return recipes

        # Parcourir tous les sous-dossiers du répertoire packs
        for pack_dir in self.packs_directory.iterdir():
            if pack_dir.is_dir() and not pack_dir.name.startswith('.'):
                manifest_path = pack_dir / "manifest.json"

                if manifest_path.exists():
                    try:
                        # Charger et valider le manifest
                        with open(manifest_path, 'r', encoding='utf-8') as f:
                            manifest_data = json.load(f)

                        # Validation avec Pydantic
                        manifest = RecipeManifest(**manifest_data)
                        recipes.append(manifest)

                        log.info("Recette découverte",
                                recipe_id=manifest.id,
                                recipe_name=manifest.name,
                                pack_dir=pack_dir.name)

                    except (json.JSONDecodeError, ValidationError) as e:
                        log.error("Erreur lors du chargement du manifest",
                                 pack_dir=pack_dir.name,
                                 error=str(e))
                    except Exception as e:
                        log.error("Erreur inattendue lors de la découverte",
                                 pack_dir=pack_dir.name,
                                 error=str(e))
                else:
                    log.warning("Manifest manquant pour le pack", pack_dir=pack_dir.name)

        log.info("Découverte terminée", nombre_recettes=len(recipes))
        return recipes

    async def get_recipe_manifest(self, recipe_id: str) -> Optional[RecipeManifest]:
        """
        Récupère le manifest d'une recette spécifique par son ID.
        """
        recipes = await self.discover_recipes()
        for recipe in recipes:
            if recipe.id == recipe_id:
                return recipe
        return None

    async def validate_inputs(self, manifest: RecipeManifest, inputs: Dict[str, Any]) -> bool:
        """
        Valide que les inputs fournis correspondent au schéma défini dans le manifest.

        Args:
            manifest: Le manifest de la recette
            inputs: Les données d'entrée fournies

        Returns:
            True si valide, False sinon
        """
        try:
            # Vérifier que tous les inputs requis sont présents
            for input_param in manifest.inputs:
                if input_param.required and input_param.name not in inputs:
                    log.error("Input requis manquant",
                             input_name=input_param.name,
                             recipe_id=manifest.id)
                    return False

                # Vérification basique des types
                if input_param.name in inputs:
                    value = inputs[input_param.name]

                    # Validation selon le type
                    if input_param.type == "file" and input_param.multiple:
                        if not isinstance(value, list):
                            log.error("Input file multiple doit être une liste",
                                     input_name=input_param.name,
                                     actual_type=type(value).__name__)
                            return False
                    elif input_param.type == "text":
                        if not isinstance(value, str):
                            log.error("Input text doit être une chaîne",
                                     input_name=input_param.name,
                                     actual_type=type(value).__name__)
                            return False
                    elif input_param.type == "number":
                        if not isinstance(value, (int, float)):
                            log.error("Input number doit être un nombre",
                                     input_name=input_param.name,
                                     actual_type=type(value).__name__)
                            return False
                    elif input_param.type == "boolean":
                        if not isinstance(value, bool):
                            log.error("Input boolean doit être un booléen",
                                     input_name=input_param.name,
                                     actual_type=type(value).__name__)
                            return False

            log.info("Validation des inputs réussie", recipe_id=manifest.id)
            return True

        except Exception as e:
            log.error("Erreur lors de la validation des inputs",
                     recipe_id=manifest.id,
                     error=str(e))
            return False

    async def run_recipe(self, recipe_id: str, inputs: Dict[str, Any]) -> str:
        """
        Lance l'exécution d'une recette de manière asynchrone.

        Workflow:
        1. Charge le manifest de la recette
        2. Valide que les inputs correspondent au schéma
        3. Lance execute_recipe_task.delay() sur Celery
        4. Retourne immédiatement le task_id (pas d'attente)

        Args:
            recipe_id: L'identifiant de la recette à exécuter
            inputs: Les données d'entrée pour la recette

        Returns:
            Le task_id de la tâche Celery lancée

        Raises:
            ValueError: Si la recette n'existe pas ou si les inputs sont invalides
        """
        # 1. Charger le manifest
        manifest = await self.get_recipe_manifest(recipe_id)
        if not manifest:
            error_msg = f"Recette '{recipe_id}' introuvable"
            log.error(error_msg)
            raise ValueError(error_msg)

        # 2. Valider les inputs
        if not await self.validate_inputs(manifest, inputs):
            error_msg = f"Inputs invalides pour la recette '{recipe_id}'"
            log.error(error_msg)
            raise ValueError(error_msg)

        # 3. Générer un task_id unique
        task_id = str(uuid.uuid4())

        # 4. Lancer la tâche Celery et retourner immédiatement
        log.info("Lancement de la tâche asynchrone",
                recipe_id=recipe_id,
                task_id=task_id,
                input_keys=list(inputs.keys()))

        # Délégation complète à Celery - pas d'attente
        # Import dynamique pour éviter les imports circulaires
        from .tasks import execute_recipe_task
        execute_recipe_task.delay(recipe_id, task_id, inputs)

        return task_id


# Instance singleton pour l'injection de dépendance
_orchestrator_instance = None

def get_orchestrator() -> OrchestratorService:
    """
    Factory function pour obtenir l'instance singleton de l'orchestrateur.
    Utilisée pour l'injection de dépendance FastAPI.
    """
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = OrchestratorService()
    return _orchestrator_instance