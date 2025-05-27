$(function () {

    var map = L.map('map_aoi', {
        zoomControl: true,
        center: [42.35, -71.08],
        zoom: 3,
    });
    map.zoomControl.setPosition('topright');
    osm.addTo(map);


    var drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);


    var drawControlFull = new L.Control.Draw({
        position: 'topright',
        draw: {
            polygon: {
                allowIntersection: false,
                drawError: {
                    color: '#e1e100',
                    message: '<strong>Oh snap!<strong> Impossible de dessiner cela !'
                },
                shapeOptions: {
                    color: '#97009c'
                }
            },
            polyline: false,
            circle: false,
            rectangle: false,
            marker: false,
            circlemarker: false,
        },
        edit: {
            featureGroup: drawnItems,
            remove: true,
        }
    });
    map.addControl(drawControlFull);


    // Importer un GeoJSON
    $('#geojson-upload').on('change', function (event) {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function (e) {
                try {
                    const geojsonData = JSON.parse(e.target.result);

                    // Vérifiez si le GeoJSON contient des fonctionnalités
                    if (!geojsonData.features || geojsonData.features.length === 0) {
                        alert("Le fichier GeoJSON ne contient aucune donnée à afficher.");
                        return;
                    }

                    console.log("GeoJSON chargé :", geojsonData); // Débogage

                    // Ajouter le GeoJSON au groupe de calques
                    const importedLayer = L.geoJSON(geojsonData, {
                        style: {
                            color: "#3388ff",
                            weight: 2,
                            opacity: 0.8,
                        }
                    }).addTo(drawnItems);

                    console.log("Calque ajouté :", importedLayer);


                    map.fitBounds(importedLayer.getBounds());
                } catch (error) {
                    alert("Erreur : fichier GeoJSON invalide.");
                    console.error("Erreur de traitement du fichier GeoJSON :", error);
                }
            };
            reader.readAsText(file);
        }
    });


    drawnItems.eachLayer(function (layer) {
        console.log("Calque existant dans drawnItems :", layer);
    });









});





fetch('/parcelles/')
    .then(response => response.json())
    .then(data => {
        const geojson = JSON.parse(data.geojson);
        L.geoJSON(geojson, {
            style: { color: "#3388ff", weight: 2, opacity: 0.8 }
        }).addTo(map);
    })
    .catch(error => console.error('Erreur lors du chargement des parcelles :', error));


$("#generate-bdn-form").on("submit", function (e) {
    e.preventDefault();


    Swal.fire({
        title: 'Génération en cours...',
        html: 'Veuillez patienter pendant que les codes BDN sont générés.',
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });


    fetch($(this).attr("action"), {
        method: "POST",
        headers: {
            "X-CSRFToken": $("input[name=csrfmiddlewaretoken]").val()
        }
    })
        .then(response => response.json())
        .then(data => {
            Swal.close();


            if (data.alert && data.alert.type === 'success') {
                Swal.fire({
                    icon: 'success',
                    title: 'Succès',
                    text: data.alert.message,
                    confirmButtonText: 'OK'
                }).then(() => {

                    if (data.geojson_url) {
                        window.generatedFileUrl = data.geojson_url;
                        $("#export").show();
                    }

                    if (data.zip_url) {
                        window.qrCodesFileUrl = data.zip_url;
                        $("#download-qr-zip").show();
                    }
                });
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'Erreur',
                    text: data.alert ? data.alert.message : 'Réponse inattendue du serveur.'
                });
            }
        })
        .catch(error => {
            Swal.close();
            Swal.fire({
                icon: 'error',
                title: 'Erreur',
                text: 'Une erreur est survenue lors de la génération des codes BDN.'
            });
            console.error("Erreur lors de la génération :", error);
        });
});


$("#export").on("click", function () {
    if (window.generatedFileUrl) {
        const link = document.createElement('a');
        link.href = window.generatedFileUrl;
        link.download = "generated_bdn.geojson";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        Swal.fire({
            icon: 'success',
            title: 'Fichier téléchargé',
            text: 'Le fichier GEOJSON a été téléchargé avec succès !',
            confirmButtonText: 'OK'
        });
    } else {
        Swal.fire({
            icon: 'error',
            title: 'Erreur',
            text: 'Aucun fichier généré à télécharger.'
        });
    }
});


$("#download-qr-zip").on("click", function () {
    if (window.qrCodesFileUrl) {
        const link = document.createElement('a');
        link.href = window.qrCodesFileUrl;
        link.download = "qr_codes.zip";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        Swal.fire({
            icon: 'success',
            title: 'QR Codes téléchargés',
            text: 'Le fichier ZIP des QR codes a été téléchargé avec succès !',
            confirmButtonText: 'OK'
        });
    } else {
        Swal.fire({
            icon: 'error',
            title: 'Erreur',
            text: 'Aucun fichier ZIP généré à télécharger.'
        });
    }
});





