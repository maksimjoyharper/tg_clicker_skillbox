from locust import HttpUser, task, between


class LoadTestUser(HttpUser):
    # Задержка между запросами от одного пользователя
    wait_time = between(1, 3)

    @task
    def test_player_info(self):
        # Тестирование эндпоинта player-info
        self.client.get("/api/player-info/1/name/")
