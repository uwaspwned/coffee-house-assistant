from coffee_assistant.assistant import _to_content
from coffee_assistant.database import StoredMessage


def test_to_content_maps_roles_for_gemini() -> None:
    user_content = _to_content(StoredMessage(role="user", content="hello"))
    assistant_content = _to_content(StoredMessage(role="assistant", content="hi"))

    assert user_content.role == "user"
    assert assistant_content.role == "model"
    assert user_content.parts[0].text == "hello"
    assert assistant_content.parts[0].text == "hi"
