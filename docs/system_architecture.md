# System Architecture

```mermaid
flowchart LR
    User((Usuario))
    Browser["Navegador Web\nHTML + CSS + JS"]

    subgraph Frontend [Frontend]
        Templates[["Plantillas Jinja2\nweb/templates"]]
        StaticAssets[["Recursos Estáticos\nweb/static"]]
        APIClient[["BugTrackerAPI\nweb/static/api.js"]]
        Utils[["Utilidades UI\nweb/static/utils.js"]]
    end

    subgraph Backend [Backend FastAPI]
        FastAPIApp["Aplicación FastAPI\napp.py"]
        Routers["Routers REST\nweb/api/*.py"]
        Schemas[("Esquemas Pydantic\ncore/schemas.py")]
        Repos[["Repositorios de Datos\ncore/repos/*"]]
        Automation[["Automatizaciones\ncore/automation/*"]]
    end

    subgraph Persistence [Persistencia]
        DBSess[("Sesión SQLAlchemy\ncore/db.py")] 
        Models[("Modelos ORM\ncore/models.py")]
        Database[("Base de Datos\n(engine configurado)")]
    end

    User -->|Interacción| Browser
    Browser -->|Solicita vistas| FastAPIApp
    FastAPIApp --> Templates
    FastAPIApp --> StaticAssets
    Templates --> Browser
    StaticAssets --> Browser

    Browser -->|Fetch API (REST)| APIClient
    APIClient -->|peticiones HTTP| Routers
    Routers -->|validación| Schemas
    Routers -->|opera| Repos
    Repos -->|usa| Automation
    Repos -->|transacciones| DBSess
    DBSess --> Models
    Models --> Database
    Database --> DBSess

    Automation -->|sugerencias/etiquetas| Repos
    Schemas -->|serializa respuestas| Routers
    Routers -->|respuestas JSON| Browser
```

Este diagrama muestra el flujo de interacción entre el usuario final, el frontend basado en plantillas y recursos estáticos, el backend FastAPI que expone rutas HTML y REST, y la capa de persistencia gestionada mediante SQLAlchemy.
