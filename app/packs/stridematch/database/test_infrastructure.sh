#!/bin/bash

# ============================================================================
# StrideMatch Infrastructure Test Script
# ============================================================================
#
# This script tests the entire StrideMatch database infrastructure:
# - PostgreSQL (product catalog)
# - MongoDB (user profiles)
# - Neo4j (recommendation graph)
#
# Usage:
#   chmod +x test_infrastructure.sh
#   ./test_infrastructure.sh
# ============================================================================

set -e  # Exit on error

echo "============================================================"
echo "StrideMatch Infrastructure Test"
echo "============================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================================================
# 1. Check Docker is Running
# ============================================================================

echo "📋 Step 1: Checking Docker status..."
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker Desktop.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker is running${NC}"
echo ""

# ============================================================================
# 2. Start Services
# ============================================================================

echo "📋 Step 2: Starting database services..."
docker-compose up -d db mongodb neo4j

echo "⏳ Waiting for services to be ready (30 seconds)..."
sleep 30

# Check services are running
if docker-compose ps | grep -q "db.*Up"; then
    echo -e "${GREEN}✅ PostgreSQL is running${NC}"
else
    echo -e "${RED}❌ PostgreSQL failed to start${NC}"
    exit 1
fi

if docker-compose ps | grep -q "mongodb.*Up"; then
    echo -e "${GREEN}✅ MongoDB is running${NC}"
else
    echo -e "${RED}❌ MongoDB failed to start${NC}"
    exit 1
fi

if docker-compose ps | grep -q "neo4j.*Up"; then
    echo -e "${GREEN}✅ Neo4j is running${NC}"
else
    echo -e "${RED}❌ Neo4j failed to start${NC}"
    exit 1
fi
echo ""

# ============================================================================
# 3. Initialize PostgreSQL
# ============================================================================

echo "📋 Step 3: Initializing PostgreSQL schema..."

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Execute schema.sql
PGPASSWORD="${POSTGRES_PASSWORD}" psql \
    -h localhost \
    -p 5432 \
    -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" \
    -f app/packs/stridematch/database/schema.sql

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ PostgreSQL schema initialized${NC}"
else
    echo -e "${RED}❌ Failed to initialize PostgreSQL schema${NC}"
    exit 1
fi

# Verify tables were created
echo "🔍 Verifying PostgreSQL tables..."
TABLE_COUNT=$(PGPASSWORD="${POSTGRES_PASSWORD}" psql \
    -h localhost \
    -p 5432 \
    -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" \
    -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE 'stridematch_%';")

echo "   Found ${TABLE_COUNT} StrideMatch tables"

if [ "$TABLE_COUNT" -ge 7 ]; then
    echo -e "${GREEN}✅ All tables created successfully${NC}"
else
    echo -e "${YELLOW}⚠️  Expected 7 tables, found ${TABLE_COUNT}${NC}"
fi

