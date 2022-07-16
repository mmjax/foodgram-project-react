from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, CreateModelMixin, DestroyModelMixin
from rest_framework.viewsets import GenericViewSet


class ListRetriveViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    pass


class CreateDeleteSerializer(CreateModelMixin, DestroyModelMixin):
    pass