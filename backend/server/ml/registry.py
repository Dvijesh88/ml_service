from endpoints.models import Endpoint
from endpoints.models import MLAlgorithm
from endpoints.models import MLAlgorithmStatus

class MLRegistry:
    def __init__(self):
        self.endpoints = {}

    def add_algorithm (self, endpoint_name, algorithm_name, algorithm_object, algorithm_status, algorithm_version, owner, algorithm_description, algorithm_code):
        enpoints, _ = Endpoint.objects.get_or_create(name=endpoint_name, owner=owner)
    
        #get algorithm
        database_object, algoritm_created = MLAlgorithm.objects.get_or_create(
            name=algorithm_name,
            description=algorithm_description,
            code=algorithm_code,
            version=algorithm_version,
            owner=owner,
            parent_endpoint=enpoints,
        )

        if algoritm_created:
            status = MLAlgorithmStatus(
                status=algorithm_status, created_by = owner, parent_mlalgorithm=database_object, active = True)
            status.save()
        
        self.endpoints[database_object.id] = algorithm_object
    