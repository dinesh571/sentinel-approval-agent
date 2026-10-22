"""Approval decisions are explicit, action-bound, and issued only here."""

from dataclasses import dataclass, field

from actions import Action, action_fingerprint

_ISSUER = object()


@dataclass(frozen=True)
class ApprovalDecision:
    approved: bool
    action_fingerprint: str
    reason: str
    _issuer: object = field(repr=False, compare=False)

    def is_valid_for(self, action: Action) -> bool:
        return (
            self._issuer is _ISSUER
            and self.approved
            and self.action_fingerprint == action_fingerprint(action)
        )


def request_approval(action: Action, response: str) -> ApprovalDecision:
    fingerprint = action_fingerprint(action)
    normalized = response.strip().casefold() if isinstance(response, str) else ""
    if normalized == "yes":
        return ApprovalDecision(True, fingerprint, "Approved explicitly.", _ISSUER)
    if normalized == "no":
        return ApprovalDecision(False, fingerprint, "Rejected by the user.", _ISSUER)
    return ApprovalDecision(
        False,
        fingerprint,
        "Approval was not granted; the response was not exactly yes or no.",
        _ISSUER,
    )
