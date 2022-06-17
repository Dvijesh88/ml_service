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