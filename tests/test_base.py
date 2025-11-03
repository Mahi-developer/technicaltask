import pytest
from django.urls import reverse
from conftest import TestBase


@pytest.mark.asyncio
class TestPing(TestBase):

    def setUp(self):
        super().setUp()
        self.url = reverse("ping")
    
    async def test_ping(self):
        """Testing Ping Endpoint
        """
        response = await self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "Hey, There!!")
