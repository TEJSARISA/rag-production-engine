import pytest
from deepeval.test_case import LLMTestCase
from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric, HallucinationMetric

# Synthetic evaluation dataset with domain questions, context groundings, and synthetic responses
SYNTHETIC_DATASET = [
    {
        "input": "What database extension is used for vector search in PostgreSQL?",
        "context": ["PostgreSQL uses the pgvector extension to store and search vector embeddings using distance metrics like cosine similarity."],
        "actual_output": "PostgreSQL uses the pgvector extension to store and query vector embeddings efficiently.",
        "expected_output": "The pgvector extension is used for vector search in PostgreSQL."
    },
    {
        "input": "Which task queue framework is integrated into the RAG backend?",
        "context": ["Background document ingestion and vector embedding processing is powered by Celery workers backed by a Redis broker."],
        "actual_output": "The service integrates Celery workers with a Redis broker for asynchronous background document ingestion.",
        "expected_output": "Celery with Redis is used as the background task queue."
    },
    {
        "input": "What metrics are evaluated in the automated test suite?",
        "context": ["The DeepEval evaluation suite tests FaithfulnessMetric (threshold 0.8), AnswerRelevancyMetric (threshold 0.8), and HallucinationMetric (threshold 0.2)."],
        "actual_output": "The automated evaluations cover Faithfulness, Answer Relevancy, and Hallucination metrics.",
        "expected_output": "Faithfulness, Answer Relevancy, and Hallucination metrics are evaluated."
    },
    {
        "input": "How are documents uploaded and processed?",
        "context": ["Documents are uploaded via POST /api/v1/documents/upload, returning HTTP 202 with task_id. A background worker splits text into chunks of 500 words with 50 word overlap."],
        "actual_output": "Users upload documents via POST endpoint, receiving a task ID while Celery splits content into 500-word chunks with 50-word overlap in the background.",
        "expected_output": "Documents are uploaded via HTTP POST and processed asynchronously by background workers into chunks."
    },
    {
        "input": "What deployment options are supported?",
        "context": ["The service includes a production Dockerfile, docker-compose.yml for local orchestration, and scripts for deployment to Azure Container Apps, Render, or Railway."],
        "actual_output": "Deployment is supported locally via Docker Compose and in production on Azure Container Apps, Render, or Railway.",
        "expected_output": "Azure Container Apps, Render, Railway, and Docker Compose."
    }
]

@pytest.mark.parametrize("item", SYNTHETIC_DATASET)
def test_faithfulness(item):
    metric = FaithfulnessMetric(threshold=0.8)
    test_case = LLMTestCase(
        input=item["input"],
        actual_output=item["actual_output"],
        retrieval_context=item["context"]
    )
    metric.measure(test_case)
    assert metric.score >= metric.threshold, f"Faithfulness score {metric.score} below threshold {metric.threshold}"

@pytest.mark.parametrize("item", SYNTHETIC_DATASET)
def test_answer_relevancy(item):
    metric = AnswerRelevancyMetric(threshold=0.8)
    test_case = LLMTestCase(
        input=item["input"],
        actual_output=item["actual_output"]
    )
    metric.measure(test_case)
    assert metric.score >= metric.threshold, f"Relevancy score {metric.score} below threshold {metric.threshold}"

@pytest.mark.parametrize("item", SYNTHETIC_DATASET)
def test_hallucination(item):
    metric = HallucinationMetric(threshold=0.2)
    test_case = LLMTestCase(
        input=item["input"],
        actual_output=item["actual_output"],
        context=item["context"]
    )
    metric.measure(test_case)
    assert metric.score <= metric.threshold, f"Hallucination score {metric.score} exceeded threshold {metric.threshold}"
