import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path

from scripts.check_release import check_artifact, check_ui_assets, compare_manifest, file_manifest
from scripts.refresh_ui_assets import UI_ASSETS, render_ui_assets


class ReleaseConsistencyTests(unittest.TestCase):
    def make_ui(self, directory):
        root, source = Path(directory) / "site", Path(directory) / "web"
        (root / "data").mkdir(parents=True)
        (root / "details").mkdir()
        source.mkdir()
        (root / "data/latest.json").write_text(json.dumps({"dataset_version": "v1-" + "a" * 16}), encoding="utf-8")
        (root / "details/latest.json").write_text(json.dumps({"detail_version": "d1-" + "b" * 16}), encoding="utf-8")
        for name in UI_ASSETS:
            (source / name).write_bytes((name + " __VERSION__ __DETAIL_VERSION__\r\n").encode("utf-8"))
        for name, content in render_ui_assets(root, source).items():
            (root / name).write_bytes(content)
        return root, source

    def test_current_pointers_render_exact_lf_bytes_without_modifying_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            root, source = self.make_ui(directory)
            before = file_manifest(root)
            check_ui_assets(root, source)
            self.assertEqual(file_manifest(root), before)
            self.assertEqual((root / "index.html").read_bytes(), b"index.html v1-aaaaaaaaaaaaaaaa d1-bbbbbbbbbbbbbbbb\n")

    def test_source_change_is_rejected_until_candidate_is_refreshed(self):
        with tempfile.TemporaryDirectory() as directory:
            root, source = self.make_ui(directory)
            before = file_manifest(root)
            (source / "app.mjs").write_text("changed app\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "differs from web source: app.mjs"):
                check_ui_assets(root, source)
            self.assertEqual(file_manifest(root), before)
            for name, content in render_ui_assets(root, source).items():
                (root / name).write_bytes(content)
            check_ui_assets(root, source)

    def test_pointer_only_change_and_crlf_drift_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root, source = self.make_ui(directory)
            (root / "details/latest.json").write_text(json.dumps({"detail_version": "d1-" + "c" * 16}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "differs from web source: index.html"):
                check_ui_assets(root, source)
            for name, content in render_ui_assets(root, source).items():
                (root / name).write_bytes(content)
            check_ui_assets(root, source)
            path = root / "style.css"
            path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
            with self.assertRaisesRegex(ValueError, "differs from web source: style.css"):
                check_ui_assets(root, source)

    def test_full_tree_manifest_rejects_added_removed_and_modified_data(self):
        for change in ("add", "remove", "modify"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                root, _ = self.make_ui(directory)
                bundle = root / "data/v1-aaaaaaaaaaaaaaaa"
                bundle.mkdir()
                data = bundle / "cards.json"
                data.write_bytes(b"original data")
                before = file_manifest(root)
                compare_manifest(file_manifest(root), before)
                if change == "add":
                    (bundle / "unexpected.txt").write_bytes(b"new file")
                elif change == "remove":
                    data.unlink()
                else:
                    data.write_bytes(b"changed data")
                with self.assertRaisesRegex(ValueError, "Release tree changed during verification: data/v1-"):
                    compare_manifest(file_manifest(root), before)

    def test_actual_pages_archive_matches_every_tested_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root, _ = self.make_ui(directory)
            (root / ".nojekyll").write_bytes(b"")
            expected = file_manifest(root)
            path = Path(directory) / "artifact.tar"
            with tarfile.open(path, "w") as archive:
                archive.add(root, arcname=".")
            check_artifact(path, expected)

    def test_actual_pages_archive_rejects_omissions_changes_extras_and_unsafe_entries(self):
        for change in ("missing", "changed", "extra", "duplicate", "symlink", "escape"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                root, _ = self.make_ui(directory)
                (root / ".nojekyll").write_bytes(b"")
                expected = file_manifest(root)
                path = Path(directory) / "artifact.tar"
                with tarfile.open(path, "w") as archive:
                    for item in sorted(root.rglob("*")):
                        if item.is_file() and not (change == "missing" and item.name == ".nojekyll"):
                            data = b"different" if change == "changed" and item.name == "app.mjs" else item.read_bytes()
                            member = tarfile.TarInfo("./" + item.relative_to(root).as_posix())
                            member.size = len(data)
                            archive.addfile(member, io.BytesIO(data))
                    if change in ("extra", "duplicate", "escape"):
                        member = tarfile.TarInfo({"extra": "extra.txt", "duplicate": "app.mjs", "escape": "../escape.txt"}[change])
                        archive.addfile(member, io.BytesIO())
                    elif change == "symlink":
                        member = tarfile.TarInfo("linked.mjs")
                        member.type = tarfile.SYMTYPE
                        member.linkname = "app.mjs"
                        archive.addfile(member)
                with self.assertRaises(ValueError):
                    check_artifact(path, expected)

    def test_manifest_rejects_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root, _ = self.make_ui(directory)
            try:
                (root / "linked.mjs").symlink_to(root / "app.mjs")
            except OSError as error:
                self.skipTest(f"Symlinks unavailable: {error}")
            with self.assertRaisesRegex(ValueError, "symlink in site"):
                file_manifest(root)


if __name__ == "__main__":
    unittest.main()
