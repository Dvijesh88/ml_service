from gettext import translation
from rest_framework.exceptions import APIException

# Create your views here.
from rest_framework import mixins
from rest_framework import viewsets

from endpoints.models import Endpoint
from endpoints.serializers import EndpointSerializer

from endpoints.models import MLAlgorithm
from endpoints.serializers import MLAlgorithmSerializer

from endpoints.models import MLAlgorithmStatus
from endpoints.serializers import MLAlgorithmStatusSerializer

from endpoints.models import MLRequest
from endpoints.serializers import MLRequestSerializer

import json
from numpy.random import rand
from rest_framework import views, status
from rest_framework.response import Response
from ml.registry import MLRegistry
from server.wsgi import registry

class EndpointViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = EndpointSerializer
    queryset = Endpoint.objects.all()


class MLAlgorithmViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = MLAlgorithmStatusSerializer
    queryset = MLAlgorithmStatus.objects.all()

def deactivate_other_statues(instance):
    old_statues = MLAlgorithmStatus.objects.filter(parent_mlalgorithm=instance.parent_mlalgorithm, created_at_lt=instance.created_at, active=True)

    for i in range(len(old_statues)):
        old_statues[i].active = False
    MLAlgorithmStatus.objects.bulk_update(old_statues, ["active"])

class MLAlgorithmStatusViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = MLAlgorithmStatusSerializer
    queryset = MLAlgorithmStatus.objects.all()

    def perform_create(self, serializer):
        try:
            with translation.atomic():
                instance = serializer.save(active=True)
                deactivate_other_statues(instance)
        except Exception as e:
            raise APIException(str(e))

class MLRequestViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = MLRequestSerializer
    queryset = MLRequest.objects.all()


class PredictView(views.APIView):
    def post(self, request, endpoint_name, format=None):
        algorithm_status = self.request.query_params.get('status', 'production')
        algorithm_version = self.request.query_params.get('version')

        algs =  MLAlgorithm.objects.filter(parent_endpoint__name=endpoint_name, status__status=algorithm_status, status__active=True)
        if algorithm_version is not None:
            algs = algs.filter(version=algorithm_version)
        
        if len(algs) == 0:
            return Response({"status": "error", "message": "ML algorithm not found"}, status=status.HTTP_404_NOT_FOUND)
        print("-----------------> ", len(algs))
        if len(algs) != 1 and algorithm_status != 'ab_testing':
            return Response({"status": "error", "message": "ML algorithm selection is ambiguous, please select specific version "}, status=status.HTTP_404_NOT_FOUND)
        
        alg_index = 0
        if algorithm_status == 'ab_testing':
            alg_index = 0 if rand() < 0.5 else 1
        
        algorithm_object = registry.endpoints[algs[alg_index].id]
        prediction = algorithm_object.compute_prediction(request.data)

        label = prediction['label'] if 'label' in prediction else 'error'

        ml_request = MLRequest(
            input_data = json.dumps(request.data),
            full_response = prediction,
            response = label,
            feedback = "",
            parent_mlalgorithm = algs[alg_index],
        )
        ml_request.save()

        prediction['request_id'] = ml_request.id

        return Response(prediction)