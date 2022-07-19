from rest_framework.mixins import CreateModelMixin, DestroyModelMixin
from rest_framework.viewsets import GenericViewSet


class CreateDeleteMixins(CreateModelMixin, DestroyModelMixin, GenericViewSet):
    pass
