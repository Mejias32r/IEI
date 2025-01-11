var rootURL="http://localhost:8082/"

export async function initFilteredSearch(){
    let localidad = document.getElementById("localidad").value
    let cp = document.getElementById("codigo-postal").value
    let provincia = document.getElementById("provincia").value
    let tipo = document.getElementById("tipo").value
    let json = await filteredSearch(localidad, cp, provincia, tipo)
    let coordList = []
    let monumentList = []
    json.forEach(element =>{
        coordList.push(element.coordinates)
        monumentList.push(element.table)
    })
    buildMap(coordList)
    buildTable(monumentList)
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


export async function buildMap(coordList){
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

async function filteredSearch(localidad,cp,provincia,tipo){
    let url = rootURL+"filteredSearch/"
    const params = {
        localty: localidad,
        postalCode: cp,
        province: provincia,
        type: tipo
    };

    const queryString = new URLSearchParams(params).toString();
    const completedUrl = `${url}?${queryString}`;
    /*
    fetch(completedUrl)
        .then(response => {
            if(!response.ok){
                throw new Error('Error en la solicitud');
            }
            console.log(response.json())
            let json = response.json()
        })
    */
    let arrayJson =
    [{
        table : {
            name :"Puente Romano" ,
            type:"Puente",
            address:"Calle Antigua",
            localty:"Sevilla",
            postalCode:"41001",
            province:"Sevilla",
            description: "Puente histórico de la época romana 2222222."
        },
        coordinates: [-0.8656800,38.6373000]
    },{
        table : {
            name :"Puente Romano" ,
            type:"Puente",
            address:"Calle Antigua",
            localty:"Sevilla",
            postalCode:"41001",
            province:"Sevilla",
            description: "Puente histórico de la época romana 2222222."
        },
        coordinates: [-0.4814900,38.3451700]
    }]
    
    return arrayJson
}

document.addEventListener('DOMContentLoaded', () =>{
    let url = rootURL + "busquedaTodo/"
    console.log("perticion debería enviarse")
    fetch(url)
        .then(response => {
            console.log("recibida respuesta")
            if(!response.ok){
                throw new Error('Error en la solicitud');
            }
            let json = response.json()
            return json
        })
        .then(json =>{
            console.log(json)
            let coordList = []
            let monumentList = []
            json.forEach(element =>{
                coordList.push(element.coordinates)
                monumentList.push(element.table)
            })
            buildMap(coordList)
            buildTable(monumentList)
        })
})







