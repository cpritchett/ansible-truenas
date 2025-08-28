#!/bin/bash
# Complete validation script for development
# Runs both upstream and ansible-test validations

set -e

echo "🔍 TrueNAS Incus Module Validation"
echo "================================="

# Check if we're in the right directory
if [[ ! -f "galaxy.yml" ]]; then
    echo "❌ Error: Must be run from ansible-truenas root directory"
    exit 1
fi

# Check dependencies
if ! command -v ansible-test &> /dev/null; then
    echo "⚠️  Warning: ansible-test not found, skipping sanity tests"
    SKIP_SANITY=1
fi

if ! command -v pytest &> /dev/null; then
    echo "⚠️  Warning: pytest not found, skipping unit tests"
    SKIP_UNIT=1
fi

echo ""
echo "🧹 Cleaning previous artifacts..."
make -f Makefile.dev clean > /dev/null 2>&1 || true

echo ""
echo "=== UPSTREAM VALIDATION ==="

echo "📝 Running upstream lint..."
if ! make lint; then
    echo "❌ Upstream lint failed"
    exit 1
fi

echo "📚 Running upstream doc check..."
if ! make check-docs; then
    echo "❌ Upstream doc check failed"  
    exit 1
fi

if [[ -z "$SKIP_SANITY" ]]; then
    echo ""
    echo "=== ANSIBLE-TEST VALIDATION ==="
    
    echo "🔬 Running ansible-test sanity..."
    if ! make -f Makefile.dev sanity-test; then
        echo "❌ ansible-test sanity failed"
        exit 1
    fi
else
    echo ""
    echo "⏭️  Skipping ansible-test (not available)"
fi

if [[ -z "$SKIP_UNIT" ]]; then
    echo ""
    echo "=== UNIT TESTS ==="
    
    echo "🧪 Running unit tests..."
    if ! make -f Makefile.dev unit-test; then
        echo "❌ Unit tests failed"
        exit 1
    fi
else
    echo ""
    echo "⏭️  Skipping unit tests (pytest not available)"
fi

echo ""
echo "=== SYNTAX VALIDATION ==="

echo "📋 Validating integration test syntax..."
if ! make -f Makefile.dev integration-test-syntax; then
    echo "❌ Integration test syntax validation failed"
    exit 1
fi

echo "📋 Validating example syntax..."
if ! make -f Makefile.dev example-syntax; then
    echo "❌ Example syntax validation failed"
    exit 1
fi

echo ""
echo "🧹 Cleaning up..."
make -f Makefile.dev clean > /dev/null 2>&1

echo ""
echo "🎉 ALL VALIDATIONS PASSED!"
echo ""
echo "Ready for upstream contribution:"
echo "  • Upstream lint: ✅"
echo "  • Upstream docs: ✅"
[[ -z "$SKIP_SANITY" ]] && echo "  • ansible-test: ✅"
[[ -z "$SKIP_UNIT" ]] && echo "  • Unit tests: ✅"
echo "  • Integration test syntax: ✅"
echo "  • Example syntax: ✅"
echo ""
echo "Use 'git status' to review changes before committing."