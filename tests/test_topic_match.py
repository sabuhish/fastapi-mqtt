import pytest

from fastapi_mqtt.fastmqtt import FastMQTT


class TestTopicMatching:
    matching = [
        # pattern, topic, match
        ("sport/tennis/player1", "sport/tennis/player1", True),
        # wildcard "#"
        ("sport/tennis/#", "sport/tennis/player1", True),
        ("sport/tennis/#", "sport/tennis", True),
        ("sport/#", "sport/tennis/player1", True),
        ("#", "sport/tennis/player1", True),
        # wildcard "+"
        ("+", "anything", True),
        ("+/+", "/anything", True),
        ("+/tennis", "anything/tennis", True),
        ("sport/+/player1", "sport/tennis/player1", True),
        ("+/tennis/player1", "sport/tennis/player1", True),
        ("sport/tennis/+", "sport/tennis/player1", True),
        # both wildcards
        ("sport/+/#", "sport/tennis/player1", True),
        ("+/tennis/#", "sport/tennis/player1", True),
        # leading $ and /
        ("$SYS/state", "$SYS/state", True),
        ("$SYS/#", "$SYS/state", True),
        ("/foo/bar", "/foo/bar", True),
        ("/#", "/foo/bar", True),
        # non-matching
        ("sport/tennis/player1", "sport/tennis/player1/ranking", False),
        ("sport/tennis/player1", "sport/tennis/player2", False),
        ("sport/tennis/player1", "sport/tennis", False),
        ("sport/tennis/+", "sport/tennis", False),
        ("sport/tennis/+", "sport/tennis/player1/ranking", False),
        ("sport/+/player1", "sport/tennis/player2", False),
        ("+", "/anything", False),
        ("+/tennis", "anything/golf", False),
        ("#", "$SYS/anything", False),
        ("+/monitor/Clients", "$SYS/monitor/Clients", False),

        # According to MQTT5.0 item 4.8.2
        ("$share/myshare/Clients/anything", "Clients/anything", True),
        ("$share/myshare/Clients/+", "Clients/anything", True),
        ("$share/myshare//finance", "/finance", True),
        ("$share/myshare//finance", "finance", False),
    ]

    @pytest.mark.parametrize(argnames=["pattern", "topic", "match"], argvalues=matching)
    def test_matching(self, topic: str, pattern: str, match: bool) -> None:
        assert match == FastMQTT.match(topic=topic, template=pattern)
