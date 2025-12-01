// ============================================================================
// StrideMatch Recommendation Graph - Neo4j Initialization Script
// ============================================================================
//
// This script creates the graph schema for the StrideMatch recommendation engine.
//
// Architecture:
//   - PostgreSQL → Product catalog (see schema.sql)
//   - MongoDB → User profiles (see mongodb_schemas.py)
//   - Neo4j → Recommendation graph (this file)
//
// Graph Purpose:
//   Enable graph-based recommendations using relationships between:
//   - Users and their biomechanical profiles
//   - Products and their technical specifications
//   - Purchase history, views, ratings
//   - Co-purchase patterns
//   - Biomechanical similarities
//
// Usage:
//   1. Via Neo4j Browser: Copy-paste this file
//   2. Via cypher-shell: cat neo4j_init.cypher | cypher-shell -u neo4j -p stridematch_neo4j
//   3. Via Docker mount: Already mounted in docker-compose.yml
//
// ============================================================================


// ============================================================================
// CONSTRAINTS - Ensure Uniqueness and Data Integrity
// ============================================================================

// User nodes (mapped from MongoDB users collection)
CREATE CONSTRAINT user_id_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.user_id IS UNIQUE;

// Product nodes (mapped from PostgreSQL stridematch_products table)
CREATE CONSTRAINT product_id_unique IF NOT EXISTS
FOR (p:Product) REQUIRE p.product_id IS UNIQUE;

// Brand nodes (mapped from PostgreSQL stridematch_brands table)
CREATE CONSTRAINT brand_id_unique IF NOT EXISTS
FOR (b:Brand) REQUIRE b.brand_id IS UNIQUE;

// BiomechanicalProfile nodes (from MongoDB biomechanics subdocument)
CREATE CONSTRAINT biomech_profile_id_unique IF NOT EXISTS
FOR (bp:BiomechanicalProfile) REQUIRE bp.profile_id IS UNIQUE;

// ProductCategory nodes (for hierarchical filtering)
CREATE CONSTRAINT category_name_unique IF NOT EXISTS
FOR (c:Category) REQUIRE c.name IS UNIQUE;


// ============================================================================
// INDEXES - Optimize Query Performance
// ============================================================================

// User indexes
CREATE INDEX user_tenant_id IF NOT EXISTS
FOR (u:User) ON (u.tenant_id);

CREATE INDEX user_email IF NOT EXISTS
FOR (u:User) ON (u.email);

// Product indexes
CREATE INDEX product_brand_id IF NOT EXISTS
FOR (p:Product) ON (p.brand_id);

CREATE INDEX product_category IF NOT EXISTS
FOR (p:Product) ON (p.category);

CREATE INDEX product_gender IF NOT EXISTS
FOR (p:Product) ON (p.gender);

CREATE INDEX product_is_active IF NOT EXISTS
FOR (p:Product) ON (p.is_active);

// Biomechanical indexes (for similarity matching)
CREATE INDEX biomech_foot_strike IF NOT EXISTS
FOR (bp:BiomechanicalProfile) ON (bp.foot_strike);

CREATE INDEX biomech_pronation IF NOT EXISTS
FOR (bp:BiomechanicalProfile) ON (bp.pronation_type);

// Brand indexes
CREATE INDEX brand_name IF NOT EXISTS
FOR (b:Brand) ON (b.name);

// Category indexes
CREATE INDEX category_type IF NOT EXISTS
FOR (c:Category) ON (c.type);


// ============================================================================
// FULL-TEXT SEARCH INDEXES (for product search)
// ============================================================================

// Product search by model name
CALL db.index.fulltext.createNodeIndex(
    "product_search",
    ["Product"],
    ["model_name", "full_name", "description"]
) YIELD name
RETURN "Created full-text index: " + name AS status;


// ============================================================================
// NODE LABELS SCHEMA (Documentation)
// ============================================================================

