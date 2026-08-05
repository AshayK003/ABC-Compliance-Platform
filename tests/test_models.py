from __future__ import annotations

import pytest


class TestModelTopLevel:
    def test_committee_models_are_module_level(self):
        """Committee models must be importable at module level, not nested.

        Regression: these were accidentally indented inside Notification,
        making `from src.models.base import Committee` raise ImportError.
        """
        from src.models.base import (
            Committee,
            CommitteeDocument,
            CommitteeMember,
            Decision,
            Meeting,
            MeetingAttendee,
            Notification,
            Vote,
        )

        # Top-level classes are not attributes of Notification.
        assert not hasattr(Notification, "Committee")
        assert not hasattr(Notification, "Meeting")

        # Class names resolve at module scope.
        assert Committee.__name__ == "Committee"
        assert Meeting.__name__ == "Meeting"
        assert Decision.__name__ == "Decision"
        assert Vote.__name__ == "Vote"
        assert CommitteeMember.__name__ == "CommitteeMember"
        assert MeetingAttendee.__name__ == "MeetingAttendee"
        assert CommitteeDocument.__name__ == "CommitteeDocument"

    def test_committee_relationships_are_wired(self):
        from src.models.base import Committee, Meeting

        assert hasattr(Committee, "meetings")
        assert hasattr(Meeting, "committee")
