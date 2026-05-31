import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent
INSTALL_SCRIPT = REPO_ROOT / "install.py"

pytestmark = pytest.mark.skipif(
    not INSTALL_SCRIPT.exists(),
    reason="install.py is not present yet; CLI tests are ready for implementation.",
)


def _run_install(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(INSTALL_SCRIPT), *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _prepare_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    project.mkdir(parents=True, exist_ok=True)

    frame_data = {
        "projectDirectory": "",
        "tagList": [],
        "directoryList": [
            {
                "name": "alpha",
                "tagList": [{"kind": "location", "name": "A"}],
                "directoryList": [],
            },
            {
                "name": "beta",
                "tagList": [{"kind": "location", "name": "B"}],
                "directoryList": [
                    {
                        "name": "delta",
                        "tagList": [{"kind": "location", "name": "D"}],
                        "directoryList": [],
                    }
                ],
            },
        ],
        "dataGroupList": ["exampleGroup1", "exampleGroup2", "exampleGroup3"],
    }
    _write_json(project / "frameData.config.json", frame_data)

    _make_group(
        project,
        "exampleGroup1",
        [
            ("file11.md", "A", "force", "group1-a"),
            ("file12.md", "A", "force", "group1-b"),
            ("file13.md", "A", "force", "group1-c"),
        ],
    )
    _make_group(
        project,
        "exampleGroup2",
        [
            ("file21.md", "B", "force", "group2-a"),
            ("file22.md", "B", "force", "group2-b"),
            ("file23.md", "B", "force", "group2-c"),
        ],
    )
    _make_group(
        project,
        "exampleGroup3",
        [
            ("file31.md", "A", "force", "group3-a"),
            ("file32.md", "B", "force", "group3-b"),
            ("file33.md", "D", "force", "group3-c"),
        ],
    )
    return project


def _make_group(
    project: Path,
    group_name: str,
    rows: list[tuple[str, str, str, str]],
) -> None:
    group_dir = project / group_name
    group_dir.mkdir(parents=True, exist_ok=True)

    file_list = []
    for file_name, tag_name, write_policy, contents in rows:
        (group_dir / file_name).write_text(contents, encoding="utf-8")
        file_list.append(
            {
                "name": file_name,
                "tag": {"kind": "location", "name": tag_name},
                "writePolicy": write_policy,
            }
        )

    _write_json(group_dir / f"{group_name}.dataGroup.json", {"fileList": file_list})


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    return _prepare_project(tmp_path)


def test_install_frame_creates_nested_directories(project_dir: Path) -> None:
    result = _run_install(["frame"], cwd=project_dir)
    target_root = project_dir.parent

    assert result.returncode == 0, result.stderr
    assert (target_root / "alpha").is_dir()
    assert (target_root / "beta").is_dir()
    assert (target_root / "beta" / "delta").is_dir()


def test_install_frame_second_run_is_non_fatal(project_dir: Path) -> None:
    first = _run_install(["frame"], cwd=project_dir)
    second = _run_install(["frame"], cwd=project_dir)

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr


def test_install_datagroup_copies_files_to_tagged_directories(project_dir: Path) -> None:
    frame_result = _run_install(["frame"], cwd=project_dir)
    install_result = _run_install(["datagroup", "exampleGroup3"], cwd=project_dir)
    target_root = project_dir.parent

    assert frame_result.returncode == 0, frame_result.stderr
    assert install_result.returncode == 0, install_result.stderr
    assert (target_root / "alpha" / "file31.md").read_text(encoding="utf-8") == "group3-a"
    assert (target_root / "beta" / "file32.md").read_text(encoding="utf-8") == "group3-b"
    assert (target_root / "beta" / "delta" / "file33.md").read_text(encoding="utf-8") == "group3-c"


def test_uninstall_datagroup_removes_only_that_datagroup(project_dir: Path) -> None:
    assert _run_install(["frame"], cwd=project_dir).returncode == 0
    assert _run_install(["datagroup", "exampleGroup1"], cwd=project_dir).returncode == 0
    assert _run_install(["datagroup", "exampleGroup3"], cwd=project_dir).returncode == 0
    target_root = project_dir.parent

    result = _run_install(["datagroup", "--uninstall", "exampleGroup3"], cwd=project_dir)

    assert result.returncode == 0, result.stderr
    assert not (target_root / "alpha" / "file31.md").exists()
    assert not (target_root / "beta" / "file32.md").exists()
    assert not (target_root / "beta" / "delta" / "file33.md").exists()
    assert (target_root / "alpha" / "file11.md").exists()
    assert (target_root / "alpha" / "file12.md").exists()
    assert (target_root / "alpha" / "file13.md").exists()


def test_install_datagroup_rejects_unknown_group(project_dir: Path) -> None:
    assert _run_install(["frame"], cwd=project_dir).returncode == 0

    result = _run_install(["datagroup", "doesNotExist"], cwd=project_dir)

    assert result.returncode != 0


def test_install_datagroup_fails_when_tag_is_unresolved(project_dir: Path) -> None:
    bad_group = project_dir / "badGroup"
    bad_group.mkdir(parents=True, exist_ok=True)
    (bad_group / "bad.md").write_text("bad", encoding="utf-8")
    _write_json(
        bad_group / "badGroup.dataGroup.json",
        {
            "fileList": [
                {
                    "name": "bad.md",
                    "tag": {"kind": "location", "name": "MISSING"},
                    "writePolicy": "force",
                }
            ]
        },
    )

    frame_data = json.loads((project_dir / "frameData.config.json").read_text(encoding="utf-8"))
    frame_data["dataGroupList"].append("badGroup")
    _write_json(project_dir / "frameData.config.json", frame_data)

    assert _run_install(["frame"], cwd=project_dir).returncode == 0
    result = _run_install(["datagroup", "badGroup"], cwd=project_dir)

    assert result.returncode != 0


def test_install_datagroups_can_coexist(project_dir: Path) -> None:
    assert _run_install(["frame"], cwd=project_dir).returncode == 0

    first = _run_install(["datagroup", "exampleGroup1"], cwd=project_dir)
    second = _run_install(["datagroup", "exampleGroup2"], cwd=project_dir)

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr

    target_root = project_dir.parent
    assert (target_root / "alpha" / "file11.md").exists()
    assert (target_root / "alpha" / "file12.md").exists()
    assert (target_root / "alpha" / "file13.md").exists()
    assert (target_root / "beta" / "file21.md").exists()
    assert (target_root / "beta" / "file22.md").exists()
    assert (target_root / "beta" / "file23.md").exists()


def test_uninstall_frame_skips_non_empty_directories(project_dir: Path) -> None:
    assert _run_install(["frame"], cwd=project_dir).returncode == 0
    assert _run_install(["datagroup", "exampleGroup1"], cwd=project_dir).returncode == 0
    target_root = project_dir.parent

    result = _run_install(["frame", "--uninstall"], cwd=project_dir)

    assert result.returncode != 0
    assert (target_root / "alpha").exists()
    assert (target_root / "beta").exists()


def test_write_policy_copy_creates_tmp_file(project_dir: Path) -> None:
    copy_group = project_dir / "copyGroup"
    copy_group.mkdir(parents=True, exist_ok=True)
    (copy_group / "copy-me.md").write_text("source", encoding="utf-8")
    _write_json(
        copy_group / "copyGroup.dataGroup.json",
        {
            "fileList": [
                {
                    "name": "copy-me.md",
                    "tag": {"kind": "location", "name": "A"},
                    "writePolicy": "copy",
                }
            ]
        },
    )

    frame_data = json.loads((project_dir / "frameData.config.json").read_text(encoding="utf-8"))
    frame_data["dataGroupList"].append("copyGroup")
    _write_json(project_dir / "frameData.config.json", frame_data)

    assert _run_install(["frame"], cwd=project_dir).returncode == 0
    target_root = project_dir.parent

    destination = target_root / "alpha" / "copy-me.md"
    destination.write_text("existing", encoding="utf-8")

    result = _run_install(["datagroup", "copyGroup"], cwd=project_dir)

    assert result.returncode == 0, result.stderr
    tmp_candidates = sorted((target_root / "alpha").glob("copy-me*.tmp"))
    assert tmp_candidates, "Expected at least one .tmp copy file to be created"


def test_write_policy_skip_does_not_overwrite_existing_file(project_dir: Path) -> None:
    skip_group = project_dir / "skipGroup"
    skip_group.mkdir(parents=True, exist_ok=True)
    (skip_group / "skip-me.md").write_text("source", encoding="utf-8")
    _write_json(
        skip_group / "skipGroup.dataGroup.json",
        {
            "fileList": [
                {
                    "name": "skip-me.md",
                    "tag": {"kind": "location", "name": "A"},
                    "writePolicy": "skip",
                }
            ]
        },
    )

    frame_data = json.loads((project_dir / "frameData.config.json").read_text(encoding="utf-8"))
    frame_data["dataGroupList"].append("skipGroup")
    _write_json(project_dir / "frameData.config.json", frame_data)

    assert _run_install(["frame"], cwd=project_dir).returncode == 0
    target_root = project_dir.parent

    destination = target_root / "alpha" / "skip-me.md"
    destination.write_text("existing", encoding="utf-8")

    result = _run_install(["datagroup", "skipGroup"], cwd=project_dir)

    assert result.returncode == 0, result.stderr
    assert destination.read_text(encoding="utf-8") == "existing"


def test_frame_config_missing_file_fails(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir(parents=True, exist_ok=True)

    result = _run_install(["frame"], cwd=project)

    assert result.returncode != 0


def test_datagroup_config_missing_file_fails(project_dir: Path) -> None:
    assert _run_install(["frame"], cwd=project_dir).returncode == 0

    shutil.rmtree(project_dir / "exampleGroup1")
    result = _run_install(["datagroup", "exampleGroup1"], cwd=project_dir)

    assert result.returncode != 0