/*
Node Types in StrideMatch Graph:

1. User
   Properties:
     - user_id (INT, unique): User ID from MongoDB
     - tenant_id (INT): Tenant ID for multi-tenancy
     - email (STRING): User email
     - created_at (DATETIME): Account creation date

2. BiomechanicalProfile
   Properties:
     - profile_id (STRING, unique): UUID of biomechanical profile
     - user_id (INT): Associated user ID
     - foot_strike (STRING): heel_strike, midfoot_strike, forefoot_strike
     - pronation_type (STRING): neutral, overpronation, underpronation
     - avg_cadence_spm (INT): Average cadence (steps/min)
     - avg_contact_time_ms (FLOAT): Average ground contact time
     - created_at (DATETIME): Profile creation date

3. Product
   Properties:
     - product_id (STRING, unique): UUID from PostgreSQL
     - brand_id (INT): Brand ID
     - model_name (STRING): Product model name
     - full_name (STRING): Full product name
     - category (STRING): Product category
     - gender (STRING): male, female, unisex
     - is_active (BOOLEAN): Still in production?
     - release_year (INT): Release year
     - drop_mm (FLOAT): Heel-to-toe drop
     - weight_g (FLOAT): Weight in grams
     - cushioning_ha (FLOAT): Cushioning softness
     - stability_type (STRING): neutral, stability_mild, etc.

4. Brand
   Properties:
     - brand_id (INT, unique): Brand ID from PostgreSQL
     - name (STRING): Brand name
     - slug (STRING): URL-friendly name
     - country_origin (STRING): ISO country code

5. Category
   Properties:
     - name (STRING, unique): Category name
     - type (STRING): running_road, running_trail, etc.

6. Tag
   Properties:
     - tag_name (STRING): Tag name (e.g., SUITED_FOR_HEEL_STRIKER)
     - tag_category (STRING): biomechanics, durability, terrain
*/


// ============================================================================
// RELATIONSHIP TYPES SCHEMA (Documentation)
// ============================================================================

/*
Relationship Types in StrideMatch Graph:

1. (User)-[:HAS_PROFILE]->(BiomechanicalProfile)
   Properties: created_at

2. (User)-[:PURCHASED]->(Product)
   Properties:
     - purchase_date (DATETIME)
     - price_paid (FLOAT)
     - rating (INT, 1-5)
     - review_text (STRING)

3. (User)-[:VIEWED]->(Product)
   Properties:
     - viewed_at (DATETIME)
     - view_duration_sec (INT)

4. (User)-[:RATED]->(Product)
   Properties:
     - rating (INT, 1-5)
     - rated_at (DATETIME)

5. (User)-[:PREFERS_BRAND]->(Brand)
   Properties:
     - preference_strength (FLOAT, 0.0-1.0)

6. (Product)-[:BELONGS_TO_BRAND]->(Brand)
   Properties: None

7. (Product)-[:IN_CATEGORY]->(Category)
   Properties: None

8. (Product)-[:HAS_TAG]->(Tag)
   Properties:
     - confidence_score (FLOAT, 0.0-1.0)
     - rule_source (STRING)

9. (Product)-[:CO_PURCHASED_WITH]->(Product)
   Properties:
     - count (INT): Number of co-purchases
     - confidence (FLOAT): Co-purchase confidence

10. (BiomechanicalProfile)-[:SIMILAR_TO]->(BiomechanicalProfile)
    Properties:
      - similarity_score (FLOAT, 0.0-1.0)
      - based_on (LIST<STRING>): ["foot_strike", "pronation_type"]

11. (Product)-[:RECOMMENDED_FOR]->(BiomechanicalProfile)
    Properties:
      - recommendation_score (FLOAT, 0.0-1.0)
      - reasons (LIST<STRING>): ["drop_matches", "stability_matches"]
*/


// ============================================================================
// SAMPLE DATA - Initial Nodes and Relationships (For Testing)
// ============================================================================

// Create sample categories
MERGE (c1:Category {name: "Running Road", type: "running_road"})
MERGE (c2:Category {name: "Running Trail", type: "running_trail"})
MERGE (c3:Category {name: "Running Track", type: "running_track"})
MERGE (c4:Category {name: "Walking", type: "walking"})
MERGE (c5:Category {name: "Training", type: "training"});

