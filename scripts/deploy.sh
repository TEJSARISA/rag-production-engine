#!/usr/bin/env bash

# File: scripts/deploy.sh
# Automated Deployment Script for Azure Container Apps & Render Infrastructure

set -e

echo "================─────────────────────────"
echo " Asynchronous RAG Engine - Deployment    "
echo "================─────────────────────────"

# Azure Container Apps Deployment Sequence
deploy_azure() {
    echo "🔍 Checking Azure CLI installation & authentication..."
    if ! command -v az &> /dev/null; then
        echo "❌ Azure CLI ('az') is not installed."
        return 1
    fi

    if ! az account show &> /dev/null; then
        echo "⚠️ Azure CLI is not logged in. Please run 'az login' first."
        return 1
    fi

    AZ_SUBSCRIPTION=$(az account show --query name -o tsv)
    echo "✅ Azure CLI logged in under subscription: $AZ_SUBSCRIPTION"

    RESOURCE_GROUP="${RESOURCE_GROUP:-rag-engine-rg}"
    LOCATION="${LOCATION:-centralindia}"
    RANDOM_ID=$((1000 + RANDOM % 9000))
    REGISTRY_NAME="${REGISTRY_NAME:-ragregistry$RANDOM_ID}"
    APP_NAME="${APP_NAME:-rag-production-engine}"
    ENV_NAME="${ENV_NAME:-rag-env}"

    echo "🚀 Creating Azure Resource Group: $RESOURCE_GROUP in $LOCATION..."
    az group create --name "$RESOURCE_GROUP" --location "$LOCATION"

    echo "📦 Creating Azure Container Registry: $REGISTRY_NAME..."
    az acr create --resource-group "$RESOURCE_GROUP" --name "$REGISTRY_NAME" --sku Basic --admin-enabled true

    echo "🔨 Building image inside Azure Container Registry..."
    az acr build --registry "$REGISTRY_NAME" --image rag-api:latest .

    echo "⚡ Deploying Azure Container App..."
    az containerapp up \
        --name "$APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --environment "$ENV_NAME" \
        --image "$REGISTRY_NAME.azurecr.io/rag-api:latest" \
        --target-port 8000 \
        --ingress external

    echo "🎉 Azure Container App deployment initiated successfully!"
}

# Main Execution Flow
echo "Attempting deployment..."
if deploy_azure; then
    echo "✅ Azure Container Apps deployment completed!"
else
    echo "--------------------------------------------------------"
    echo "ℹ️ Azure CLI deployment skipped or not logged in."
    echo "ℹ️ You can deploy via Render Blueprint using render.yaml,"
    echo "ℹ️ or log in with 'az login' and rerun scripts/deploy.sh."
    echo "--------------------------------------------------------"
fi
