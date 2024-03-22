from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    # ex: /animal/5/
    path("<int:animal_id>/", views.animal_detail, name="animal-detail"),
    # ex: /adoption_notice/7/
    path("vermittlung/<int:adoption_notice_id>/", views.adoption_notice_detail, name="adoption-notice-detail"),

    # ex: /search/
    path("suchen/", views.search, name="search"),
    # ex: /vermitteln/
    path("vermitteln/", views.add_adoption, name="add-adoption"),

    # ex: vermitteln-tiere-hinzufügen/5
    path("vermitteln-tiere-hinzufügen/<int:adoption_notice_id>",
         views.add_animal_to_adoption,
         name="add-animal-to-adoption"),

    path("ueber-uns/", views.about, name="about"),

    #############
    ## Reports ##
    #############
    path("melden/<int:adoption_notice_id>/", views.report_adoption, name="report-adoption-notices"),
    path("meldung/<uuid:report_id>/", views.report_detail, name="report-detail"),
    path("meldung/<uuid:report_id>/sucess", views.report_detail_success, name="report-detail-success"),
]
