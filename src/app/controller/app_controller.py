"""Controlador principal para la interfaz de Nebula Finance."""

from __future__ import annotations

from collections import OrderedDict
from types import SimpleNamespace
from typing import Any, Dict, Iterable, List, Tuple

from backend.app.controller.app_controller import AppController as BackendAppController


class AppController(BackendAppController):
    """Extiende la lógica del backend para alimentar la interfaz gráfica."""

    def __init__(self, view=None):
        super().__init__(view=view)
        self.view = view

    # ------------------------------------------------------------------
    # Dashboard helpers
    # ------------------------------------------------------------------
    def update_dashboard(self, *_: Any) -> None:
        """Obtiene los datos y actualiza la vista del dashboard."""
        if not self.view or not hasattr(self.view, "dashboard_page"):
            return

        dashboard = self.view.dashboard_page
        filters = dashboard.get_selected_filters()

        year = filters.get("year")
        months = filters.get("months", [])
        chart_range = filters.get("chart_range", "6m")

        data = super().get_dashboard_data(year, months)

        self._update_dashboard_kpis(dashboard, data.get("kpis", {}))
        self._update_dashboard_net_worth(dashboard, data.get("net_worth_chart", {}), chart_range)
        self._update_dashboard_cash_flow(dashboard, data.get("cash_flow_chart", {}), chart_range)
        self._update_dashboard_goals(dashboard, data.get("goals_summary", []))
        self._update_dashboard_accounts(dashboard, data.get("accounts_summary", []))
        self._update_dashboard_budget_cards(dashboard, data.get("budget_vs_real", {}))
        dashboard.update_budget_rule_chart(data.get("budget_rules", []))

        expense_distribution = data.get("expense_distribution", {})
        dashboard.update_expense_dist_chart(
            expense_distribution.get("categories", []),
            expense_distribution.get("amounts", []),
        )

        expense_type = data.get("expense_type_breakdown", {})
        dashboard.update_expense_type_chart(
            expense_type.get("labels", []),
            expense_type.get("values", []),
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _update_dashboard_kpis(self, dashboard, kpis: Dict[str, Any]) -> None:
        income = float(kpis.get("income", 0.0))
        expense = float(kpis.get("expense", 0.0))
        net_flow = float(kpis.get("net", income - expense))
        income_comp = kpis.get("income_comparison")
        expense_comp = kpis.get("expense_comparison")

        dashboard.update_kpis(income, expense, net_flow, income_comp, expense_comp)

    def _update_dashboard_net_worth(self, dashboard, payload: Dict[str, Any], chart_range: str) -> None:
        dates = payload.get("dates", [])
        values = payload.get("values", [])

        limit = self._resolve_chart_window(chart_range, len(dates))
        if limit:
            dates = dates[-limit:]
            values = values[-limit:]

        dashboard.update_net_worth_chart(dates, values)

    def _update_dashboard_cash_flow(self, dashboard, payload: Dict[str, Any], chart_range: str) -> None:
        months, income_series, expense_series = self._normalize_cash_flow_payload(payload)
        limit = self._resolve_chart_window(chart_range, len(months))
        if limit:
            months = months[-limit:]
            income_series = income_series[-limit:]
            expense_series = expense_series[-limit:]

        dashboard.update_cash_flow_chart(months, income_series, expense_series)

    def _update_dashboard_goals(self, dashboard, goals_payload: Iterable[Dict[str, Any]]) -> None:
        normalized = []
        for goal in goals_payload:
            normalized.append(
                {
                    "name": goal.get("name", "Meta"),
                    "current": float(goal.get("current", goal.get("current_amount", 0.0))),
                    "target": float(goal.get("target", goal.get("target_amount", 0.0))),
                }
            )
        dashboard.update_main_goals(normalized)

    def _update_dashboard_accounts(self, dashboard, accounts_payload: Iterable[Dict[str, Any]]) -> None:
        accounts = [SimpleNamespace(**account) for account in accounts_payload]
        dashboard.update_accounts_card(accounts)

    def _update_dashboard_budget_cards(self, dashboard, payload: Dict[str, Dict[str, float]]) -> None:
        income_payload = payload.get("income", {"budgeted_amount": 0.0, "real_amount": 0.0})
        expense_payload = payload.get("expense", {"budgeted_amount": 0.0, "real_amount": 0.0})

        dashboard.update_budget_vs_real_cards(income_payload, expense_payload)

    def _normalize_cash_flow_payload(self, payload: Dict[str, Any]) -> Tuple[List[str], List[float], List[float]]:
        if not payload:
            return [], [], []

        if "months" in payload:
            months = list(payload.get("months", []))
            income_series = [float(value) for value in payload.get("income", [])]
            expense_series = [float(value) for value in payload.get("expenses", [])]
            return months, income_series, expense_series

        ordered: "OrderedDict[str, Dict[str, float]]" = OrderedDict(sorted(payload.items()))
        months = list(ordered.keys())
        income_series = [float(data.get("income", 0.0)) for data in ordered.values()]
        expense_series = [float(data.get("expense", 0.0)) for data in ordered.values()]
        return months, income_series, expense_series

    @staticmethod
    def _resolve_chart_window(chart_range: str, available: int) -> int:
        mapping = {
            "3m": 3,
            "6m": 6,
            "12m": 12,
            "ytd": available,
            "all": available,
        }
        requested = mapping.get(chart_range, 6)
        if available <= 0:
            return 0
        if requested <= 0:
            return available
        return min(available, requested)
