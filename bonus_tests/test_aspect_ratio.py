"""Test bổ sung cho bonus; không sửa test gốc được bảo vệ của đề."""
import hashlib
import json

import pytest
from PIL import Image

from pipeline.bonus import main
from pipeline.checks import aspect_ratio
from pipeline.common import Dataset


@pytest.fixture
def cfg():
    return {"classes": ["car", "person", "truck", "bus"], "aspect_ratio": {"max_ratio": 10}}


@pytest.fixture
def make_ds(tmp_path, cfg):
    def make(lines=(), size=(400, 200), suffix=".jpg"):
        root = tmp_path / "ds"
        (root / "images").mkdir(parents=True, exist_ok=True)
        (root / "labels").mkdir(exist_ok=True)
        Image.new("RGB", size, "white").save(root / "images" / ("sample" + suffix))
        (root / "labels/sample.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        return Dataset(root, cfg["classes"])
    return make


def test_pixel_dimensions_not_normalized_ratio(make_ds, cfg):
    ds = make_ds(["0 .5 .5 .4 .04"])
    issue, = aspect_ratio.run(ds, cfg)
    assert (issue.code, issue.severity, issue.image, issue.line) == ("BOX_EXTREME_ASPECT", "warn", "sample", 1)
    assert issue.extra == {"aspect_ratio": 20, "width_px": 160, "height_px": 8, "max_ratio": 10}


def test_normalized_extreme_can_be_normal_in_pixels(make_ds, cfg):
    ds = make_ds(["1 .5 .5 .02 .4"], size=(1000, 100))
    assert aspect_ratio.run(ds, cfg) == []  # 20 x 40 px, ratio 2


@pytest.mark.parametrize("box", [".4 .04", ".04 .4"])
def test_exact_boundary_is_allowed(make_ds, cfg, box):
    assert aspect_ratio.run(make_ds([f"0 .5 .5 {box}"], size=(200, 200)), cfg) == []


def test_vertical_box_and_blank_lines_keep_original_line(make_ds, cfg):
    ds = make_ds(["", "garbage", "1 .5 .5 .01 .8"])
    issue, = aspect_ratio.run(ds, cfg)
    assert issue.line == 3 and issue.extra["aspect_ratio"] == 40


def test_threshold_is_configurable(make_ds, cfg):
    ds = make_ds(["0 .5 .5 .4 .04"])
    cfg["aspect_ratio"]["max_ratio"] = 25
    assert aspect_ratio.run(ds, cfg) == []
    cfg["aspect_ratio"]["max_ratio"] = 15
    assert len(aspect_ratio.run(ds, cfg)) == 1


def test_bad_labels_do_not_crash_or_become_geometry_warnings(make_ds, cfg):
    ds = make_ds(["garbage", "1 nan .5 .01 .8", "inf .5 .5 .01 .8", "93 .5 .5 .01 .8",
                  "0 .5 .5 0 .8", "0 .5 .5 -.01 .8", "0 .5 .5 1e308 .8"])
    assert aspect_ratio.run(ds, cfg) == []


def test_missing_empty_or_orphan_labels(make_ds, cfg):
    ds = make_ds()
    assert aspect_ratio.run(ds, cfg) == []
    ds.label_path("sample").unlink()
    ds.label_path("orphan").write_text("0 .5 .5 .01 .8\n")
    assert aspect_ratio.run(ds, cfg) == []


def test_unreadable_image_is_skipped(make_ds, cfg):
    ds = make_ds(["0 .5 .5 .01 .8"])
    ds.image_files()[0].write_bytes(b"broken image")
    assert aspect_ratio.run(ds, cfg) == []


def test_uppercase_image_extension(make_ds, cfg):
    ds = make_ds(["0 .5 .5 .4 .04"], suffix=".JPG")
    assert len(aspect_ratio.run(ds, cfg)) == 1


@pytest.mark.parametrize("limit", [0, 1, -2, float("nan"), float("inf")])
def test_invalid_threshold_fails_explicitly(make_ds, cfg, limit):
    cfg["aspect_ratio"]["max_ratio"] = limit
    with pytest.raises(ValueError, match="max_ratio"):
        aspect_ratio.run(make_ds(), cfg)


def test_runner_is_readonly_and_repeatable(make_ds, tmp_path):
    ds = make_ds(["0 .5 .5 .4 .04"])
    before = {p: hashlib.sha1(p.read_bytes()).hexdigest() for p in ds.root.rglob("*") if p.is_file()}
    outputs = []
    for tag in ("first", "second"):
        out = tmp_path / tag
        assert main(["--dataset", str(ds.root), "--out", str(out)]) == 0
        outputs.append({p.name: p.read_bytes() for p in out.iterdir()})
    assert outputs[0] == outputs[1]
    assert before == {p: hashlib.sha1(p.read_bytes()).hexdigest() for p in before}
    summary = json.loads(outputs[0]["summary.json"])
    assert (summary["n_images"], summary["n_issues"], summary["n_warn_images"]) == (1, 1, 1)


def test_runner_refuses_output_inside_dataset(make_ds):
    ds = make_ds()
    with pytest.raises(SystemExit):
        main(["--dataset", str(ds.root), "--out", str(ds.root / "reports")])


def test_runner_rejects_missing_dataset(tmp_path):
    with pytest.raises(SystemExit):
        main(["--dataset", str(tmp_path / "missing")])
