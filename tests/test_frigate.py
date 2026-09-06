# SPDX-License-Identifier: Apache-2.0
from frigatespotter.frigate import _extract_track_labels


def test_extract_track_labels_list():
    assert _extract_track_labels({"track": ["person", "dog"]}) == ["dog", "person"]


def test_extract_track_labels_dict():
    assert _extract_track_labels({"track": {"dog": {}, "person": {}}}) == ["dog", "person"]


def test_extract_track_labels_missing():
    assert _extract_track_labels(None) == []
