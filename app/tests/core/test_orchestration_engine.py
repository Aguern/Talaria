# Fichier: tests/core/test_orchestration_engine.py

import pytest
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app.core.orchestration_engine import OrchestrationEngine

@pytest.fixture
def engine() -> OrchestrationEngine:
    """Fournit une instance fraîche du moteur pour chaque test."""
    return OrchestrationEngine()

def test_engine_initialization(engine: OrchestrationEngine):
    """Teste que le moteur s'initialise correctement."""
    assert engine is not None
    assert isinstance(engine.registered_recipes, dict)
    assert len(engine.registered_recipes) == 0

def test_register_recipe(engine: OrchestrationEngine):
    """Teste l'enregistrement d'une recette factice."""
    mock_graph = "ceci est un faux graphe"
    engine.register_recipe("test_recipe", mock_graph)
    assert "test_recipe" in engine.registered_recipes
    assert engine.registered_recipes["test_recipe"] == mock_graph

@pytest.mark.asyncio
async def test_run_recipe_not_found(engine: OrchestrationEngine):
    """Teste que l'exécution d'une recette non enregistrée lève une erreur."""
    with pytest.raises(ValueError, match="Recipe 'unknown_recipe' is not registered."):
        await engine.run_recipe("unknown_recipe", {})

@pytest.mark.asyncio
async def test_run_recipe_success(engine: OrchestrationEngine):
    """Teste que l'exécution d'une recette enregistrée retourne un semblant de task_id."""
    engine.register_recipe("test_recipe", "fake_graph")
    task_id = await engine.run_recipe("test_recipe", {"input": "data"})
    assert isinstance(task_id, str)
    assert len(task_id) > 10 # Doit ressembler à un UUID