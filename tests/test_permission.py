from typing import Optional

from nonebug import App
import pytest

from nonebot.exception import SkippedException
from nonebot.permission import (
    MESSAGE,
    METAEVENT,
    NOTICE,
    REQUEST,
    SUPERUSER,
    USER,
    Message,
    MetaEvent,
    Notice,
    Permission,
    Request,
    SuperUser,
    User,
)
from utils import make_fake_event


@pytest.mark.anyio
async def test_permission(app: App):
    async def falsy():
        return False

    async def truthy():
        return True

    async def skipped() -> bool:
        raise SkippedException

    def _is_eq(a: Permission, b: Permission) -> bool:
        return {d.call for d in a.checkers} == {d.call for d in b.checkers}

    assert _is_eq(Permission(truthy) | None, Permission(truthy))
    assert _is_eq(Permission(truthy) | falsy, Permission(truthy, falsy))
    assert _is_eq(Permission(truthy) | Permission(falsy), Permission(truthy, falsy))

    assert _is_eq(None | Permission(truthy), Permission(truthy))
    assert _is_eq(truthy | Permission(falsy), Permission(truthy, falsy))

    event = make_fake_event()()

    async with app.test_api() as ctx:
        bot = ctx.create_bot()
        assert await Permission(falsy)(bot, event) is False
        assert await Permission(truthy)(bot, event) is True
        assert await Permission(skipped)(bot, event) is False
        assert await Permission(truthy, falsy)(bot, event) is True
        assert await Permission(truthy, skipped)(bot, event) is True


@pytest.mark.anyio
@pytest.mark.parametrize(("type", "expected"), [("message", True), ("notice", False)])
async def test_message(type: str, expected: bool):
    dependent = next(iter(MESSAGE.checkers))
    checker = dependent.call

    assert isinstance(checker, Message)

    event = make_fake_event(_type=type)()
    assert await dependent(event=event) == expected


@pytest.mark.anyio
@pytest.mark.parametrize(("type", "expected"), [("message", False), ("notice", True)])
async def test_notice(type: str, expected: bool):
    dependent = next(iter(NOTICE.checkers))
    checker = dependent.call

    assert isinstance(checker, Notice)

    event = make_fake_event(_type=type)()
    assert await dependent(event=event) == expected


@pytest.mark.anyio
@pytest.mark.parametrize(("type", "expected"), [("message", False), ("request", True)])
async def test_request(type: str, expected: bool):
    dependent = next(iter(REQUEST.checkers))
    checker = dependent.call

    assert isinstance(checker, Request)

    event = make_fake_event(_type=type)()
    assert await dependent(event=event) == expected


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("type", "expected"), [("message", False), ("meta_event", True)]
)
async def test_metaevent(type: str, expected: bool):
    dependent = next(iter(METAEVENT.checkers))
    checker = dependent.call

    assert isinstance(checker, MetaEvent)

    event = make_fake_event(_type=type)()
    assert await dependent(event=event) == expected


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("type", "user_id", "expected"),
    [
        ("message", "test", True),
        ("message", "foo", False),
        ("message", "faketest", True),
        ("message", None, False),
        ("notice", "test", True),
    ],
)
async def test_superuser(app: App, type: str, user_id: str, expected: bool):
    dependent = next(iter(SUPERUSER.checkers))
    checker = dependent.call

    assert isinstance(checker, SuperUser)

    event = make_fake_event(_type=type, _user_id=user_id)()

    async with app.test_api() as ctx:
        bot = ctx.create_bot()
        assert await dependent(bot=bot, event=event) == expected


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("session_ids", "session_id", "expected"),
    [
        (("user", "foo"), "user", True),
        (("user", "foo"), "bar", False),
        (("user", "foo"), None, False),
    ],
)
async def test_user(
    app: App, session_ids: tuple[str, ...], session_id: Optional[str], expected: bool
):
    dependent = next(iter(USER(*session_ids).checkers))
    checker = dependent.call

    assert isinstance(checker, User)

    event = make_fake_event(_session_id=session_id)()

    async with app.test_api() as ctx:
        bot = ctx.create_bot()
        assert await dependent(bot=bot, event=event) == expected
