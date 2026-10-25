from django.urls import path
from .views import (
    EligibleMatchesView,
    RunOptimizationView,
    RecommendationBatchListView,
    RecommendationBatchDetailView,
    ApproveBatchView,
    RejectBatchView,
    ApplyBatchView,
    RecoveryPreviewView,
    RecoveryApplyView,
    DisasterAnalysisView,
    DataIntelligenceAnalyticsView,
    VerifiedImpactAnalyticsView,
    EvaluationsListView,
    OfferListView,
    OfferResponseView,
)

urlpatterns = [
    # Matching & Screening
    path('matches/', EligibleMatchesView.as_view(), name='intelligence-matches'),

    # Optimization Execution
    path('optimize/', RunOptimizationView.as_view(), name='intelligence-optimize'),

    # Recommendations & Approval Workflow
    path('recommendations/', RecommendationBatchListView.as_view(), name='intelligence-recommendations-list'),
    path('recommendations/<str:pk>/', RecommendationBatchDetailView.as_view(), name='intelligence-recommendations-detail'),
    path('recommendations/<str:pk>/approve/', ApproveBatchView.as_view(), name='intelligence-recommendations-approve'),
    path('recommendations/<str:pk>/reject/', RejectBatchView.as_view(), name='intelligence-recommendations-reject'),
    path('recommendations/<str:pk>/apply/', ApplyBatchView.as_view(), name='intelligence-recommendations-apply'),
    path('offers/', OfferListView.as_view(), name='intelligence-offers'),
    path('offers/<str:pk>/respond/', OfferResponseView.as_view(), name='intelligence-offer-respond'),

    # Disruption Recovery
    path('recovery/preview/', RecoveryPreviewView.as_view(), name='intelligence-recovery-preview'),
    path('recovery/<str:pk>/apply/', RecoveryApplyView.as_view(), name='intelligence-recovery-apply'),

    # Disaster Emergency Prioritization
    path('disaster-analysis/', DisasterAnalysisView.as_view(), name='intelligence-disaster-analysis'),

    # Pandas/NumPy Descriptive Analytics & Part 6 Impact Dashboard
    path('analytics/', DataIntelligenceAnalyticsView.as_view(), name='intelligence-analytics'),
    path('impact/', VerifiedImpactAnalyticsView.as_view(), name='intelligence-impact'),

    # Reproducible Evaluation Benchmarks
    path('evaluations/', EvaluationsListView.as_view(), name='intelligence-evaluations'),
]