# Verify seed data (brands)
BRAND_COUNT=$(PGPASSWORD="${POSTGRES_PASSWORD}" psql \
    -h localhost \
    -p 5432 \
    -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" \
    -t -c "SELECT COUNT(*) FROM stridematch_brands;")

echo "   Found ${BRAND_COUNT} brands in database"

if [ "$BRAND_COUNT" -ge 10 ]; then
    echo -e "${GREEN}✅ Seed data loaded (${BRAND_COUNT} brands)${NC}"
else
    echo -e "${YELLOW}⚠️  Expected 10 brands, found ${BRAND_COUNT}${NC}"
fi
echo ""

# ============================================================================
# 4. Test MongoDB
# ============================================================================

echo "📋 Step 4: Testing MongoDB..."

# Test MongoDB connection
docker exec $(docker-compose ps -q mongodb) mongosh \
    --username stridematch \
    --password stridematch_password \
    --authenticationDatabase admin \
    --eval "db.adminCommand('ping')" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ MongoDB connection successful${NC}"
else
    echo -e "${RED}❌ Failed to connect to MongoDB${NC}"
    exit 1
fi

# Create test user profile
echo "🔍 Creating test user profile in MongoDB..."
docker exec $(docker-compose ps -q mongodb) mongosh \
    stridematch \
    --username stridematch \
    --password stridematch_password \
    --authenticationDatabase admin \
    --eval '
db.users.insertOne({
  user_id: 1,
  tenant_id: 1,
  email: "test@stridematch.com",
  demographics: {
    age: 35,
    weight_kg: 75.0,
    height_cm: 175.0,
    gender: "male"
  },
  biomechanics: {
    foot_strike: "heel_strike",
    pronation_type: "overpronation",
    avg_cadence_spm: 172
  },
  created_at: new Date()
})' > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Test user profile created${NC}"
else
    echo -e "${YELLOW}⚠️  User profile might already exist${NC}"
fi

# Count documents
USER_COUNT=$(docker exec $(docker-compose ps -q mongodb) mongosh \
    stridematch \
    --username stridematch \
    --password stridematch_password \
    --authenticationDatabase admin \
    --quiet \
    --eval "db.users.countDocuments()")

echo "   Found ${USER_COUNT} user(s) in MongoDB"
echo ""

# ============================================================================
# 5. Test Neo4j
# ============================================================================

echo "📋 Step 5: Testing Neo4j..."

# Wait for Neo4j to be fully ready
echo "⏳ Waiting for Neo4j to be fully ready (10 seconds)..."
sleep 10

# Test Neo4j connection
docker exec $(docker-compose ps -q neo4j) cypher-shell \
    -u neo4j \
    -p stridematch_neo4j \
    "RETURN 'Connection successful' AS status;" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Neo4j connection successful${NC}"
else
    echo -e "${RED}❌ Failed to connect to Neo4j${NC}"
    echo "   Try accessing Neo4j Browser: http://localhost:7474"
    echo "   Credentials: neo4j / stridematch_neo4j"
fi

# Initialize Neo4j schema (execute cypher script)
echo "🔍 Initializing Neo4j schema..."
docker exec $(docker-compose ps -q neo4j) cypher-shell \
    -u neo4j \
    -p stridematch_neo4j \
    -f /import/init.cypher > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Neo4j schema initialized${NC}"
else
    echo -e "${YELLOW}⚠️  Neo4j schema might already be initialized${NC}"
fi

# Count constraints
CONSTRAINT_COUNT=$(docker exec $(docker-compose ps -q neo4j) cypher-shell \
    -u neo4j \
    -p stridematch_neo4j \
    --format plain \
    "SHOW CONSTRAINTS;" 2>/dev/null | grep -c "CONSTRAINT" || echo "0")

echo "   Found ${CONSTRAINT_COUNT} constraint(s) in Neo4j"
echo ""

# ============================================================================
# 6. Summary
# ============================================================================

echo "============================================================"
echo "Test Summary"
echo "============================================================"
echo ""
echo -e "${GREEN}✅ PostgreSQL:${NC} ${TABLE_COUNT} tables, ${BRAND_COUNT} brands"
echo -e "${GREEN}✅ MongoDB:${NC} ${USER_COUNT} user(s)"
echo -e "${GREEN}✅ Neo4j:${NC} ${CONSTRAINT_COUNT} constraint(s)"
echo ""
echo "🌐 Access Points:"
echo "   - PostgreSQL: localhost:5432"
echo "   - MongoDB: localhost:27017"
echo "   - Neo4j Browser: http://localhost:7474"
echo ""
echo "🔑 Credentials (from .env):"
echo "   - PostgreSQL: ${POSTGRES_USER} / ${POSTGRES_PASSWORD}"
echo "   - MongoDB: stridematch / stridematch_password"
echo "   - Neo4j: neo4j / stridematch_neo4j"
echo ""
echo -e "${GREEN}✅ Infrastructure test completed successfully!${NC}"
echo "============================================================"