// Create sample tags (biomechanical matching tags)
MERGE (t1:Tag {tag_name: "SUITED_FOR_HEEL_STRIKER", tag_category: "biomechanics"})
MERGE (t2:Tag {tag_name: "SUITED_FOR_MIDFOOT_STRIKER", tag_category: "biomechanics"})
MERGE (t3:Tag {tag_name: "SUITED_FOR_FOREFOOT_STRIKER", tag_category: "biomechanics"})
MERGE (t4:Tag {tag_name: "SUITED_FOR_OVERPRONATOR", tag_category: "biomechanics"})
MERGE (t5:Tag {tag_name: "SUITED_FOR_SUPINATOR", tag_category: "biomechanics"})
MERGE (t6:Tag {tag_name: "SUITED_FOR_NEUTRAL_RUNNER", tag_category: "biomechanics"})
MERGE (t7:Tag {tag_name: "HIGH_DURABILITY", tag_category: "durability"})
MERGE (t8:Tag {tag_name: "LIGHTWEIGHT", tag_category: "weight"})
MERGE (t9:Tag {tag_name: "SUITED_FOR_HEAVY_RUNNER", tag_category: "weight"})
MERGE (t10:Tag {tag_name: "SUITED_FOR_TRAIL", tag_category: "terrain"});


// ============================================================================
// GRAPH DATA POPULATION STRATEGY
// ============================================================================

/*
Data Population Approach:

The graph will be populated by ETL scripts that sync data from PostgreSQL and MongoDB:

1. BRANDS (from PostgreSQL stridematch_brands)
   Script: sync_brands_to_neo4j.py
   Creates Brand nodes

2. PRODUCTS (from PostgreSQL stridematch_products + specs tables)
   Script: sync_products_to_neo4j.py
   Creates Product nodes with embedded specs
   Creates (Product)-[:BELONGS_TO_BRAND]->(Brand)
   Creates (Product)-[:IN_CATEGORY]->(Category)
   Creates (Product)-[:HAS_TAG]->(Tag) from enrichment_tags table

3. USERS (from MongoDB users collection)
   Script: sync_users_to_neo4j.py
   Creates User nodes
   Creates BiomechanicalProfile nodes from users.biomechanics
   Creates (User)-[:HAS_PROFILE]->(BiomechanicalProfile)

4. INTERACTIONS (from application events/logs)
   Script: sync_interactions_to_neo4j.py
   Creates (User)-[:PURCHASED]->(Product)
   Creates (User)-[:VIEWED]->(Product)
   Creates (User)-[:RATED]->(Product)

5. CO-PURCHASE PATTERNS (computed from purchase history)
   Script: compute_copurchases.py
   Creates (Product)-[:CO_PURCHASED_WITH]->(Product)

6. BIOMECHANICAL SIMILARITIES (computed from profiles)
   Script: compute_biomech_similarities.py
   Creates (BiomechanicalProfile)-[:SIMILAR_TO]->(BiomechanicalProfile)

7. RECOMMENDATIONS (computed by recommendation engine)
   Script: compute_recommendations.py
   Creates (Product)-[:RECOMMENDED_FOR]->(BiomechanicalProfile)

These scripts will be located in:
  app/packs/stridematch/scraping/neo4j_sync/
*/


// ============================================================================
// EXAMPLE QUERIES (For Testing and Development)
// ============================================================================

