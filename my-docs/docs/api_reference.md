# **API Reference - IPNI FastAPI Project**

## **Endpoints**

### 1. Name
- **GET /name/** → List names
- **POST /name/** → Create name  `{rank, scientheficname, authorship, status, referenceid, link, id}`
- **GET /name/{id}** → Get name details
- **DELETE /name/{id}** → Delete name
- **GET /name/{id}/metadata** → Get name metadata

### 2. Reference
- **GET /reference/** → List references
- **POST /reference/** → Create reference `{title, issued, volume, id}`
- **GET /reference/{id}** → Get reference details
- **DELETE /reference/{id}** → Delete reference

### 3. Taxon
- **GET /taxon/** → List taxa
- **POST /taxon/** → Create taxon `{nameid, provisional, family, id}`
- **GET /taxon/{id}** → Get taxon details
- **DELETE /taxon/{id}** → Delete taxon

### 4. Name Relation
- **GET /name_relation/** → List name relations
- **POST /name_relation/** → Create name relation `{nameid, relatednameid, relation_type}`

### 5. Type Material
- **GET /type_material/** → List type materials
- **POST /type_material/** → Create type material `{nameid, status, institutioncode, collector, locality}`
- **GET /type_material/{id}** → Get type material details

### 6. Database Management
- **POST /database/import/** → Import data `{}`

### Response Format
Success:

    ```json
    {"status": "success", 
    "data": {...}, 
    "message": "optional message"}
    ```
Error:

    ```json
    {"status": "error", 
    "message": "error details"}
    ```

