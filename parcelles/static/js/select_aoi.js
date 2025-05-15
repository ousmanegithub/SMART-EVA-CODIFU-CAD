$(function () {
    // Initialisation de la carte
    var map = L.map('map_aoi', {
        zoomControl: true,
        center: [42.35, -71.08],
        zoom: 3,
    });
    map.zoomControl.setPosition('topright');
    osm.addTo(map);

    // Groupe de calques éditables
    var drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);

    // Contrôle de dessin
    var drawControlFull = new L.Control.Draw({
        position: 'topright',
        draw: {
            polygon: {
                allowIntersection: false, // Restreindre les intersections
                drawError: {
                    color: '#e1e100', // Couleur de l'erreur
                    message: '<strong>Oh snap!<strong> Impossible de dessiner cela !' // Message d'erreur
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

    // Exporter le GeoJSON
    map.on("draw:created", function (e) {
        document.getElementById("export").style.display = "initial";
        var temp = drawnItems.addLayer(e.layer);
        document.getElementById('export').onclick = function (e) {
            var data = drawnItems.toGeoJSON();
            var convertedData = 'text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(data));
            document.getElementById('export').setAttribute('href', 'data:' + convertedData);
            document.getElementById('export').setAttribute('download', 'drawn_aoi.geojson');
        };
    });








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

                    console.log("Calque ajouté :", importedLayer); // Débogage

                    // Zoomer sur les données importées
                    map.fitBounds(importedLayer.getBounds());
                } catch (error) {
                    alert("Erreur : fichier GeoJSON invalide.");
                    console.error("Erreur de traitement du fichier GeoJSON :", error);
                }
            };
            reader.readAsText(file);
        }
    });

    // Débogage : Vérifiez les calques dans drawnItems
    drawnItems.eachLayer(function (layer) {
        console.log("Calque existant dans drawnItems :", layer);
    });


    $("#generate-bdn").on("click", function () {
        const processingMessage = $("#processing-message");

        processingMessage.text("Traitement en cours... Veuillez patienter.").show();

        fetch("{% url 'generate_bdn_codes' %}", {
            method: "POST",
            headers: {
                "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
            },
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.geojson_url) {
                    $("#download-file").attr("href", data.geojson_url).show();
                    processingMessage.text("Traitement terminé avec succès !").css("color", "green");
                } else {
                    processingMessage.text("Erreur lors du traitement.").css("color", "red");
                    alert(data.error || "Erreur inconnue.");
                }
            })
            .catch((error) => {
                processingMessage.text("Erreur lors du traitement.").css("color", "red");
                console.error("Erreur :", error);
            });
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

    // Affiche une alerte de traitement
    Swal.fire({
        title: 'Génération en cours...',
        html: 'Veuillez patienter pendant que les codes BDN sont générés.',
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });

    // Envoyer la requête pour générer les codes BDN
    fetch($(this).attr("action"), {
        method: "POST",
        headers: {
            "X-CSRFToken": $("input[name=csrfmiddlewaretoken]").val()
        }
    })
        .then(response => response.json())
        .then(data => {
            Swal.close(); // Fermer l'alerte de traitement

            // Vérifier la réponse du serveur
            if (data.alert && data.alert.type === 'success') {
                Swal.fire({
                    icon: 'success',
                    title: 'Succès',
                    text: data.alert.message,
                    confirmButtonText: 'OK'
                }).then(() => {
                    // Afficher les boutons Export
                    if (data.geojson_url) {
                        window.generatedFileUrl = data.geojson_url; // Sauvegarder l'URL pour le téléchargement
                        $("#export").show(); // Afficher le bouton pour le fichier GeoJSON
                    }

                    if (data.zip_url) {
                        window.qrCodesFileUrl = data.zip_url; // Sauvegarder l'URL du fichier ZIP des QR codes
                        $("#download-qr-zip").show(); // Afficher le bouton pour les QR codes
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

// Gestion du clic sur le bouton Export pour le fichier GeoJSON
$("#export").on("click", function () {
    if (window.generatedFileUrl) {
        const link = document.createElement('a');
        link.href = window.generatedFileUrl;
        link.download = "generated_bdn.geojson"; // Nom du fichier
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

// Gestion du clic sur le bouton Export pour les QR codes
$("#download-qr-zip").on("click", function () {
    if (window.qrCodesFileUrl) {
        const link = document.createElement('a');
        link.href = window.qrCodesFileUrl;
        link.download = "qr_codes.zip"; // Nom du fichier ZIP
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






