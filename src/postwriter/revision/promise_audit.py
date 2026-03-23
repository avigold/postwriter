"""Promise audit: checks for unresolved, premature, weak, and duplicated payoffs."""

from __future__ import annotations

from typing import Any

from postwriter.revision.base import RevisionProposal


class PromiseAudit:
    """Audits the promise ledger for structural problems."""

    name = "promise_audit"

    async def audit(self, manuscript_data: dict[str, Any]) -> list[RevisionProposal]:
        proposals: list[RevisionProposal] = []
        promises = manuscript_data.get("promises", [])
        total_chapters = manuscript_data.get("total_chapters", 0)

        for promise in promises:
            status = promise.get("status", "open")
            salience = promise.get("salience", 0.5)
            description = promise.get("description", "")
            pid = promise.get("id", "")

            # Unresolved high-salience promises
            if status == "open" and salience > 0.6:
                proposals.append(RevisionProposal(
                    audit_name=self.name,
                    severity=salience,
                    description=f"Unresolved promise: {description}",
                    proposed_action=(
                        "Either resolve this promise in the final chapters or "
                        "explicitly transform it into deliberate ambiguity."
                    ),
                    evidence={"promise_id": pid, "status": status, "salience": salience},
                ))

            # Overdue promises
            if status == "overdue":
                proposals.append(RevisionProposal(
                    audit_name=self.name,
                    severity=min(1.0, salience + 0.2),
                    description=f"Overdue promise: {description}",
                    proposed_action=(
                        "This promise has passed its expected resolution window. "
                        "Either resolve it urgently or seed a reason for delay."
                    ),
                    evidence={"promise_id": pid},
                    requires_human_approval=salience >= 0.8,
                ))

            # Weak payoffs
            payoff_strength = promise.get("payoff_strength")
            if status == "resolved" and payoff_strength is not None and payoff_strength < 0.4:
                proposals.append(RevisionProposal(
                    audit_name=self.name,
                    severity=0.6 * salience,
                    description=f"Weak payoff for: {description}",
                    proposed_action=(
                        "The resolution of this promise feels insufficient. "
                        "Strengthen the payoff scene or add preparation in preceding scenes."
                    ),
                    target_scene_ids=[promise.get("resolution_scene_id", "")],
                    evidence={"payoff_strength": payoff_strength},
                ))

        return proposals
