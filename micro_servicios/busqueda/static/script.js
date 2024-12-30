
export async function initFilteredSearch(){
    let localidad = document.getElementById("localidad").value
    let cp = document.getElementById("codigo-postal").value
    let provincia = document.getElementById("provincia").value
    let tipo = document.getElementById("tipo").value
    var list = [[-0.8656800,38.6373000],[-0.4814900,38.3451700]]
    buildMap(list)
    buildTable()
}

export function buildTable(){
    console.log("se habría contruido la tabla")
}

export function cancel(){
    document.getElementById("localidad").value = ""
    document.getElementById("codigo-postal").value = ""
    document.getElementById("provincia").value = ""
    document.getElementById("tipo").value = ""
}

const map = new ol.Map({
    target: 'map',
    layers: [
        // Capa base de mapa (OpenStreetMap)
        new ol.layer.Tile({
            source: new ol.source.OSM()
        })
    ],
    view: new ol.View({
        center: ol.proj.fromLonLat([-3.7038, 40.4168]), // Coordenadas de Madrid
        zoom: 6 // Nivel de zoom
    })
});


export function buildMap(coordList){
    const vectorSource = new ol.source.Vector();

    coordList.forEach(element => {

        const marker = new ol.Feature({
            geometry: new ol.geom.Point(ol.proj.fromLonLat(element))
        });
        const markerStyle = new ol.style.Style({
            image: new ol.style.Icon({
                src: 'https://openlayers.org/en/v4.6.5/examples/data/icon.png', // Usar una imagen de marcador
                scale: 0.8 // Tamaño del icono
            })
        });
        marker.setStyle(markerStyle);
        vectorSource.addFeature(marker);
    });
    const vectorLayer = new ol.layer.Vector({
        source: vectorSource
    });
    map.addLayer(vectorLayer);

}   









