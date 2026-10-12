import asyncio
from types import SimpleNamespace

import discord
import pytest

from src.pixel.cogs import welcome


class FakeBot:
    def __init__(self, auto_role_id):
        self.settings = SimpleNamespace(
            auto_role_id=auto_role_id, welcome_channel_id=1, is_prod=False
        )
        self.errors = []

    async def report_error(self, where, error):
        self.errors.append((where, error))


class FakeMember:
    def __init__(self, roles, is_bot=False, fail_with=None):
        self.bot = is_bot
        self.guild = SimpleNamespace(get_role=roles.get)
        self.given = []
        self._fail_with = fail_with

    async def add_roles(self, role, reason=None):
        if self._fail_with:
            raise self._fail_with
        self.given.append(role)


@pytest.fixture
def make_cog(monkeypatch):
    def broken_card():
        raise FileNotFoundError  # sin tarjeta: aquí solo probamos el rol

    monkeypatch.setattr(welcome, "WelcomeCard", broken_card)
    return lambda role_id: welcome.Welcome(FakeBot(role_id))


ROLE = SimpleNamespace(id=123, name="Insert Coin")


def run(cog, member):
    asyncio.run(cog._assign_role(member))


def test_gives_the_role_to_a_new_member(make_cog):
    cog, member = make_cog(123), FakeMember({123: ROLE})
    run(cog, member)
    assert member.given == [ROLE]
    assert cog.bot.errors == []


def test_does_nothing_when_no_role_is_configured(make_cog):
    cog, member = make_cog(0), FakeMember({123: ROLE})
    run(cog, member)
    assert member.given == []
    assert cog.bot.errors == []


def test_bots_do_not_get_the_role(make_cog):
    cog, member = make_cog(123), FakeMember({123: ROLE}, is_bot=True)
    run(cog, member)
    assert member.given == []


def test_reports_an_error_when_the_role_does_not_exist(make_cog):
    cog, member = make_cog(999), FakeMember({123: ROLE})
    run(cog, member)
    assert member.given == []
    assert "AUTO_ROLE_ID" in str(cog.bot.errors[0][1])


def test_reports_a_clear_error_when_discord_refuses(make_cog):
    refusal = discord.Forbidden(SimpleNamespace(status=403, reason="Forbidden"), "no")
    cog, member = make_cog(123), FakeMember({123: ROLE}, fail_with=refusal)
    run(cog, member)
    where, error = cog.bot.errors[0]
    assert where == "rol automático"
    assert "ARRIBA" in str(error)