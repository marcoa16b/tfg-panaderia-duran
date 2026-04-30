import pytest

from dev.states.dashboard_state import DashboardState


class TestDashboardStateLoad:
    def test_load_dashboard(self, seed_producto):
        state = DashboardState()
        state.load_dashboard()
        assert state.is_loading is False
        assert state.total_productos >= 1
        assert isinstance(state.alertas_recientes, list)

    def test_load_dashboard_error_handling(self, seed_basic):
        state = DashboardState()
        state.load_dashboard()
        assert state.is_loading is False


class TestDashboardStateAlertas:
    def test_marcar_todas_leidas_sin_alertas(self, seed_basic):
        state = DashboardState()
        state.load_dashboard()
        count = state.marcar_todas_leidas()
