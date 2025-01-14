var rootURL="http://localhost:8080/"
export async function initFilteredSearch(){
    let localidad = document.getElementById("localidad").value
    let cp = document.getElementById("codigo-postal").value
    let provincia = document.getElementById("provincia").value
    let tipo = document.getElementById("tipo").value
    await filteredSearch(localidad, cp, provincia, tipo)
}


export async function buildTable(jsonList){
    const table = document.getElementById("resultTable").querySelector("tbody");

    table.innerHTML = ""

    jsonList.forEach(item => {
      const row = document.createElement("tr");

      const nameShell = document.createElement("td");
      nameShell.textContent = item.name;
      row.appendChild(nameShell);

      const typeShell = document.createElement("td");
      typeShell.textContent = item.type;
      row.appendChild(typeShell);

      const ageShell = document.createElement("td");
      ageShell.textContent = item.addres;
      row.appendChild(ageShell);

      const cityShell = document.createElement("td");
      cityShell.textContent = item.locality;
      row.appendChild(cityShell);

      const postalCodeShell = document.createElement("td");
      postalCodeShell.textContent = item.postalCode;
      row.appendChild(postalCodeShell);

      const provinceShell = document.createElement("td");
      provinceShell.textContent = item.provincie;
      row.appendChild(provinceShell);

      const descriptionShell = document.createElement("td");
      descriptionShell.textContent = item.description;
      row.appendChild(descriptionShell);

      table.appendChild(row);
    });
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

const popupContainer = document.createElement('div');
popupContainer.className = 'ol-popup';

const popupCloser = document.createElement('a');
popupCloser.className = 'ol-popup-closer';
popupCloser.href = '#';
popupCloser.innerHTML = '×';
popupContainer.appendChild(popupCloser);

const popupContent = document.createElement('div');
popupContainer.appendChild(popupContent);

const overlay = new ol.Overlay({
    element: popupContainer,
    autoPan: true,
    autoPanAnimation: {
        duration: 250,
    },
});

popupCloser.onclick = function () {
    overlay.setPosition(undefined);
    return false;
};

map.addOverlay(overlay);

map.on('singleclick', function (event) {
    map.forEachFeatureAtPixel(event.pixel, function (feature) {
        const name = feature.get('name');
        const description = feature.get('description');
        const coordinate = feature.getGeometry().getCoordinates();

        // Actualizar el contenido del popup
        popupContent.innerHTML = `<strong>${name}</strong><br>${description}`;
        overlay.setPosition(coordinate);
    });
});

export async function buildMap(coordList,monumentList){
    const vectorSource = new ol.source.Vector();
    let count = 0

    map.getLayers().forEach((layer) => {
        if (layer instanceof ol.layer.Vector) {
            map.removeLayer(layer);
        }
    });

    coordList.forEach(element => {

        const marker = new ol.Feature({
            geometry: new ol.geom.Point(ol.proj.fromLonLat(element)),
            name:monumentList[count].name,
            description:monumentList[count].description,
        });
        const markerStyle = new ol.style.Style({
            image: new ol.style.Icon({
                src: 'https://openlayers.org/en/v4.6.5/examples/data/icon.png', // Usar una imagen de marcador
                scale: 0.8 // Tamaño del icono
            })
        });
        marker.setStyle(markerStyle);
        vectorSource.addFeature(marker);
        count++
    });
    const vectorLayer = new ol.layer.Vector({
        source: vectorSource
    });
    map.addLayer(vectorLayer);

}   

async function filteredSearch(localidad,cp,provincia,tipo){
    let url = rootURL+"main/get-monumentos/"
    if(!localidad || localidad == null){localidad=''}
    if(!cp || cp == null){cp=''}
    if(!provincia || provincia == null){provincia=''}
    if(!tipo || tipo == null){tipo=''}

    const params = {
        localidad: localidad,
        codigo_postal: cp,
        provincia: provincia,
        tipo: tipo
    };

    const queryString = new URLSearchParams(params).toString();
    const completedUrl = `${url}?${queryString}`;
    console.log("Petición a:"+ completedUrl)
    
    fetch(completedUrl)
        .then(response => {
            if(!response.ok){
                
            }
            return response.json()
        })
        .then(data=>{
            console.log(data)
            let coordList = []
            let monumentList = []
            data.forEach(element =>{
                coordList.push(element.coordinates)
                monumentList.push(element.table)
            })
            buildMap(coordList,monumentList)
            buildTable(monumentList)
        })
}

document.addEventListener('DOMContentLoaded', () =>{
    let url = rootURL + "main/get-monumentos"
    console.log("perticion debería enviarse")
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error('Error en la solicitud: ' + response.status);
            }
            return response.json();
        })
        .then(data =>{
            console.log(data)
            let coordList = []
            let monumentList = []
            data.forEach(element =>{
                coordList.push(element.coordinates)
                monumentList.push(element.table)
            })
            buildMap(coordList,monumentList)
            buildTable(monumentList)
        })
})







