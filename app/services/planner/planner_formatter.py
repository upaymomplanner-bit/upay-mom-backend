from msgraph.generated.models.planner_checklist_items import PlannerChecklistItems
from schemas.transcript import CheckListItem
import uuid


class PlannerFormatter:
    @staticmethod
    def format_checklist_items(
        checklist_items: list[CheckListItem],
    ) -> PlannerChecklistItems:
        """
        Format checklist items for Planner API

        Args:
            checklist_items: List of checklist items extracted from the transcript

        Returns:
            dict[str]: Formatted checklist items suitable for Planner API
        """

        additional_data: dict[str, dict] = {}
        for item in checklist_items:
            item_id = str(uuid.uuid4())
            additional_data[item_id] = {
                "title": item.title,
                "isChecked": False,
                "@odata_type": "microsoft.graph.plannerChecklistItem",
            }

        return PlannerChecklistItems(additional_data=additional_data)
