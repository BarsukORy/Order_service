from uuid import uuid4
from business_logic.domain.services import AbstractIdGenerator


class DjangoUniqueIdGenerator(AbstractIdGenerator):

    def __init__(self, django_model) -> None:
        self.django_model = django_model

    def generate_id(self) -> str:
        while True:
            domain_id = str(uuid4())

            if not self.django_model.objects.filter(domain_id=domain_id).exists():
                return domain_id