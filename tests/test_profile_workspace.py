from pathlib import Path

import pytest

from app.profile_export import load_profile, save_profile, set_profile_workspace


ROOT = Path(__file__).resolve().parents[1]


def make_base(tmp_path: Path) -> Path:
    base_dir = tmp_path / 'vpe'
    (base_dir / 'schemas').mkdir(parents=True)
    (base_dir / 'schemas' / 'profile.yaml').write_text(
        (ROOT / 'schemas' / 'profile.yaml').read_text(encoding='utf-8'),
        encoding='utf-8',
    )
    return base_dir


def test_default_profile_uses_ignored_workspace(tmp_path, monkeypatch):
    monkeypatch.delenv('VPE_PROFILE_WORKSPACE', raising=False)
    base_dir = make_base(tmp_path)

    schema = load_profile(base_dir)
    schema['name'] = 'edited_profile'
    save_profile(base_dir, schema)

    workspace_profile = base_dir / '.vpe-workspace' / 'profiles' / 'profile.yaml'
    assert workspace_profile.exists()
    assert 'edited_profile' in workspace_profile.read_text(encoding='utf-8')
    assert 'edited_profile' not in (base_dir / 'schemas' / 'profile.yaml').read_text(encoding='utf-8')


def test_set_profile_workspace_uses_requested_directory(tmp_path, monkeypatch):
    monkeypatch.delenv('VPE_PROFILE_WORKSPACE', raising=False)
    base_dir = make_base(tmp_path)
    target_dir = tmp_path / 'chosen-profile-store'

    workspace, schema = set_profile_workspace(base_dir, str(target_dir))

    assert workspace['directory'] == str(target_dir.resolve())
    assert workspace['schema_path'] == str(target_dir.resolve() / 'profile.yaml')
    assert schema['name'] == 'construct_dcat_profile'
    assert (target_dir / 'profile.yaml').exists()


def test_workspace_cannot_be_inside_versioned_schema_seeds(tmp_path, monkeypatch):
    monkeypatch.delenv('VPE_PROFILE_WORKSPACE', raising=False)
    base_dir = make_base(tmp_path)

    with pytest.raises(ValueError):
        set_profile_workspace(base_dir, str(base_dir / 'schemas'))
