const todas = document.getElementById('todas')
const castillaLeon = document.getElementById('castilla_leon')
const comunidadValenciana = document.getElementById('comunidad_valenciana')
const euskadi = document.getElementById('euskadi')
const btnEnviar = document.getElementById('enviar')


function activarTodas(){
    if(castillaLeon.checked && comunidadValenciana.checked && euskadi.checked){
        todas.checked = true
    }
    else{
        todas.checked = false;
    }
}

castillaLeon.addEventListener('change', activarTodas);
comunidadValenciana.addEventListener('change', activarTodas);
euskadi.addEventListener('change', activarTodas);


btnEnviar.addEventListener('click', function(){
    alert("se enviar la petición al backend")
})