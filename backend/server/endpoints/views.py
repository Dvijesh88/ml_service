from django.db import transaction
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

from endpoints.models import ABtesting
from endpoints.serializers import ABTestSerializer

from django.db.models import F
import datetime

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
    old_statues = MLAlgorithmStatus.objects.filter(parent_mlalgorithm=instance.parent_mlalgorithm, created_at__lt=instance.created_at, active=True)

    for i in range(len(old_statues)):
        old_statues[i].active = False
    MLAlgorithmStatus.objects.bulk_update(old_statues, ["active"])

class MLAlgorithmStatusViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = MLAlgorithmStatusSerializer
    queryset = MLAlgorithmStatus.objects.all()

    def perform_create(self, serializer):
        try:
            with transaction.atomic():
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

class ABTestViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin , viewsets.GenericViewSet):
    serializer_class = ABTestSerializer
    queryset = ABtesting.objects.all()

    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                instance = serializer.save()
                #update stattus for first algorithm
                status_1 = MLAlgorithmStatus(status = "ab_testing",
                                created_by=instance.created_by,
                                parent_mlalgorithm = instance.parent_mlalgorithm_1,
                                active=True)
                status_1.save()
                deactivate_other_statues(status_1)
                # update status for second algorithm
                status_2 = MLAlgorithmStatus(status = "ab_testing",
                                created_by=instance.created_by,
                                parent_mlalgorithm = instance.parent_mlalgorithm_2,
                                active=True)
                status_2.save()
                deactivate_other_statues(status_2)
        except Exception as e:
            raise APIException(str(e))

class StopABTestView(views.APIView):
    def post(self, request, ab_test_id, format=None):
        try:
            ab_test = ABtesting.objects.get(pk=ab_test_id)
            if ab_test.ended_at is not None:
                return Response({ "message": "AB Test already finished."})
            
            date_now = datetime.datetime.now()
            # alg #1 accuracy
            all_responses_1 = MLRequest.objects.filter(parent_mlalgorithm=ab_test.parent_mlalgorithm_1, created_at__gt = ab_test.created_at, created_at__lt = date_now).count()
            correct_responses_1 = MLRequest.objects.filter(parent_mlalgorithm=ab_test.parent_mlalgorithm_1, created_at__gt = ab_test.created_at, created_at__lt = date_now, response=F('feedback')).count()
            accuracy_1 = correct_responses_1 / float(all_responses_1)
            print(all_responses_1, correct_responses_1, accuracy_1)

            # alg #2 accuracy
            all_responses_2 = MLRequest.objects.filter(parent_mlalgorithm=ab_test.parent_mlalgorithm_2, created_at__gt = ab_test.created_at, created_at__lt = date_now).count()
            correct_responses_2 = MLRequest.objects.filter(parent_mlalgorithm=ab_test.parent_mlalgorithm_2, created_at__gt = ab_test.created_at, created_at__lt = date_now, response=F('feedback')).count()
            accuracy_2 = correct_responses_2 / float(all_responses_2)
            print(all_responses_2, correct_responses_2, accuracy_2)

            # select algorithm with higher accuracy
            alg_id_1, alg_id_2 = ab_test.parent_mlalgorithm_1, ab_test.parent_mlalgorithm_2
            # swap
            if accuracy_1 < accuracy_2:
                alg_id_1, alg_id_2 = alg_id_2, alg_id_1

            status_1 = MLAlgorithmStatus(status = "production",
                            created_by=ab_test.created_by,
                            parent_mlalgorithm = alg_id_1,
                            active=True)
            status_1.save()
            deactivate_other_statues(status_1)
            # update status for second algorithm
            status_2 = MLAlgorithmStatus(status = "testing",
                            created_by=ab_test.created_by,
                            parent_mlalgorithm = alg_id_2,
                            active=True)
            status_2.save()
            deactivate_other_statues(status_2)


            summary = "Algorithm #1 accuracy: {}, Algorithm #2 accuracy: {}".format(accuracy_1, accuracy_2)
            ab_test.ended_at = date_now
            ab_test.summary = summary
            ab_test.save()

        except Exception as e:
            return Response({"status": "Error", "message": str(e)},
                            status=status.HTTP_400_BAD_REQUEST
            )
        return Response({"message": "AB Test finished.", "summary": summary})
        