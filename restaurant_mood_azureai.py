from azure.ai.projects import ProjectsClient
from azure.identity import DefaultAzureCredential

endpoint = "https://mit-pocs.services.ai.azure.com/api/projects/restaurantRoulette"  # Replace with your actual project endpoint

project_client = ProjectsClient(
    endpoint=endpoint,
    credential=DefaultAzureCredential()
)