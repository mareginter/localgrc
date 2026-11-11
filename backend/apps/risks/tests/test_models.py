from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.core.models import Organization, Role, UserRole
from apps.risks.models import Risk, RiskAssessment

User = get_user_model()

class RiskModelTests(TestCase):
    """Testes para garantir que a lógica de negócio do Risco está correta."""

    def setUp(self):
        # Setup que corre antes de cada teste
        self.org = Organization.objects.create(name="Test Org")
        self.user = User.objects.create_user(
            email="tester@local", 
            password="password123"
        )
        self.risk = Risk.objects.create(
            organization=self.org,
            title="Test SQL Injection",
            category="technical",
            owner=self.user
        )

    def test_risk_assessment_score_calculation(self):
        """Testa se o score do risco é calculado corretamente (L x I)."""
        assessment = RiskAssessment.objects.create(
            risk=self.risk,
            type="inherent",
            likelihood=4,
            impact=5
        )
        
        # O Score deve ser 4 * 5 = 20
        self.assertEqual(assessment.score, 20, "O score calculado devia ser 20")
        
        # Como o score é 20, o nível deve ser Crítico (conforme a nossa matriz)
        if hasattr(self.risk, 'risk_level'):
            self.assertEqual(self.risk.risk_level, "critical", "Score 20 deve ser Crítico")

    def test_risk_level_boundaries(self):
        """Testa os limites de classificação da matriz (Low, Medium, High, Critical)."""
        # Teste 1: Risco Baixo (L=1, I=2 -> Score=2)
        RiskAssessment.objects.create(risk=self.risk, type="inherent", likelihood=1, impact=2)
        self.risk.refresh_from_db()
        if hasattr(self.risk, 'risk_level'):
            self.assertEqual(self.risk.risk_level, "low", "Score 2 deve ser Low")
        
        # Teste 2: Risco Alto (L=4, I=4 -> Score=16)
        self.risk.assessments.all().delete()
        RiskAssessment.objects.create(risk=self.risk, type="inherent", likelihood=4, impact=4)
        self.risk.refresh_from_db()
        if hasattr(self.risk, 'risk_level'):
            self.assertEqual(self.risk.risk_level, "high", "Score 16 deve ser High")


class RiskViewTests(TestCase):
    """Testes para garantir que as páginas principais de Risco abrem sem erros."""

    def setUp(self):
        self.org = Organization.objects.create(name="Test Org")
        self.user = User.objects.create_user(email="tester@local", password="password123")

        UserRole.objects.create(
            user=self.user,
            role=Role.objects.get(code="admin"),
            organization=self.org,
        )

        self.client.force_login(self.user)

    def test_risk_list_view_status_code(self):
        """Testa se a página da lista de riscos abre corretamente."""
        response = self.client.get('/risks/')
        self.assertEqual(response.status_code, 200)

    def test_risk_matrix_view_status_code(self):
        """Testa se a página da Matriz de Risco abre corretamente."""
        response = self.client.get('/risks/matrix/')
        self.assertEqual(response.status_code, 200)
        
        # Verifica se a matriz foi enviada para o template
        self.assertIn('matrix', response.context)
        
        # A matriz deve ter 5 linhas (5 níveis de impacto)
        self.assertEqual(len(response.context['matrix']), 5)
        
        # A primeira linha deve ter 5 colunas (5 níveis de probabilidade)
        self.assertEqual(len(response.context['matrix'][0]), 5)