/*
1. Find products recommended for a specific biomechanical profile:

MATCH (bp:BiomechanicalProfile {foot_strike: "heel_strike", pronation_type: "overpronation"})
      <-[:RECOMMENDED_FOR]-(p:Product)-[:BELONGS_TO_BRAND]->(b:Brand)
RETURN p.model_name, b.name, p.drop_mm, p.stability_type
ORDER BY p.recommendation_score DESC
LIMIT 10;


2. Find users with similar biomechanical profiles:

MATCH (u1:User {user_id: 42})-[:HAS_PROFILE]->(bp1:BiomechanicalProfile)
      -[:SIMILAR_TO]->(bp2:BiomechanicalProfile)<-[:HAS_PROFILE]-(u2:User)
RETURN u2.email, bp2.foot_strike, bp2.pronation_type, bp2.similarity_score
ORDER BY bp2.similarity_score DESC
LIMIT 10;


3. Find products frequently co-purchased with a specific product:

MATCH (p1:Product {product_id: "some-uuid"})-[cp:CO_PURCHASED_WITH]->(p2:Product)
      -[:BELONGS_TO_BRAND]->(b:Brand)
RETURN p2.model_name, b.name, cp.count, cp.confidence
ORDER BY cp.count DESC
LIMIT 10;


4. Find all products suitable for heel strikers with overpronation:

MATCH (p:Product)-[:HAS_TAG]->(t1:Tag {tag_name: "SUITED_FOR_HEEL_STRIKER"}),
      (p)-[:HAS_TAG]->(t2:Tag {tag_name: "SUITED_FOR_OVERPRONATOR"}),
      (p)-[:BELONGS_TO_BRAND]->(b:Brand)
RETURN p.model_name, b.name, p.drop_mm, p.stability_type, p.cushioning_ha
ORDER BY p.release_year DESC
LIMIT 20;


5. Full-text search for products:

CALL db.index.fulltext.queryNodes("product_search", "pegasus nike")
YIELD node, score
MATCH (node)-[:BELONGS_TO_BRAND]->(b:Brand)
RETURN node.model_name, b.name, score
ORDER BY score DESC
LIMIT 10;


6. Collaborative filtering: "Users who bought X also bought Y":

MATCH (p1:Product {product_id: "some-uuid"})<-[:PURCHASED]-(u:User)
      -[:PURCHASED]->(p2:Product)-[:BELONGS_TO_BRAND]->(b:Brand)
WHERE p1 <> p2
RETURN p2.model_name, b.name, COUNT(u) AS purchase_count
ORDER BY purchase_count DESC
LIMIT 10;


7. Graph Neural Network input: Get neighborhood for a user:

MATCH path = (u:User {user_id: 42})-[:HAS_PROFILE|PURCHASED|RATED|PREFERS_BRAND*1..2]-(related)
RETURN path
LIMIT 50;
*/


// ============================================================================
// GRAPH ALGORITHMS PREPARATION (for advanced recommendations)
// ============================================================================

/*
Neo4j Graph Data Science (GDS) Library Algorithms to Use:

1. PageRank - Product importance ranking
CALL gds.pageRank.stream({
    nodeProjection: 'Product',
    relationshipProjection: 'CO_PURCHASED_WITH'
})
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).model_name AS product, score
ORDER BY score DESC LIMIT 10;

2. Node Similarity - Find similar products based on shared users
CALL gds.nodeSimilarity.stream({
    nodeProjection: ['User', 'Product'],
    relationshipProjection: {
        PURCHASED: {orientation: 'UNDIRECTED'}
    }
})
YIELD node1, node2, similarity
RETURN gds.util.asNode(node1).model_name AS product1,
       gds.util.asNode(node2).model_name AS product2,
       similarity
ORDER BY similarity DESC LIMIT 20;

3. Community Detection - Cluster users by purchase behavior
CALL gds.louvain.stream({
    nodeProjection: 'User',
    relationshipProjection: {
        PURCHASED: {orientation: 'UNDIRECTED'}
    }
})
YIELD nodeId, communityId
RETURN gds.util.asNode(nodeId).email AS user, communityId
ORDER BY communityId;

4. GraphSAGE - Inductive node embeddings for deep learning recommendations
// To be implemented in Phase 7+
*/


// ============================================================================
// INITIALIZATION COMPLETE
// ============================================================================

// Return confirmation
RETURN "StrideMatch Neo4j graph schema initialized successfully!" AS status,
       "Constraints: 5, Indexes: 11, Sample nodes created" AS details;
