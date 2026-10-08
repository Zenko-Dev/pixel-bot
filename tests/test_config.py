import pytest

from src.pixel.config import load_settings

ENV_COMPLETO = {
    "APP_ENV": "staging",
    "DISCORD_TOKEN": "token-falso",
    "STAGING_CHANNEL_ID": "111",
    "ERROR_CHANNEL_ID": "222",
    "WELCOME_CHANNEL_ID": "333",
}


def poner_env(monkeypatch, **cambios):
    valores = {**ENV_COMPLETO, **cambios}
    for nombre, valor in valores.items():
        monkeypatch.setenv(nombre, valor)


def test_lee_cada_variable_con_su_nombre(monkeypatch):
    poner_env(monkeypatch)
    settings = load_settings()
    assert settings.staging_channel_id == 111
    assert settings.error_channel_id == 222
    assert settings.welcome_channel_id == 333


def test_prod_se_detecta(monkeypatch):
    poner_env(monkeypatch, APP_ENV="prod")
    assert load_settings().is_prod is True


def test_staging_no_es_prod(monkeypatch):
    poner_env(monkeypatch)
    assert load_settings().is_prod is False


def test_env_invalido_falla(monkeypatch):
    poner_env(monkeypatch, APP_ENV="produccion")
    with pytest.raises(RuntimeError):
        load_settings()


def test_sin_token_falla(monkeypatch):
    poner_env(monkeypatch)
    monkeypatch.delenv("DISCORD_TOKEN")
    with pytest.raises(RuntimeError):
        load_settings()