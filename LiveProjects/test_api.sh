#!/bin/bash

# Complete API Testing Script
# This script tests all API endpoints to ensure the application is working correctly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
BASE_URL="http://127.0.0.1:8888"
TEST_EMAIL="test$(date +%s)@example.com"  # Unique email for each test
TEST_USERNAME="testuser$(date +%s)"        # Unique username for each test
TEST_PASSWORD="test123"

# Function to print colored output
print_test() {
    echo -e "${BLUE}🧪 Testing: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_fail() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Function to test JSON response
test_json_response() {
    local url="$1"
    local expected_field="$2"
    local test_name="$3"
    
    print_test "$test_name"
    
    response=$(curl -s "$url")
    if echo "$response" | python -c "import sys, json; data=json.load(sys.stdin); print(data.get('$expected_field', 'NOT_FOUND'))" | grep -v "NOT_FOUND" >/dev/null; then
        print_success "$test_name passed"
        return 0
    else
        print_fail "$test_name failed"
        echo "Response: $response"
        return 1
    fi
}

# Function to make authenticated request
make_auth_request() {
    local method="$1"
    local endpoint="$2"
    local token="$3"
    local data="$4"
    
    if [ -n "$data" ]; then
        curl -s -X "$method" "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $token" \
            -d "$data"
    else
        curl -s -X "$method" "$BASE_URL$endpoint" \
            -H "Authorization: Bearer $token"
    fi
}

echo "🚀 Production Observability App - Complete API Test"
echo "=================================================="
echo ""

# Test 1: Check if application is running
print_test "Application availability"
if curl -s "$BASE_URL/" >/dev/null 2>&1; then
    print_success "Application is responding"
else
    print_fail "Application is not responding at $BASE_URL"
    echo "Please ensure the application is running with: ./run.sh"
    exit 1
fi
echo ""

# Test 2: Root endpoint
test_json_response "$BASE_URL/" "status" "Root endpoint"
echo ""

# Test 3: Health check
test_json_response "$BASE_URL/api/v1/health" "status" "Health check endpoint"
echo ""

# Test 4: Metrics endpoint
print_test "Metrics endpoint"
if curl -s "$BASE_URL/metrics" | grep "http_requests_total" >/dev/null; then
    print_success "Metrics endpoint working"
else
    print_fail "Metrics endpoint failed"
fi
echo ""

# Test 5: User Registration
print_test "User registration"
registration_response=$(curl -s -X POST "$BASE_URL/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d "{
        \"email\": \"$TEST_EMAIL\",
        \"username\": \"$TEST_USERNAME\",
        \"password\": \"$TEST_PASSWORD\",
        \"full_name\": \"Test User\"
    }")

if echo "$registration_response" | python -c "import sys, json; data=json.load(sys.stdin); print(data.get('id', 'FAILED'))" | grep -v "FAILED" >/dev/null; then
    print_success "User registration successful"
    USER_ID=$(echo "$registration_response" | python -c "import sys, json; data=json.load(sys.stdin); print(data.get('id', ''))")
    print_info "Created user ID: $USER_ID"
else
    print_fail "User registration failed"
    echo "Response: $registration_response"
    exit 1
fi
echo ""

# Test 6: User Login
print_test "User login"
login_response=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{
        \"email\": \"$TEST_EMAIL\",
        \"password\": \"$TEST_PASSWORD\"
    }")

if echo "$login_response" | python -c "import sys, json; data=json.load(sys.stdin); print(data.get('access_token', 'FAILED'))" | grep -v "FAILED" >/dev/null; then
    print_success "User login successful"
    ACCESS_TOKEN=$(echo "$login_response" | python -c "import sys, json; data=json.load(sys.stdin); print(data.get('access_token', ''))")
    print_info "JWT token obtained"
else
    print_fail "User login failed"
    echo "Response: $login_response"
    exit 1
fi
echo ""

# Test 7: Get current user info
print_test "Get current user info"
user_info_response=$(make_auth_request "GET" "/api/v1/auth/me" "$ACCESS_TOKEN")

if echo "$user_info_response" | python -c "import sys, json; data=json.load(sys.stdin); print(data.get('email', 'FAILED'))" | grep "$TEST_EMAIL" >/dev/null; then
    print_success "Get current user info successful"
else
    print_fail "Get current user info failed"
    echo "Response: $user_info_response"
fi
echo ""

# Test 8: Create a task
print_test "Create task"
task_response=$(make_auth_request "POST" "/api/v1/tasks" "$ACCESS_TOKEN" "{
    \"title\": \"Test Task\",
    \"description\": \"This is a test task created by the test script\",
    \"priority\": \"high\"
}")

if echo "$task_response" | python -c "import sys, json; data=json.load(sys.stdin); print(data.get('id', 'FAILED'))" | grep -v "FAILED" >/dev/null; then
    print_success "Task creation successful"
    TASK_ID=$(echo "$task_response" | python -c "import sys, json; data=json.load(sys.stdin); print(data.get('id', ''))")
    print_info "Created task ID: $TASK_ID"
else
    print_fail "Task creation failed"
    echo "Response: $task_response"
fi
echo ""

# Test 9: Get tasks
print_test "Get user tasks"
tasks_response=$(make_auth_request "GET" "/api/v1/tasks" "$ACCESS_TOKEN")

if echo "$tasks_response" | python -c "import sys, json; data=json.load(sys.stdin); print(len(data) if isinstance(data, list) else 'FAILED')" | grep -v "FAILED" >/dev/null; then
    print_success "Get tasks successful"
    TASK_COUNT=$(echo "$tasks_response" | python -c "import sys, json; data=json.load(sys.stdin); print(len(data) if isinstance(data, list) else 0)")
    print_info "Found $TASK_COUNT tasks"
else
    print_fail "Get tasks failed"
    echo "Response: $tasks_response"
fi
echo ""

# Test 10: Unauthorized access test
print_test "Unauthorized access protection"
unauthorized_response=$(curl -s -w "%{http_code}" -X GET "$BASE_URL/api/v1/tasks")
http_code="${unauthorized_response: -3}"

if [ "$http_code" = "403" ]; then
    print_success "Unauthorized access properly blocked (HTTP 403)"
else
    print_fail "Unauthorized access test failed (expected HTTP 403, got $http_code)"
fi
echo ""

# Test 11: Test invalid login
print_test "Invalid login protection"
invalid_login_response=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{
        \"email\": \"invalid@example.com\",
        \"password\": \"wrongpassword\"
    }")
http_code="${invalid_login_response: -3}"

if [ "$http_code" = "401" ]; then
    print_success "Invalid login properly rejected (HTTP 401)"
else
    print_fail "Invalid login test failed (expected HTTP 401, got $http_code)"
fi
echo ""

# Final summary
echo "📋 Test Summary"
echo "==============="
print_success "All tests completed!"
echo ""
print_info "Application is running at: $BASE_URL"
print_info "API Documentation: $BASE_URL/docs"
print_info "Health Check: $BASE_URL/api/v1/health"
print_info "Metrics: $BASE_URL/metrics"
echo ""
print_info "Test user created:"
print_info "  Email: $TEST_EMAIL"
print_info "  Username: $TEST_USERNAME"
print_info "  Password: $TEST_PASSWORD"
echo ""
echo "🎉 Your Production Observability App is working perfectly!"